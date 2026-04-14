"""
Seed products from real Amazon dataset (CSV).
Usage: python manage.py seed_products [--sync-neo4j] [--csv data/amazon-products.csv]

Data source: https://github.com/luminati-io/Amazon-dataset-samples
"""
import csv, json, sys, os, re
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from ai_service.models.django_models import Category, Product

csv.field_size_limit(sys.maxsize)

DEFAULT_CSV = os.path.join("data", "amazon-products.csv")


def _parse_price(raw: str) -> Decimal:
    raw = raw.strip().strip('"')
    try:
        return Decimal(str(float(raw))).quantize(Decimal("0.01"))
    except (ValueError, InvalidOperation):
        return Decimal("0.00")


def _parse_category(raw: str) -> str:
    try:
        cats = json.loads(raw.replace("'", '"'))
        return cats[0] if cats else "Other"
    except (json.JSONDecodeError, IndexError):
        return "Other"


def _parse_float(raw: str, default=0.0) -> float:
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default


def _parse_int(raw: str, default=0) -> int:
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return default


class Command(BaseCommand):
    help = "Seed products from Amazon CSV dataset"

    def add_arguments(self, parser):
        parser.add_argument("--sync-neo4j", action="store_true")
        parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to CSV file")

    def handle(self, *args, **options):
        csv_path = options["csv"]
        if not os.path.exists(csv_path):
            self.stderr.write(f"CSV not found: {csv_path}")
            return

        created = 0
        skipped = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get("title", "").strip()
                if not title:
                    skipped += 1
                    continue

                price = _parse_price(row.get("final_price", "0"))
                cat_name = _parse_category(row.get("categories", "[]"))
                cat, _ = Category.objects.get_or_create(name=cat_name)

                _, is_new = Product.objects.get_or_create(
                    name=title[:500],
                    defaults={
                        "description": row.get("description", "")[:5000],
                        "price": price,
                        "brand": row.get("brand", "")[:200],
                        "image_url": row.get("image_url", "")[:1000],
                        "rating": _parse_float(row.get("rating", "0")),
                        "rating_count": _parse_int(row.get("reviews_count", "0")),
                        "category": cat,
                    },
                )
                if is_new:
                    created += 1
                else:
                    skipped += 1

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} new products (skipped {skipped}, total {total})"
        ))

        if options["sync_neo4j"]:
            self._sync_neo4j()

    def _sync_neo4j(self):
        from ai_service.services.graph import graph_service
        graph_service.create_indexes()
        products = Product.objects.select_related("category").all()
        for p in products:
            graph_service.sync_product(
                pid=p.id, name=p.name, description=p.description,
                price=p.price,
                category_id=p.category_id,
                category_name=p.category.name if p.category else None,
            )
        self.stdout.write(self.style.SUCCESS(f"Synced {products.count()} products to Neo4j"))
