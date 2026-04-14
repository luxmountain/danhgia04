# AI-Service Design Document

## 1. System Overview

Hệ thống gồm 2 microservice Django chạy độc lập:

| Service | Port | DB | Responsibility |
|---|---|---|---|
| **product-service** | 8001 | PostgreSQL (product_service) | Product catalog, search |
| **ai-service** | 8000 | PostgreSQL (ai_service) + Neo4j + Redis | Recommendations, GNN, RAG chat |

AI-service gọi product-service qua HTTP. Không share database.

**Nguyên tắc: Tự xây dựng toàn bộ, không dùng model bên ngoài.**

```
product-service (8001)              ai-service (8000)
┌──────────────────┐               ┌──────────────────────────┐
│ GET /products/   │◄──── HTTP ────│ product_client.py        │
│ GET /products/id │               │                          │
│ GET /search/     │               │ POST /track/             │
└──────────────────┘               │ GET  /recommend/<uid>/   │
                                   │ GET  /similar/<pid>/     │
                                   │ POST /chat/              │
                                   │                          │
                                   │ Neo4j ← graph.py         │
                                   │ FAISS ← vector_store.py  │
                                   │ GNN   ← gnn.py           │
                                   └──────────────────────────┘
```

## 2. Self-Trained Models

### 2.1 Text Embedding: TF-IDF + Autoencoder

```
Product text → TF-IDF (5000 features, bigrams) → Autoencoder → Dense (128d)
```

- Train trên product data fetched từ product-service
- Autoencoder: Linear(5000→256→128), MSE loss, 100 epochs

### 2.2 GNN: GraphSAGE + BPR Loss

```
Bipartite graph User ↔ Product (from Neo4j)
    → GNN Encoder (2-layer GraphSAGE, dim=128)
    → h_u, h_p embeddings
    → BPR loss training
```

### 2.3 Response Generator (thay LLM)

```
Query → Intent Detection (6 intents) → Template → Fill with graph + vector context
```

### 2.4 Embedding Fusion

```
Text (128d) + GNN (128d) → Concat (256d) → Normalize → FAISS
```

## 3. Knowledge Graph (Neo4j)

| Edge | From → To | Properties |
|---|---|---|
| `INTERACTED` | User → Product | weight, types[] |
| `SEARCHED` | User → Query | — |
| `BELONGS_TO` | Product → Category | — |
| `SIMILAR` | Product ↔ Product | score |

Edge weight: `w(u,p) = 1·clicks + 3·cart + 5·purchases`

## 4. Data

### 4.1 Seed Data
1000 sản phẩm thực từ Amazon (Bright Data dataset), 15+ categories.
CSV file: `data/amazon-products.csv`

### 4.2 Interaction Simulation
Conversion funnel: view(100%) → click(50%) → cart(20%) → purchase(8%)

## 5. Docker Compose

```
docker-compose:
  ├── db              (ai-service PostgreSQL, port 5432)
  ├── product-db      (product-service PostgreSQL, port 5433)
  ├── neo4j           (port 7474/7687)
  ├── redis           (port 6379)
  ├── product-service (port 8001)
  └── ai-service      (port 8000)
```

## 6. Training Pipeline

```bash
cd product_service && python manage.py seed_products          # Seed CSV → product DB
python manage.py seed_products                                 # Sync → Neo4j
python ai_service/scripts/simulate_interactions.py             # Collect data
python ai_service/scripts/train_embeddings.py                  # TF-IDF + Autoencoder
python ai_service/scripts/export_graph.py                      # Neo4j → JSON
python ai_service/scripts/train_gnn.py                         # GraphSAGE + BPR
python ai_service/scripts/build_index.py                       # FAISS index
```
