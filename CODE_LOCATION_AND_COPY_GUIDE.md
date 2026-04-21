# 💻 CODE CỦA CÁC MODEL - VỊ TRÍ CHI TIẾT

## 📍 CÁC FILE CODE CỦA MODEL

### 1️⃣ **MODEL DEFINITION** (Architecture)

**File**: `d:/AI-SERVICE/danhgia04/ai_service/models/gnn.py`

**Nội dung**:
- ✅ **GNNEncoder** - Base encoder (GraphSAGE)
- ✅ **RecModel** - Recommendation model (cho graph)
- ✅ **TextAutoencoder** - Text embedding model
- ⚠️ **BiLSTM code** - Ở `ai_service/services/embedding.py` (tích hợp trong EmbeddingService)

---

### 2️⃣ **TRAINING SCRIPT** (Train models)

**File**: `d:/AI-SERVICE/danhgia04/ai_service/scripts/train_gnn.py`

**Nội dung**:
- ✅ Load edges từ JSON
- ✅ Build heterogeneous data
- ✅ Initialize RecModel
- ✅ Training loop (BPR loss)
- ✅ Save embeddings

**Chạy**:
```bash
cd d:/AI-SERVICE/danhgia04
python ai_service/scripts/train_gnn.py
```

---

### 3️⃣ **TEXT EMBEDDING TRAINING**

**File**: `d:/AI-SERVICE/danhgia04/ai_service/scripts/train_embeddings.py`

**Nội dung**:
- ✅ TF-IDF vectorization
- ✅ Autoencoder architecture (để embedding)
- ✅ Training loop (MSE loss)
- ✅ Save models

**Chạy**:
```bash
python ai_service/scripts/train_embeddings.py
```

---

### 4️⃣ **DATA PREPARATION** (Processing dataset)

**File**: `d:/AI-SERVICE/danhgia04/ai_service/scripts/simulate_interactions.py`

**Nội dung**:
- ✅ Load products từ product-service
- ✅ Simulate user interactions
- ✅ Create sequences (for LSTM training)
- ✅ Save vào PostgreSQL + Neo4j

**Chạy**:
```bash
python ai_service/scripts/simulate_interactions.py --users 500 --actions 4000
```

---

## 🔍 **COPY CODE ỚI ĐÂU**

### **Cho BiLSTM Model** → `ai_service/models/gnn.py`

```python
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

    def bpr_loss(self, user_emb, pos_prod_emb, neg_prod_emb):
        """BPR (Bayesian Personalized Ranking) loss"""
        pos_score = (user_emb * pos_prod_emb).sum(dim=1)
        neg_score = (user_emb * neg_prod_emb).sum(dim=1)
        return -(pos_score - neg_score).sigmoid().log().mean()
```

### **Cho Text Embedding (Autoencoder)** → `ai_service/scripts/train_embeddings.py`

```python
class TextAutoencoder(nn.Module):
    def __init__(self, input_dim: int, embed_dim: int = EMBED_DIM):
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

# Training loop
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
```

### **Cho GNN Training Loop** → `ai_service/scripts/train_gnn.py`

```python
model = RecModel(num_users, num_products, GNN_DIM)
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

# Prepare edges
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

# Save model
torch.save(model.state_dict(), os.path.join(DATA_DIR, "gnn_model.pt"))
```

---

## 📂 **TỔNG HỢP FILE CODE**

| Loại | File | Nội Dung |
|------|------|---------|
| **Model Def** | `ai_service/models/gnn.py` | RecModel, GNNEncoder, Embedding |
| **Training** | `ai_service/scripts/train_gnn.py` | GNN training loop |
| **Text Embed** | `ai_service/scripts/train_embeddings.py` | Autoencoder + TF-IDF |
| **Data Prep** | `ai_service/scripts/simulate_interactions.py` | Load data + sequences |
| **Embedding Service** | `ai_service/services/embedding.py` | TextAutoencoder inference |
| **Graph Service** | `ai_service/services/graph.py` | Neo4j operations |

---

## 🔧 **CÁCH COPY CODE**

### **Option 1: Copy từng file**

1. Mở file cần copy
2. Select code (Ctrl+A)
3. Copy (Ctrl+C)
4. Paste vào báo cáo (Ctrl+V)

### **Option 2: Copy từ terminal**

```bash
# Xem nội dung file
type ai_service/models/gnn.py

# Hoặc mở trực tiếp
notepad ai_service/models/gnn.py
```

### **Option 3: Copy từ VS Code**

1. Mở VS Code
2. File → Open Folder → `d:/AI-SERVICE/danhgia04`
3. Mở file cần copy
4. Copy code

---

## 📝 **CODE STRUCTURE QUICK VIEW**

### **`ai_service/models/gnn.py`** (80 lines)
```python
class GNNEncoder(torch.nn.Module):
    # GraphSAGE encoder (2 layers)
    
class RecModel(torch.nn.Module):
    # Recommendation model (embeddings + BPR loss)
    
def build_hetero_data(edges, num_users, num_products):
    # Build heterogeneous graph data
```

### **`ai_service/scripts/train_gnn.py`** (60 lines)
```python
def main():
    # Load edges
    # Build model
    # Training loop
    # Save embeddings
```

### **`ai_service/scripts/train_embeddings.py`** (80 lines)
```python
class TextAutoencoder(nn.Module):
    # Encoder-Decoder
    
def _fetch_all_products():
    # Fetch từ product-service
    
def main():
    # TF-IDF → Autoencoder training
    # Save models
```

### **`ai_service/scripts/simulate_interactions.py`** (100 lines)
```python
def _fetch_all_products():
    # Fetch products
    
def main(users, actions):
    # Create user sequences
    # Log to DB + Neo4j
```

---

## 🎯 **PHẦN CODE CHÍNH CHO YÊU CẦU 4 (YC2a)**

### **Đúng là BiLSTM ở đâu?**

❌ **KHÔNG phải** ở `ai_service/models/gnn.py` (đó là GNN architecture)

✅ **BiLSTM code** ở các chỗ:

**1. Definition**:
```python
# File: ai_service/scripts/train_gnn.py (sử dụng RecModel)
# hoặc có thể tạo class BiLSTM riêng

class BiLSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super().__init__()
        self.bilstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, bidirectional=True, dropout=0.3
        )
        self.fc = nn.Linear(2 * hidden_size, num_classes)
    
    def forward(self, x):
        out, (h_n, c_n) = self.bilstm(x)
        return self.fc(out[:, -1, :])
```

**2. Training**:
```python
# Chỗ này nên thêm vào train_gnn.py hoặc tạo file mới
model = BiLSTMModel(input_size=8, hidden_size=128, num_layers=2, num_classes=8)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(1, 50 + 1):
    model.train()
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = loss_fn(outputs, y_batch)
        loss.backward()
        optimizer.step()
```

---

## 💡 **TÓML**:

| Cần Copy | File | Line Range |
|----------|------|-----------|
| **Model Classes** | `ai_service/models/gnn.py` | All |
| **Training Loop** | `ai_service/scripts/train_gnn.py` | Line 30-60 |
| **Data Prep** | `ai_service/scripts/simulate_interactions.py` | Line 1-40 |
| **Embedding** | `ai_service/scripts/train_embeddings.py` | All |

**Mở file và copy code theo bảng trên!** 📋
