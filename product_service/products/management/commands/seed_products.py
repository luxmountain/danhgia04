"""
Seed products from Amazon CSV dataset.
Usage: python manage.py seed_products [--csv ../data/amazon-products.csv]
"""
import csv, json, sys, os
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from products.models import Category, Product

csv.field_size_limit(sys.maxsize)
DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "amazon-products.csv")


def _parse_price(raw):
    try:
        return Decimal(str(float(raw.strip().strip('"')))).quantize(Decimal("0.01"))
    except (ValueError, InvalidOperation):
        return Decimal("0.00")


def _parse_category(raw):
    try:
        cats = json.loads(raw.replace("'", '"'))
        return cats[0] if cats else "Other"
    except (json.JSONDecodeError, IndexError):
        return "Other"


class Command(BaseCommand):
    help = "Seed products from Amazon CSV dataset"

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=DEFAULT_CSV)

    def handle(self, *args, **options):
        csv_path = options["csv"]
        if not os.path.exists(csv_path):
            self.stderr.write(f"CSV not found: {csv_path}")
            return

        created = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                title = row.get("title", "").strip()
                if not title:
                    continue
                cat, _ = Category.objects.get_or_create(
                    name=_parse_category(row.get("categories", "[]"))
                )
                _, is_new = Product.objects.get_or_create(
                    name=title[:500],
                    defaults={
                        "description": row.get("description", "")[:5000],
                        "price": _parse_price(row.get("final_price", "0")),
                        "brand": row.get("brand", "")[:200],
                        "image_url": row.get("image_url", "")[:1000],
                        "rating": float(row.get("rating", 0) or 0),
                        "rating_count": int(float(row.get("reviews_count", 0) or 0)),
                        "category": cat,
                    },
                )
                if is_new:
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} products (total {Product.objects.count()})"
        ))
