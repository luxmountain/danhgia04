"""HTTP client to call product-service (runs on port 8001)."""
import os
import requests

BASE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001/api")
TIMEOUT = 5


def get_products(category=None, brand=None, page=1, size=20):
    params = {"page": page, "size": size}
    if category:
        params["category"] = category
    if brand:
        params["brand"] = brand
    r = requests.get(f"{BASE_URL}/products/", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_product(product_id: int):
    r = requests.get(f"{BASE_URL}/products/{product_id}/", timeout=TIMEOUT)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def search_products(query: str, limit=20):
    r = requests.get(f"{BASE_URL}/products/search/", params={"q": query, "limit": limit}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_products_by_ids(ids: list[int]) -> dict:
    """Fetch multiple products by ID, return {id: product_dict}."""
    result = {}
    for pid in ids:
        p = get_product(pid)
        if p:
            result[pid] = p
    return result
