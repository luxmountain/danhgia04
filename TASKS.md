# AI-Service Implementation Tasks

## Phase 1: Foundation (Week 1–2)

### 1.1 Project Setup
- [ ] Init Django project (`ai_service`)
- [ ] Init FastAPI app (ML serving)
- [ ] Setup `docker-compose.yml`: Neo4j, PostgreSQL, Redis, Kafka
- [ ] Configure Django settings (DB, Redis, Kafka consumer)
- [ ] Setup project directory structure

### 1.2 Data Models (Django)
- [ ] Create `User` model
- [ ] Create `Product` model (name, description, price, category)
- [ ] Create `Interaction` model (user, product, event_type, query, timestamp)
- [ ] Migrations + seed data

### 1.3 Neo4j Graph Setup
- [ ] Neo4j connection service (`services/graph.py`)
- [ ] Create graph constraints/indexes (User.id, Product.id unique)
- [ ] `log_interaction()` — MERGE nodes + weighted edges
- [ ] `sync_products()` — sync Product + Category nodes from PostgreSQL
- [ ] Script: bulk import existing data → Neo4j

### 1.4 Event Pipeline
- [ ] Kafka producer in interaction-service (emit events on view/click/cart/purchase/search)
- [ ] Kafka consumer in ai-service (consume → write PostgreSQL + update Neo4j)
- [ ] Edge weight aggregation: `w(u,p) = α·clicks + β·cart + γ·purchases`

---

## Phase 2: Recommendation Engine (Week 3–4)

### 2.1 Graph-based Recommendation (Baseline)
- [ ] Cypher query: co-occurrence recommendation (users who bought X also bought Y)
- [ ] Cypher query: graph traversal recommendation (user→products→similar→recommend)
- [ ] API endpoint: `GET /api/recommend/{user_id}/`
- [ ] Redis caching for recommendations

### 2.2 GNN Embeddings
- [ ] Neo4j → PyG export script (`scripts/export_graph.py`)
  - Export nodes + edges → `torch_geometric.data.HeteroData`
- [ ] GNN model (`models/gnn.py`)
  - GraphSAGE or GAT (2-layer, dim=128)
  - Heterogeneous message passing (User, Product, Category)
- [ ] Training pipeline (`scripts/train_gnn.py`)
  - Link prediction task (predict User→Product edges)
  - BPR loss
  - Train/val/test split on edges
- [ ] Save user + product embeddings to file

### 2.3 FAISS Vector Index
- [ ] Build FAISS index from product embeddings
- [ ] `VectorStore` service: add, search, rebuild
- [ ] API endpoint: `GET /api/similar/{product_id}/`
- [ ] Upgrade `/recommend/` to use FAISS (embedding-based)

### 2.4 Batch Pipeline
- [ ] Nightly cron script: export → train → index
- [ ] Logging + metrics for training runs

---

## Phase 3: RAG Chat System (Week 5–6)

### 3.1 Text Embeddings
- [ ] SentenceTransformer integration (`services/embedding.py`)
- [ ] Embed all product descriptions → FAISS index
- [ ] Embed user queries at inference time

### 3.2 GraphRAG Retrieval
- [ ] Graph context retriever: user history + related products from Neo4j
- [ ] Vector context retriever: FAISS similarity search on query
- [ ] Merge graph + vector context → ranked context list

### 3.3 LLM Integration
- [ ] LLM service (`services/llm.py`) — OpenAI API wrapper
- [ ] Prompt template: system prompt + context + user query
- [ ] Conversation history management (Redis)

### 3.4 Chat API
- [ ] API endpoint: `POST /api/chat/`
  - Input: `{user_id, query, session_id}`
  - Output: `{answer, sources[]}`
- [ ] Rate limiting
- [ ] Response streaming (SSE)

---

## Phase 4: Integration & Polish (Week 7–8)

### 4.1 API Gateway (Django)
- [ ] Django REST endpoints proxying to FastAPI ai-service
- [ ] Authentication middleware (JWT from user-service)
- [ ] API documentation (Swagger/OpenAPI)

### 4.2 Product Similarity Pipeline
- [ ] Compute product-product similarity (cosine on embeddings)
- [ ] Write `SIMILAR` edges back to Neo4j (top-K per product)
- [ ] Periodic refresh

### 4.3 Monitoring & Evaluation
- [ ] Recommendation metrics: Precision@K, Recall@K, NDCG
- [ ] RAG evaluation: relevance scoring on test queries
- [ ] Logging: request latency, model inference time
- [ ] Health check endpoints

### 4.4 Deployment
- [ ] Dockerfile for ai-service (FastAPI + PyTorch)
- [ ] docker-compose full stack
- [ ] Environment config (.env)
- [ ] README with setup instructions

---

## Phase 5: Research Extensions (Optional)

- [ ] SPD manifold embeddings for users (Xu ∈ SPD(d))
- [ ] Trust propagation on graph (Affine-Invariant Metric)
- [ ] Advanced GraphRAG: multi-hop reasoning
- [ ] User segmentation via GNN clustering
- [ ] Intent prediction model (search → action)
- [ ] Anomaly/fraud detection on interaction patterns
