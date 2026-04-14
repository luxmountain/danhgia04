# AI-Service Design Document

## 1. System Overview

AI-service layer cho hệ thống e-commerce microservice Django, gồm 3 subsystem chính:

1. **Knowledge Graph** (Neo4j) — lưu trữ quan hệ User ↔ Product ↔ Category ↔ Query
2. **Deep Learning** (GNN) — tạo embedding cho User và Product từ graph
3. **RAG Chat** — chatbot hỗ trợ khách hàng dựa trên graph context + vector search

```
[User Actions] → Kafka → interaction-service → AI-service
                                                  ├── Neo4j (Graph)
                                                  ├── GNN Model (Embeddings)
                                                  ├── FAISS (Vector Search)
                                                  └── LLM (RAG Chat)
```

## 2. Microservice Context

| Service | Responsibility |
|---|---|
| user-service | Profiles, auth |
| product-service | Catalog, categories |
| interaction-service | Log events (view, click, cart, purchase, search) |
| **ai-service** | Graph, GNN, Recommendation, RAG Chat |

AI-service giao tiếp với các service khác qua Kafka events và REST API.

## 3. Knowledge Graph (Neo4j)

### 3.1 Graph Schema

**Nodes:**

| Node | Properties |
|---|---|
| `User` | id, name |
| `Product` | id, name, description, price |
| `Category` | id, name |
| `Query` | id, text |

**Edges:**

| Edge | From → To | Properties |
|---|---|---|
| `VIEWED` | User → Product | weight, timestamp |
| `CLICKED` | User → Product | weight, timestamp |
| `ADDED_TO_CART` | User → Product | weight, timestamp |
| `PURCHASED` | User → Product | weight, timestamp |
| `SEARCHED` | User → Query | timestamp |
| `BELONGS_TO` | Product → Category | — |
| `SIMILAR` | Product ↔ Product | score |

### 3.2 Edge Weight Formula

Aggregate raw events thành weighted edges:

```
w(u, p) = α · clicks + β · cart + γ · purchases
```

Suggested: α=1, β=3, γ=5

### 3.3 Cypher Query Examples

```cypher
-- Log interaction
MERGE (u:User {id: $user_id})
MERGE (p:Product {id: $product_id})
MERGE (u)-[r:VIEWED]->(p)
ON CREATE SET r.weight = 1
ON MATCH SET r.weight = r.weight + 1

-- Get recommendations via graph traversal
MATCH (u:User {id: $uid})-[:VIEWED|PURCHASED]->(p:Product)
MATCH (p)-[:SIMILAR]->(rec:Product)
WHERE NOT (u)-[:PURCHASED]->(rec)
RETURN rec.id, SUM(r.weight) AS score
ORDER BY score DESC LIMIT 10
```

## 4. Deep Learning — Graph Neural Networks

### 4.1 Architecture

Sử dụng GNN (GraphSAGE / GAT) trên heterogeneous graph từ Neo4j.

```
Input: Graph G = (V, E) from Neo4j
       ↓
GNN Encoder (2-3 layers)
       ↓
h_u = GNN(N(u))   →  User embedding (dim=128)
h_p = GNN(N(p))   →  Product embedding (dim=128)
       ↓
Downstream tasks: Recommendation, Segmentation
```

### 4.2 Model Details

- **Framework:** PyTorch + PyG (PyTorch Geometric)
- **Model:** GraphSAGE hoặc GAT
- **Input features:**
  - User: interaction counts, search history encoding
  - Product: text embedding (SentenceTransformer), price, category one-hot
- **Training:** Link prediction (predict User→Product edges)
- **Loss:** BPR Loss (Bayesian Personalized Ranking)

### 4.3 Recommendation Flow

```
1. Export graph from Neo4j → PyG HeteroData
2. Train GNN → get user/product embeddings
3. Store embeddings in FAISS index
4. At inference: query FAISS for top-K similar products
```

### 4.4 Embedding Update Strategy

- **Batch retrain:** nightly cron job, re-export graph, retrain GNN
- **Incremental:** cache new interactions, periodic fine-tune

## 5. RAG Chat System

### 5.1 Pipeline

```
User Query
    ↓
[1] Embed query (SentenceTransformer)
    ↓
[2] Retrieve context:
    ├── FAISS: similar products by vector
    ├── Neo4j: graph neighbors (user history, related products)
    └── Merge → GraphRAG context
    ↓
[3] Augmented Prompt → LLM
    ↓
[4] Response to user
```

### 5.2 GraphRAG Context Building

```cypher
-- Get user's recent interactions for context
MATCH (u:User {id: $uid})-[r:VIEWED|PURCHASED]->(p:Product)
RETURN p.name, p.description, type(r) AS action
ORDER BY r.timestamp DESC LIMIT 10
```

Kết hợp graph context + vector search results → prompt cho LLM.

### 5.3 LLM Options

| Option | Use case |
|---|---|
| OpenAI GPT-4o-mini | Quick MVP, high quality |
| LLaMA (local) | Privacy, cost control |

## 6. Tech Stack

| Layer | Technology |
|---|---|
| API Gateway | Django REST Framework |
| AI Service | FastAPI (async, ML serving) |
| Graph DB | Neo4j |
| Vector DB | FAISS |
| ML Framework | PyTorch + PyG |
| Text Embedding | SentenceTransformer |
| Event Streaming | Kafka |
| Cache | Redis |
| Relational DB | PostgreSQL |
| LLM | OpenAI API / LLaMA |

## 7. API Endpoints (AI-Service)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/track/` | Log user interaction → Neo4j |
| GET | `/api/recommend/{user_id}/` | Get top-K recommendations |
| POST | `/api/chat/` | RAG chat query |
| POST | `/api/embeddings/retrain/` | Trigger GNN retrain |
| GET | `/api/similar/{product_id}/` | Similar products |

## 8. Data Flow

```
User clicks/searches/buys
        ↓
interaction-service → Kafka event
        ↓
ai-service consumer:
  ├── Write to PostgreSQL (raw log)
  ├── Update Neo4j graph (weighted edges)
  └── Invalidate Redis cache
        ↓
Nightly batch:
  ├── Export Neo4j → PyG graph
  ├── Train GNN → embeddings
  └── Index embeddings → FAISS
        ↓
Serve:
  ├── /recommend → FAISS lookup
  ├── /chat → GraphRAG pipeline
  └── /similar → FAISS lookup
```

## 9. Deployment

```
docker-compose:
  ├── neo4j (port 7687)
  ├── postgres (port 5432)
  ├── redis (port 6379)
  ├── kafka + zookeeper
  ├── ai-service (FastAPI, port 8001)
  └── django-gateway (port 8000)
```
