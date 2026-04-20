# AI-Service for E-Commerce

AI layer cho hệ thống e-commerce microservice Django — hỗ trợ khách hàng dựa trên hành vi (view, click, cart, purchase, search) với Knowledge Graph + GNN + RAG Chat.

**Toàn bộ model tự train, không dùng external API hay pretrained model.**

## Architecture

```
[Client] → API Gateway (:8080)
                ├── /api/products/*  → product-service (:8001)
                └── /api/ai/*        → ai-service (:8000)

[User Actions] → POST /api/ai/track/ → PostgreSQL + Neo4j
                                              ↓
                                        Training Pipeline:
                                        ├── train_embeddings.py  (TF-IDF + Autoencoder)
                                        ├── export_graph.py      (Neo4j → JSON)
                                        ├── train_gnn.py         (GNN → embeddings)
                                        └── build_index.py       (FAISS index + SIMILAR edges)
                                              ↓
                                        Serve (via Gateway):
                                        ├── GET  /api/ai/recommend/<user_id>/
                                        ├── GET  /api/ai/similar/<product_id>/
                                        └── POST /api/ai/chat/  (GraphRAG)
```

## Microservices

| Service | Port | Responsibility |
|---|---|---|
| **gateway** | 8080 | API Gateway, routing, CORS |
| **product-service** | 8001 | Product catalog, search, categories |
| **ai-service** | 8000 | Recommendations, similarity, RAG chat |

AI-service gọi product-service qua HTTP (`PRODUCT_SERVICE_URL`).

## Tech Stack

| Layer | Technology |
|---|---|
| API | Django REST Framework |
| Graph DB | Neo4j (Cypher) |
| Vector DB | FAISS |
| GNN | PyTorch + PyG (GraphSAGE, BPR loss) |
| Text Embedding | Self-trained (TF-IDF + Autoencoder) |
| Chat | Self-built (Intent Detection + Template + Retrieval) |
| Database | PostgreSQL |
| Cache | Redis |

## Self-Trained Models

| Model | Input | Output | Training |
|---|---|---|---|
| Text Encoder | Product text | 128d dense vector | TF-IDF → Autoencoder (MSE loss) |
| GNN | User-Product graph | 128d user/product embeddings | GraphSAGE + BPR loss |
| Response Generator | Query + context | Structured answer | Intent matching + templates |

## Project Structure

```
├── docker-compose.yml
├── data/
│   └── amazon-products.csv         # 1000 real Amazon products
│
├── api_gateway/                    # API Gateway (port 8080)
│   ├── manage.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── gateway/
│       └── views.py                # Reverse proxy logic
│
├── product_service/                # Independent Django project (port 8001)
│   ├── manage.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── products/
│       ├── models.py               # Category, Product
│       ├── api/
│       │   ├── views.py            # list, detail, search
│       │   ├── serializers.py
│       │   └── urls.py
│       └── management/commands/
│           └── seed_products.py    # Seed from CSV
│
├── ai_service/                     # AI service (port 8000)
│   ├── models/
│   │   ├── django_models.py        # Interaction only
│   │   └── gnn.py                  # GNNEncoder + RecModel
│   ├── services/
│   │   ├── product_client.py       # HTTP client → product-service
│   │   ├── graph.py                # Neo4j service
│   │   ├── embedding.py            # Self-trained TF-IDF + Autoencoder
│   │   ├── vector_store.py         # FAISS IndexFlatIP
│   │   └── llm.py                  # Self-built response generator
│   ├── scripts/
│   │   ├── simulate_interactions.py
│   │   ├── train_embeddings.py
│   │   ├── export_graph.py
│   │   ├── train_gnn.py
│   │   └── build_index.py
│   ├── management/commands/
│   │   └── seed_products.py        # Sync products → Neo4j
│   └── api/
│       ├── views.py                # 4 AI endpoints
│       ├── serializers.py
│       └── urls.py
├── config/                         # AI-service Django config
├── manage.py                       # AI-service manage.py
├── Dockerfile
└── requirements.txt
```

