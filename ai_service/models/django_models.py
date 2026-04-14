from django.db import models


class Interaction(models.Model):
    class EventType(models.TextChoices):
        VIEW = "view"
        CLICK = "click"
        CART = "cart"
        PURCHASE = "purchase"
        SEARCH = "search"

    user_id = models.IntegerField(db_index=True)
    product_id = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    query = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interactions"
        indexes = [models.Index(fields=["user_id", "event_type"])]
