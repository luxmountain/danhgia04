import os, json, faiss
import numpy as np

_DIM = int(os.getenv("EMBEDDING_DIM", "128"))
_DATA_DIR = os.getenv("VECTOR_STORE_DIR", "data/faiss")


class VectorStore:
    def __init__(self, name: str, dim: int = _DIM):
        self.name = name
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # inner-product (cosine on normalized vecs)
        self.ids: list[int] = []

    def add(self, ids: list[int], vectors: np.ndarray):
        vectors = np.ascontiguousarray(vectors, dtype="float32")
        self.index.add(vectors)
        self.ids.extend(ids)

    def search(self, query: np.ndarray, k: int = 10) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        q = np.ascontiguousarray(query.reshape(1, -1), dtype="float32")
        scores, indices = self.index.search(q, min(k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({"id": self.ids[idx], "score": float(score)})
        return results

    def save(self):
        os.makedirs(_DATA_DIR, exist_ok=True)
        faiss.write_index(self.index, os.path.join(_DATA_DIR, f"{self.name}.index"))
        with open(os.path.join(_DATA_DIR, f"{self.name}_ids.json"), "w") as f:
            json.dump(self.ids, f)

    def load(self):
        idx_path = os.path.join(_DATA_DIR, f"{self.name}.index")
        ids_path = os.path.join(_DATA_DIR, f"{self.name}_ids.json")
        if os.path.exists(idx_path):
            self.index = faiss.read_index(idx_path)
            with open(ids_path) as f:
                self.ids = json.load(f)


# Singleton stores
product_store = VectorStore("products")
product_store.load()
