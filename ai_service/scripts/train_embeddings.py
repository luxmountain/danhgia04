"""
Train text embedding model (TF-IDF + Autoencoder) on product data.
Fetches products from product-service via HTTP.
Usage: python ai_service/scripts/train_embeddings.py
"""
import os, sys, re, pickle
import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
load_dotenv()

from ai_service.services.embedding import TextAutoencoder

MODEL_DIR = os.getenv("MODEL_DIR", "data/models")
EMBED_DIM = int(os.getenv("EMBEDDING_DIM", "128"))
EPOCHS = 100
LR = 1e-3
PRODUCT_SERVICE_URL = os.getenv(
    "AI_PRODUCT_SERVICE_URL",
    os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001/api"),
)


def _clean(text):
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def _fetch_all_products():
    import requests
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
    if len(products) < 2:
        print("Need at least 2 products. Seed product-service first.")
        return

    corpus = [_clean(f"{p['name']} {p.get('category_name', '')} {p.get('brand', '')}") for p in products]
    print(f"Training on {len(corpus)} product texts...")

    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
    sparse_matrix = tfidf.fit_transform(corpus)
    tfidf_dim = sparse_matrix.shape[1]
    print(f"TF-IDF vocabulary: {tfidf_dim} features")

    X = torch.tensor(sparse_matrix.toarray(), dtype=torch.float32)
    model = TextAutoencoder(tfidf_dim, EMBED_DIM)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    for epoch in range(1, EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        reconstructed, _ = model(X)
        loss = loss_fn(reconstructed, X)
        loss.backward()
        optimizer.step()
        if epoch % 20 == 0:
            print(f"Epoch {epoch}/{EPOCHS}  loss={loss.item():.6f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "tfidf.pkl"), "wb") as f:
        pickle.dump(tfidf, f)
    torch.save(
        {"model": model.state_dict(), "input_dim": tfidf_dim},
        os.path.join(MODEL_DIR, "autoencoder.pt"),
    )
    print(f"Saved TF-IDF + Autoencoder to {MODEL_DIR}/")

    model.eval()
    with torch.no_grad():
        _, embeddings = model(X)
    print(f"Embedding shape: {embeddings.shape}")


if __name__ == "__main__":
    main()
