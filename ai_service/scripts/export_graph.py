"""Export Neo4j graph data to JSON for GNN training."""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
load_dotenv()

from ai_service.services.graph import graph_service

DATA_DIR = os.getenv("DATA_DIR", "data")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Exporting edges...")
    edges = graph_service.export_edges()
    with open(os.path.join(DATA_DIR, "edges.json"), "w") as f:
        json.dump(edges, f)
    print(f"  {len(edges)} edges exported")

    print("Exporting product categories...")
    cats = graph_service.export_product_categories()
    with open(os.path.join(DATA_DIR, "product_categories.json"), "w") as f:
        json.dump(cats, f)
    print(f"  {len(cats)} product-category links exported")

    print("Done.")


if __name__ == "__main__":
    main()
