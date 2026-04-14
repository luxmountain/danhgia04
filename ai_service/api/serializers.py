from rest_framework import serializers
from ai_service.models.django_models import Product, Interaction


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


class TrackEventSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False)
    event_type = serializers.ChoiceField(choices=Interaction.EventType.choices)
    query = serializers.CharField(required=False, default="")


class ChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    query = serializers.CharField()
    session_id = serializers.CharField(required=False, default="")
