# AI-Service Design Document

## 1. System Overview

AI-service layer cho hệ thống e-commerce microservice Django, gồm 3 subsystem chính:

1. **Knowledge Graph** (Neo4j) — lưu trữ quan hệ User ↔ Product ↔ Category
2. **Deep Learning** (GNN + Self-trained Embeddings) — tạo embedding cho User và Product
3. **RAG Chat** — chatbot hỗ trợ khách hàng dựa trên graph context + vector search

**Nguyên tắc: Tự xây dựng toàn bộ, không dùng model bên ngoài (no OpenAI, no pretrained transformers).**

```
[User Actions] → POST /api/track/ → PostgreSQL + Neo4j
                                          ↓
                                    Training Pipeline:
                                    ├── train_embeddings.py  (TF-IDF + Autoencoder)
                                    ├── export_graph.py      (Neo4j → JSON)
                                    ├── train_gnn.py         (GNN → embeddings)
                                    └── build_index.py       (FAISS index + SIMILAR edges)
                                          ↓
                                    Serve:
                                    ├── GET  /api/recommend/<user_id>/
                                    ├── GET  /api/similar/<product_id>/
                                    └── POST /api/chat/  (GraphRAG)
```

## 2. Self-Trained Models

### 2.1 Text Embedding: TF-IDF + Autoencoder

Thay vì dùng SentenceTransformer pretrained, tự train text encoder:

```
Product text → TF-IDF (5000 features, bigrams) → Autoencoder → Dense embedding (128d)
```

- **TF-IDF**: Fit trên toàn bộ product corpus (name + description + brand + category)
- **Autoencoder**: Linear(5000→256→128) encoder, Linear(128→256→5000) decoder
- **Training**: MSE reconstruction loss, 100 epochs
- **Output**: 128-dim normalized vector per product

### 2.2 GNN: GraphSAGE + BPR Loss

```
Input: Bipartite graph User ↔ Product (from Neo4j)
       ↓
GNN Encoder (2-layer GraphSAGE, dim=128)
       ↓
h_u = GNN(N(u))   →  User embedding (128d)
h_p = GNN(N(p))   →  Product embedding (128d)
       ↓
Training: BPR loss (positive/negative edge sampling)
```

### 2.3 Response Generator (thay LLM)

Thay vì gọi OpenAI API, tự xây response generator:

```
User query → Intent Detection (keyword matching, 6 intents)
                ↓
          Template Selection → Fill with:
                                ├── Vector search results (product list)
                                └── Graph context (user history)
                ↓
          Structured response (Vietnamese)
```

Intents: `recommend`, `cheap`, `compare`, `similar`, `best`, `info`

### 2.4 Embedding Fusion

```
Text embedding (128d, self-trained) + GNN embedding (128d) → Concat (256d) → Normalize → FAISS
```

## 3. Knowledge Graph (Neo4j)

### 3.1 Graph Schema

| Node | Properties |
|---|---|
| `User` | id |
| `Product` | id, name, description, price |
| `Category` | id, name |

| Edge | From → To | Properties |
|---|---|---|
| `INTERACTED` | User → Product | weight, types[] |
| `SEARCHED` | User → Query | — |
| `BELONGS_TO` | Product → Category | — |
| `SIMILAR` | Product ↔ Product | score |

### 3.2 Edge Weight

```
w(u, p) = 1·clicks + 3·cart + 5·purchases
```

## 4. Data Collection

### 4.1 Seed Data
1000 sản phẩm thực từ Amazon (Bright Data dataset), 15+ categories.
CSV file: `data/amazon-products.csv`

### 4.2 Interaction Simulation
Script `simulate_interactions.py` tạo realistic user behavior:
- Conversion funnel: view(100%) → click(50%) → cart(20%) → purchase(8%)
- Users prefer 1-2 categories (realistic browsing pattern)

## 5. Tech Stack

| Layer | Technology |
|---|---|
| API | Django REST Framework |
| Graph DB | Neo4j (Cypher) |
| Vector DB | FAISS |
| GNN | PyTorch + PyG (GraphSAGE) |
| Text Embedding | Self-trained (TF-IDF + Autoencoder) |
| Chat | Self-built (Intent + Template + Retrieval) |
| Database | PostgreSQL |
| Cache | Redis |

**Không dependency nào vào external AI API hoặc pretrained model.**

## 6. Training Pipeline

```bash
# 1. Seed products
python manage.py seed_products --sync-neo4j

# 2. Simulate user interactions (data collection)
python ai_service/scripts/simulate_interactions.py --users 50 --actions 500

# 3. Train text embeddings (TF-IDF + Autoencoder)
python ai_service/scripts/train_embeddings.py

# 4. Export graph from Neo4j
python ai_service/scripts/export_graph.py

# 5. Train GNN (GraphSAGE + BPR)
python ai_service/scripts/train_gnn.py

# 6. Build FAISS index + write SIMILAR edges
python ai_service/scripts/build_index.py
```

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/` | List products (filter, paginate) |
| GET | `/api/products/<id>/` | Product detail |
| GET | `/api/products/search/?q=` | Search by keyword |
| POST | `/api/track/` | Log interaction → Neo4j |
| GET | `/api/recommend/<user_id>/` | Graph-based recommendations |
| GET | `/api/similar/<product_id>/` | FAISS vector similarity |
| POST | `/api/chat/` | GraphRAG chat (self-built) |
