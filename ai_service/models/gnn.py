"""
GNN model for learning user/product embeddings from the interaction graph.
Architecture: 2-layer GraphSAGE with BPR loss for link prediction.
"""
import os
import torch
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.nn import SAGEConv
from torch_geometric.data import HeteroData
import torch_geometric.transforms as T

_DIM = int(os.getenv("GNN_DIM", "128"))


class GNNEncoder(torch.nn.Module):
    """2-layer GraphSAGE encoder for bipartite User-Product graph."""

    def __init__(self, in_dim: int, hidden_dim: int = _DIM):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        x = F.relu(self.conv1(x, edge_index))
        return self.conv2(x, edge_index)


class RecModel(torch.nn.Module):
    """
    Heterogeneous GNN recommendation model.
    Nodes: User, Product  |  Edges: INTERACTED (user→product)
    Training: BPR loss on positive/negative edges.
    """

    def __init__(self, num_users: int, num_products: int, embed_dim: int = _DIM):
        super().__init__()
        self.user_emb = torch.nn.Embedding(num_users, embed_dim)
        self.prod_emb = torch.nn.Embedding(num_products, embed_dim)
        self.encoder = GNNEncoder(embed_dim, embed_dim)
        self.reset_parameters()

    def reset_parameters(self):
        torch.nn.init.xavier_uniform_(self.user_emb.weight)
        torch.nn.init.xavier_uniform_(self.prod_emb.weight)

    def forward(self, edge_index: Tensor, num_users: int) -> tuple[Tensor, Tensor]:
        """Return (user_embeddings, product_embeddings)."""
        x = torch.cat([self.user_emb.weight, self.prod_emb.weight], dim=0)
        x = self.encoder(x, edge_index)
        return x[:num_users], x[num_users:]

    def bpr_loss(self, user_emb: Tensor, pos_emb: Tensor, neg_emb: Tensor) -> Tensor:
        pos_scores = (user_emb * pos_emb).sum(dim=-1)
        neg_scores = (user_emb * neg_emb).sum(dim=-1)
        return -F.logsigmoid(pos_scores - neg_scores).mean()


def build_hetero_data(edges: list[dict], num_users: int, num_products: int) -> tuple:
    """
    Convert exported Neo4j edges to PyG tensors.
    edges: [{"user_id": int, "product_id": int, "weight": float}, ...]
    Returns: (edge_index, edge_weight, user_id_map, product_id_map)
    """
    user_ids = sorted({e["user_id"] for e in edges})
    prod_ids = sorted({e["product_id"] for e in edges})
    uid_map = {uid: i for i, uid in enumerate(user_ids)}
    pid_map = {pid: i + len(uid_map) for i, pid in enumerate(prod_ids)}

    src, dst, weights = [], [], []
    for e in edges:
        u = uid_map[e["user_id"]]
        p = pid_map[e["product_id"]]
        src.extend([u, p])  # bidirectional
        dst.extend([p, u])
        w = e.get("weight", 1.0)
        weights.extend([w, w])

    edge_index = torch.tensor([src, dst], dtype=torch.long)
    edge_weight = torch.tensor(weights, dtype=torch.float)
    return edge_index, edge_weight, uid_map, pid_map
