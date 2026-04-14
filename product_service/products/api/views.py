from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

from products.models import Product
from products.api.serializers import ProductSerializer, ProductDetailSerializer


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
