from rest_framework import serializers
from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "brand", "image_url", "rating", "rating_count", "category_name"]


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "brand", "image_url",
                  "rating", "rating_count", "category_name", "created_at"]
