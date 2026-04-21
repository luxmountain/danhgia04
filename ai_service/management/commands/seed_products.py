"""
Sync products from product-service into Neo4j graph.
Usage: python manage.py seed_products
"""
import os
import requests
from django.core.management.base import BaseCommand
from ai_service.services.graph import graph_service

PRODUCT_SERVICE_URL = os.getenv(
    "AI_PRODUCT_SERVICE_URL",
    os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001/api"),
)


class Command(BaseCommand):
    help = "Sync products from product-service into Neo4j"

    def handle(self, *args, **options):
        graph_service.create_indexes()

        products = []
        page = 1
        while True:
            r = requests.get(f"{PRODUCT_SERVICE_URL}/products/", params={"page": page, "size": 100})
            r.raise_for_status()
            data = r.json()
            products.extend(data["results"])
            if page * 100 >= data["total"]:
                break
            page += 1

        for p in products:
            graph_service.sync_product(
                pid=p["id"], name=p["name"],
                description=p.get("description", ""),
                price=p.get("price", 0),
                category_id=None,
                category_name=p.get("category_name"),
            )

        self.stdout.write(self.style.SUCCESS(f"Synced {len(products)} products to Neo4j"))
