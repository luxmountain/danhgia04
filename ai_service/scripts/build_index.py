"""Build FAISS index from self-trained embeddings (text + GNN)."""
import os, sys, json
import numpy as np
import faiss
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
load_dotenv()

from ai_service.services.embedding import embedding_service
from ai_service.services.vector_store import product_store
from ai_service.services.graph import graph_service

DATA_DIR = os.getenv("DATA_DIR", "data")
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
    products = _fetch_all_products()
    if not products:
        print("No products from product-service.")
        return

    if not embedding_service.is_trained():
        print("WARNING: Embedding model not trained. Run train_embeddings.py first.")
        print("Using hash-based fallback.")

    texts = [f"{p['name']} {p.get('category_name', '')}" for p in products]
    print(f"Embedding {len(texts)} products...")
    text_vecs = embedding_service.embed_batch(texts)

    # Try to merge with GNN embeddings
    gnn_path = os.path.join(DATA_DIR, "product_embeddings.npy")
    pid_map_path = os.path.join(DATA_DIR, "pid_map.json")

    if os.path.exists(gnn_path) and os.path.exists(pid_map_path):
        gnn_vecs = np.load(gnn_path)
        with open(pid_map_path) as f:
            pid_map = {int(k): v for k, v in json.load(f).items()}
        print("Merging text + GNN embeddings...")
        gnn_dim = gnn_vecs.shape[1]
        merged = np.zeros((len(products), text_vecs.shape[1] + gnn_dim), dtype="float32")
        for i, p in enumerate(products):
            merged[i, :text_vecs.shape[1]] = text_vecs[i]
            if p["id"] in pid_map:
                merged[i, text_vecs.shape[1]:] = gnn_vecs[pid_map[p["id"]]]
        norms = np.linalg.norm(merged, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vecs = merged / norms
        product_store.dim = vecs.shape[1]
        product_store.index = faiss.IndexFlatIP(vecs.shape[1])
    else:
        print("No GNN embeddings found, using text only.")
        vecs = text_vecs

    ids = [p["id"] for p in products]
    product_store.add(ids, vecs)
    product_store.save()
    print(f"Indexed {len(ids)} products (dim={vecs.shape[1]})")

    # Write SIMILAR edges to Neo4j
    print("Writing SIMILAR edges to Neo4j...")
    for i, p in enumerate(products):
        results = product_store.search(vecs[i], k=6)
        sim_ids = [r["id"] for r in results if r["id"] != p["id"]][:5]
        sim_scores = [r["score"] for r in results if r["id"] != p["id"]][:5]
        if sim_ids:
            graph_service.write_similar_edges(p["id"], sim_ids, sim_scores)

    print("Done.")


if __name__ == "__main__":
    main()
