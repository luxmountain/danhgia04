from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"

    def __str__(self):
        return self.name


class Interaction(models.Model):
    class EventType(models.TextChoices):
        VIEW = "view"
        CLICK = "click"
        CART = "cart"
        PURCHASE = "purchase"
        SEARCH = "search"

    user_id = models.IntegerField(db_index=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    query = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interactions"
        indexes = [models.Index(fields=["user_id", "event_type"])]