## Setup

```bash
# 1. Config
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Migrate databases
# Product service
cd product_service && python manage.py migrate && cd ..
# AI service
python manage.py migrate

# 4. Seed products (product-service)
cd product_service && python manage.py seed_products && cd ..

# 5. Sync products to Neo4j (ai-service)
python manage.py seed_products

# 6. Simulate user interactions
python ai_service/scripts/simulate_interactions.py --users 50 --actions 500

# 7. Train all models
python ai_service/scripts/train_embeddings.py
python ai_service/scripts/export_graph.py
python ai_service/scripts/train_gnn.py
python ai_service/scripts/build_index.py

# 8. Run servers
cd product_service && python manage.py runserver 8001 &
python manage.py runserver 8000
```

## Seed Data

1000 sản phẩm thực từ Amazon (Bright Data dataset), 15+ categories:

| Category | Products |
|---|---|
| Clothing, Shoes & Jewelry | 216 |
| Home & Kitchen | 143 |
| Tools & Home Improvement | 112 |
| Sports & Outdoors | 76 |
| Electronics | 75 |
| Automotive | 56 |
| Office Products | 45 |
| Health & Household | 33 |
| Beauty | 30 |
| + 6 more categories | ~214 |

Data source: https://github.com/luminati-io/Amazon-dataset-samples

## API Endpoints

### Via Gateway (port 8080) — Single Entry Point

| Method | Gateway URL | Routes to |
|---|---|---|
| GET | `/api/products/` | product-service → `/api/products/` |
| GET | `/api/products/<id>/` | product-service → `/api/products/<id>/` |
| GET | `/api/products/search/?q=` | product-service → `/api/products/search/?q=` |
| POST | `/api/ai/track/` | ai-service → `/api/track/` |
| GET | `/api/ai/recommend/<user_id>/` | ai-service → `/api/recommend/<user_id>/` |
| GET | `/api/ai/similar/<product_id>/` | ai-service → `/api/similar/<product_id>/` |
| POST | `/api/ai/chat/` | ai-service → `/api/chat/` |
| GET | `/health/` | Gateway health check |

### Product Service (port 8001 — internal)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/` | List products (filter by category/brand, pagination) |
| GET | `/api/products/<id>/` | Product detail |
| GET | `/api/products/search/?q=` | Search by keyword |

### AI Service (port 8000 — internal)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/track/` | Log interaction → PostgreSQL + Neo4j |
| GET | `/api/recommend/<user_id>/` | Graph-based recommendations |
| GET | `/api/similar/<product_id>/` | FAISS vector similarity |
| POST | `/api/chat/` | GraphRAG chat (self-built) |

## Training Pipeline

```bash
python ai_service/scripts/train_embeddings.py     # TF-IDF + Autoencoder
python ai_service/scripts/export_graph.py          # Neo4j → JSON
python ai_service/scripts/train_gnn.py             # GraphSAGE + BPR loss
python ai_service/scripts/build_index.py           # FAISS index + SIMILAR edges
```

## Key Design Decisions

- **Microservice**: gateway (port 8080) + product-service (port 8001) + ai-service (port 8000), giao tiếp qua HTTP
- **API Gateway**: Single entry point, reverse proxy bằng Django, CORS handling
- **Self-trained only**: Không dùng OpenAI, SentenceTransformer, hay bất kỳ pretrained model nào
- **Text Embedding**: TF-IDF (5000 features, bigrams) → Autoencoder (128d)
- **GNN**: GraphSAGE 2-layer + BPR loss
- **Response Generator**: Intent detection (6 intents) + template matching + graph/vector context
- **Edge weight**: `w(u,p) = 1·clicks + 3·cart + 5·purchases`
- **Embedding fusion**: Text (128d) + GNN (128d) → concat (256d) → normalize → FAISS
