"""
Simulate user interactions for training data collection.
Fetches products from product-service, writes interactions to ai-service DB + Neo4j.
Usage: python ai_service/scripts/simulate_interactions.py [--users 50] [--actions 500]
"""
import os, sys, random, argparse
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

from ai_service.models.django_models import Interaction
from ai_service.services.graph import graph_service

FUNNEL = {"view": 1.0, "click": 0.5, "cart": 0.2, "purchase": 0.08}
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001/api")


def _fetch_all_products():
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
    return products


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--actions", type=int, default=500)
    args = parser.parse_args()

    products = _fetch_all_products()
    if not products:
        print("No products. Seed product-service first.")
        return

    by_cat = {}
    for p in products:
        cat = p.get("category_name") or "Other"
        by_cat.setdefault(cat, []).append(p)
    categories = list(by_cat.keys())

    # Persistent user preferences
    user_prefs = {}
    for uid in range(1, args.users + 1):
        n = min(random.randint(2, 3), len(categories))
        user_prefs[uid] = random.sample(categories, n)

    created = 0
    batch = []
    for _ in range(args.actions):
        uid = random.randint(1, args.users)
        cat = random.choice(user_prefs[uid])
        pool = by_cat[cat]
        weights = [max(p.get("rating", 1), 1.0) for p in pool]
        product = random.choices(pool, weights=weights, k=1)[0]

        for event_type, prob in FUNNEL.items():
            if random.random() > prob:
                break
            batch.append(Interaction(
                user_id=uid, product_id=product["id"], event_type=event_type,
            ))
            graph_service.log_interaction(uid, product["id"], event_type)
            created += 1

    Interaction.objects.bulk_create(batch, batch_size=500)
    print(f"Created {created} interactions for {args.users} users across {len(products)} products")


if __name__ == "__main__":
    main()
