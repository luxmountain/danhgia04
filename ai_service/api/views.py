from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from ai_service.models.django_models import Product, Interaction
from ai_service.api.serializers import (
    ProductSerializer, ProductDetailSerializer,
    TrackEventSerializer, ChatSerializer,
)
from ai_service.services.graph import graph_service
from ai_service.services.embedding import embedding_service
from ai_service.services.vector_store import product_store
from ai_service.services import llm


# ── Product endpoints ──────────────────────────────────

@api_view(["GET"])
def product_list(request):
    """List products with optional category/brand filter and pagination."""
    qs = Product.objects.select_related("category").all()
    category = request.query_params.get("category")
    brand = request.query_params.get("brand")
    if category:
        qs = qs.filter(category__name__iexact=category)
    if brand:
        qs = qs.filter(brand__iexact=brand)
    qs = qs.order_by("-rating", "-rating_count")

    page = int(request.query_params.get("page", 1))
    size = int(request.query_params.get("size", 20))
    start = (page - 1) * size
    total = qs.count()

    return Response({
        "total": total, "page": page, "size": size,
        "results": ProductSerializer(qs[start:start + size], many=True).data,
    })


@api_view(["GET"])
def product_detail(request, product_id):
    """Get single product detail."""
    try:
        p = Product.objects.select_related("category").get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)
    return Response(ProductDetailSerializer(p).data)


@api_view(["GET"])
def product_search(request):
    """Search products by keyword (name, description, brand)."""
    q = request.query_params.get("q", "").strip()
    if not q:
        return Response({"error": "Query parameter 'q' is required"}, status=400)

    limit = int(request.query_params.get("limit", 20))
    results = Product.objects.select_related("category").filter(
        Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q)
    ).order_by("-rating")[:limit]

    return Response({
        "query": q, "count": len(results),
        "results": ProductSerializer(results, many=True).data,
    })


# ── AI endpoints ───────────────────────────────────────

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
    """Find similar products via FAISS vector search (self-trained embeddings)."""
    k = int(request.query_params.get("k", 5))
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    query_vec = embedding_service.embed_text(f"{product.name} {product.description}")
    results = product_store.search(query_vec, k=k + 1)
    results = [r for r in results if r["id"] != product_id][:k]

    pids = [r["id"] for r in results]
    products_map = {p.id: p for p in Product.objects.filter(id__in=pids)}
    return Response([
        {**ProductSerializer(products_map[r["id"]]).data, "score": r["score"]}
        for r in results if r["id"] in products_map
    ])


@api_view(["POST"])
def chat(request):
    """GraphRAG chat: graph context + vector search → self-built response generator."""
    ser = ChatSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    # 1. Graph context (user history from Neo4j)
    graph_ctx = graph_service.get_user_context(d["user_id"], limit=5)

    # 2. Vector context (FAISS similarity on self-trained embeddings)
    q_vec = embedding_service.embed_text(d["query"])
    vec_results = product_store.search(q_vec, k=5)
    pids = [r["id"] for r in vec_results]
    products_map = {p.id: p for p in Product.objects.filter(id__in=pids)}

    # 3. Generate response (no external API)
    answer = llm.chat(d["query"], graph_ctx, vec_results, products_map)

    return Response({
        "answer": answer,
        "sources": {"graph_context": graph_ctx, "vector_results": vec_results},
    })
