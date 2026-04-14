"""
Self-trained text embedding model.
Pipeline: Text → TF-IDF (sparse) → Autoencoder (dense, dim=128)
No external pretrained models used.
"""
import os, re, pickle
import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer

_DIM = int(os.getenv("EMBEDDING_DIM", "128"))
_MODEL_DIR = os.getenv("MODEL_DIR", "data/models")


def _clean(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


class TextAutoencoder(nn.Module):
    """Compress TF-IDF vectors to dense embeddings."""

    def __init__(self, input_dim: int, embed_dim: int = _DIM):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, embed_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z

    def encode(self, x):
        with torch.no_grad():
            return self.encoder(x)


class EmbeddingService:
    def __init__(self):
        self.tfidf: TfidfVectorizer | None = None
        self.autoencoder: TextAutoencoder | None = None
        self._loaded = False

    @property
    def dim(self):
        return _DIM

    def _load(self):
        if self._loaded:
            return
        tfidf_path = os.path.join(_MODEL_DIR, "tfidf.pkl")
        ae_path = os.path.join(_MODEL_DIR, "autoencoder.pt")
        if os.path.exists(tfidf_path) and os.path.exists(ae_path):
            with open(tfidf_path, "rb") as f:
                self.tfidf = pickle.load(f)
            state = torch.load(ae_path, map_location="cpu", weights_only=True)
            self.autoencoder = TextAutoencoder(state["input_dim"], _DIM)
            self.autoencoder.load_state_dict(state["model"])
            self.autoencoder.eval()
        self._loaded = True

    def is_trained(self) -> bool:
        self._load()
        return self.tfidf is not None and self.autoencoder is not None

    def embed_text(self, text: str) -> np.ndarray:
        self._load()
        if not self.is_trained():
            # Fallback: hash-based embedding (before training)
            return self._hash_embed(text)
        sparse = self.tfidf.transform([_clean(text)])
        dense = torch.tensor(sparse.toarray(), dtype=torch.float32)
        vec = self.autoencoder.encode(dense).numpy()[0]
        # L2 normalize
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        self._load()
        if not self.is_trained():
            return np.array([self._hash_embed(t) for t in texts])
        sparse = self.tfidf.transform([_clean(t) for t in texts])
        dense = torch.tensor(sparse.toarray(), dtype=torch.float32)
        vecs = self.autoencoder.encode(dense).numpy()
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vecs / norms

    @staticmethod
    def _hash_embed(text: str) -> np.ndarray:
        """Deterministic fallback before model is trained."""
        np.random.seed(hash(_clean(text)) % (2**31))
        vec = np.random.randn(_DIM).astype("float32")
        return vec / np.linalg.norm(vec)


embedding_service = EmbeddingService()
