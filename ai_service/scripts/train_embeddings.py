"""
Train text embedding model (TF-IDF + Autoencoder) on product data.
Usage: python ai_service/scripts/train_embeddings.py
"""
import os, sys, re, pickle
import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

from ai_service.models.django_models import Product

MODEL_DIR = os.getenv("MODEL_DIR", "data/models")
EMBED_DIM = int(os.getenv("EMBEDDING_DIM", "128"))
EPOCHS = 100
LR = 1e-3


def _clean(text):
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def main():
    products = list(Product.objects.all())
    if len(products) < 2:
        print("Need at least 2 products to train. Run seed_products first.")
        return

    # Build corpus: name + description + brand + category
    corpus = []
    for p in products:
        cat = p.category.name if p.category else ""
        corpus.append(_clean(f"{p.name} {p.description} {p.brand} {cat}"))

    print(f"Training on {len(corpus)} product texts...")

    # Step 1: Fit TF-IDF
    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
    sparse_matrix = tfidf.fit_transform(corpus)
    tfidf_dim = sparse_matrix.shape[1]
    print(f"TF-IDF vocabulary: {tfidf_dim} features")

    # Step 2: Train Autoencoder
    from ai_service.services.embedding import TextAutoencoder

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

    # Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "tfidf.pkl"), "wb") as f:
        pickle.dump(tfidf, f)
    torch.save(
        {"model": model.state_dict(), "input_dim": tfidf_dim},
        os.path.join(MODEL_DIR, "autoencoder.pt"),
    )
    print(f"Saved TF-IDF + Autoencoder to {MODEL_DIR}/")

    # Verify
    model.eval()
    with torch.no_grad():
        _, embeddings = model(X)
    print(f"Embedding shape: {embeddings.shape}")
    # Quick similarity check
    norms = embeddings / embeddings.norm(dim=1, keepdim=True)
    sim = norms @ norms.T
    print(f"Self-similarity range: [{sim.min():.3f}, {sim.max():.3f}]")


if __name__ == "__main__":
    main()
