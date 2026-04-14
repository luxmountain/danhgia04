from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ai_service.models.django_models import Interaction
from ai_service.api.serializers import TrackEventSerializer, ChatSerializer
from ai_service.services.graph import graph_service
from ai_service.services.embedding import embedding_service
from ai_service.services.vector_store import product_store
from ai_service.services import product_client, llm


@api_view(["POST"])
def track_event(request):
    """Log user interaction → PostgreSQL + Neo4j."""
    ser = TrackEventSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    Interaction.objects.create(
        user_id=d["user_id"], product_id=d.get("product_id"),
        event_type=d["event_type"], query=d.get("query", ""),
    )
    if d.get("product_id"):
        graph_service.log_interaction(d["user_id"], d["product_id"], d["event_type"])
    if d.get("query"):
        graph_service.log_search(d["user_id"], d["query"])

    return Response({"status": "ok"}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def recommend(request, user_id):
    """Get top-K recommendations (graph-based collaborative filtering)."""
    limit = int(request.query_params.get("limit", 10))
    return Response(graph_service.recommend(user_id, limit=limit))


@api_view(["GET"])
def similar_products(request, product_id):
    """Find similar products via FAISS vector search."""
    k = int(request.query_params.get("k", 5))
    product = product_client.get_product(product_id)
    if not product:
        return Response({"error": "Product not found"}, status=404)

    query_vec = embedding_service.embed_text(f"{product['name']} {product.get('description', '')}")
    results = product_store.search(query_vec, k=k + 1)
    results = [r for r in results if r["id"] != product_id][:k]

    products_map = product_client.get_products_by_ids([r["id"] for r in results])
    return Response([
        {**products_map[r["id"]], "score": r["score"]}
        for r in results if r["id"] in products_map
    ])


@api_view(["POST"])
def chat(request):
    """GraphRAG chat: graph context + vector search → self-built response generator."""
    ser = ChatSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    # 1. Graph context
    graph_ctx = graph_service.get_user_context(d["user_id"], limit=5)

    # 2. Vector context
    q_vec = embedding_service.embed_text(d["query"])
    vec_results = product_store.search(q_vec, k=5)
    products_map = product_client.get_products_by_ids([r["id"] for r in vec_results])

    # 3. Generate response (no external API)
    answer = llm.chat(d["query"], graph_ctx, vec_results, products_map)

    return Response({
        "answer": answer,
        "sources": {"graph_context": graph_ctx, "vector_results": vec_results},
    })
