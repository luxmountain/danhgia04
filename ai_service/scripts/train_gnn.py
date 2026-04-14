"""Train GNN model on exported graph data and save embeddings."""
import json, os, sys
import torch
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
load_dotenv()

from ai_service.models.gnn import RecModel, build_hetero_data

DATA_DIR = os.getenv("DATA_DIR", "data")
GNN_DIM = int(os.getenv("GNN_DIM", "128"))
EPOCHS = int(os.getenv("GNN_EPOCHS", "50"))
LR = 3e-3


def main():
    with open(os.path.join(DATA_DIR, "edges.json")) as f:
        edges = json.load(f)

    if not edges:
        print("No edges found. Run export_graph first.")
        return

    edge_index, edge_weight, uid_map, pid_map = build_hetero_data(
        edges, num_users=0, num_products=0
    )
    num_users = len(uid_map)
    num_products = len(pid_map)
    print(f"Graph: {num_users} users, {num_products} products, {len(edges)} edges")

    model = RecModel(num_users, num_products, GNN_DIM)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    # Positive edges (user→product)
    pos_u = torch.tensor([uid_map[e["user_id"]] for e in edges])
    pos_p = torch.tensor([pid_map[e["product_id"]] - num_users for e in edges])

    for epoch in range(1, EPOCHS + 1):
        model.train()
        optimizer.zero_grad()

        user_emb, prod_emb = model(edge_index, num_users)

        # Negative sampling
        neg_p = torch.randint(0, num_products, pos_p.shape)

        loss = model.bpr_loss(user_emb[pos_u], prod_emb[pos_p], prod_emb[neg_p])
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch}/{EPOCHS}  loss={loss.item():.4f}")

    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(DATA_DIR, "gnn_model.pt"))

    with torch.no_grad():
        user_emb, prod_emb = model(edge_index, num_users)
    np.save(os.path.join(DATA_DIR, "user_embeddings.npy"), user_emb.numpy())
    np.save(os.path.join(DATA_DIR, "product_embeddings.npy"), prod_emb.numpy())

    # Save ID maps
    with open(os.path.join(DATA_DIR, "uid_map.json"), "w") as f:
        json.dump({str(k): v for k, v in uid_map.items()}, f)
    with open(os.path.join(DATA_DIR, "pid_map.json"), "w") as f:
        json.dump({str(k): v - num_users for k, v in pid_map.items()}, f)

    print(f"Saved model + embeddings to {DATA_DIR}/")


if __name__ == "__main__":
    main()
