from rest_framework import serializers
from ai_service.models.django_models import Interaction


class TrackEventSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False)
    event_type = serializers.ChoiceField(choices=Interaction.EventType.choices)
    query = serializers.CharField(required=False, default="")


class ChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    query = serializers.CharField()
    session_id = serializers.CharField(required=False, default="")
