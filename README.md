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
                                        Training Pipeline (Product):
                                        ├── train_embeddings.py  (TF-IDF + Autoencoder)
                                        ├── export_graph.py      (Neo4j → JSON)
                                        ├── train_gnn.py         (GNN → embeddings)
                                        └── build_index.py       (FAISS index + SIMILAR edges)
                                              ↓
                                        Serve (via Gateway):
                                        ├── GET  /api/ai/recommend/<user_id>/
                                        ├── GET  /api/ai/similar/<product_id>/
                                        └── POST /api/ai/chat/  (GraphRAG)

[data_user500.csv] → Behavior Pipeline:
                     ├── prepare_user_data.py   (Kaggle REES46 → 500 users × 8 behaviors)
                     ├── train_behavior_models.py (RNN / LSTM / BiLSTM classification)
                     └── build_kb_graph.py       (Neo4j KB_Graph)
                                              ↓
                     Serve (via Gateway):
                     ├── POST /api/ai/behavior/chat/           (RAG Chat on KB_Graph)
                     ├── GET  /api/ai/behavior/segment/<id>/   (User segment)
                     ├── GET  /api/ai/behavior/recommend/<id>/ (Behavior-based recs)
                     ├── GET  /api/ai/integration/search/      (Search + recs)
                     ├── GET  /api/ai/integration/cart/<id>/   (Cart recs)
                     └── GET  /api/ai/integration/chat-ui/     (Custom chat UI)
```

## Microservices

| Service | Port | Responsibility |
|---|---|---|
| **gateway** | 8080 | API Gateway, routing, CORS |
| **product-service** | 8001 | Product catalog, search, categories |
| **ai-service** | 8000 | Recommendations, similarity, RAG chat |

AI-service gọi product-service qua HTTP (`AI_PRODUCT_SERVICE_URL`, fallback `PRODUCT_SERVICE_URL`).

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
| RNN Classifier | 8 behavior counts | User segment (5 classes) | RNN, hidden=64, CrossEntropy |
| LSTM Classifier | 8 behavior counts | User segment (5 classes) | LSTM, hidden=64, CrossEntropy |
| BiLSTM Classifier | 8 behavior counts | User segment (5 classes) | BiLSTM, hidden=64, CrossEntropy |

## Project Structure

```
├── docker-compose.yml
├── data/
│   ├── amazon-products.csv         # 1000 real Amazon products
│   └── data_user500.csv            # 500 users × 8 behaviors (from Kaggle REES46)
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
│   │   ├── gnn.py                  # GNNEncoder + RecModel
│   │   └── behavior_models.py      # RNN, LSTM, BiLSTM classifiers
│   ├── services/
│   │   ├── product_client.py       # HTTP client → product-service
│   │   ├── graph.py                # Neo4j service
│   │   ├── embedding.py            # Self-trained TF-IDF + Autoencoder
│   │   ├── vector_store.py         # FAISS IndexFlatIP
│   │   ├── llm.py                  # Self-built response generator
│   │   └── behavior_rag.py         # RAG Chat on KB_Graph + RNN
│   ├── scripts/
│   │   ├── simulate_interactions.py
│   │   ├── train_embeddings.py
│   │   ├── export_graph.py
│   │   ├── train_gnn.py
│   │   ├── build_index.py
│   │   ├── prepare_user_data.py    # Download & preprocess Kaggle data
│   │   ├── train_behavior_models.py # Train RNN/LSTM/BiLSTM + plots
│   │   ├── build_kb_graph.py       # Build Neo4j KB_Graph
│   │   └── test_all.py             # 34 integration tests
│   ├── management/commands/
│   │   └── seed_products.py        # Sync products → Neo4j
│   └── api/
│       ├── views.py                # Product AI + Behavior endpoints
│       ├── integration_views.py    # Search/Cart recs + Chat UI
│       ├── serializers.py
│       └── urls.py
│
├── docs/
│   ├── aiservice02_report.md       # Full report (for PDF export)
│   └── plots/                      # Training curves, comparison, confusion matrices
│
├── config/                         # AI-service Django config
├── manage.py                       # AI-service manage.py
├── Dockerfile
└── requirements.txt
```

## Setup

Run all commands from project root (`danhgia04`).

### Option A - Docker (recommended)

```bash
# 1. Config
cp .env.example .env

# 2. Build + start all services
docker compose up -d --build

# One-time fix if you used old volumes and see "database ai_service does not exist"
docker compose exec db psql -U postgres -c "CREATE DATABASE ai_service;"

# 3. Migrate databases
docker compose exec product-service python manage.py migrate
docker compose exec ai-service python manage.py migrate

# 4. Seed products + sync to graph
docker compose exec product-service python manage.py seed_products
docker compose exec ai-service python manage.py seed_products

# 5. Simulate interactions
docker compose exec ai-service python ai_service/scripts/simulate_interactions.py --users 50 --actions 500

# 6. Train all models
docker compose exec ai-service python ai_service/scripts/train_embeddings.py
docker compose exec ai-service python ai_service/scripts/export_graph.py
docker compose exec ai-service python ai_service/scripts/train_gnn.py
docker compose exec ai-service python ai_service/scripts/build_index.py
```

Gateway API will be available at `http://localhost:8080`.

### Behavior Pipeline (AI Service 02)

Sau khi hệ thống đã chạy, thực hiện thêm các bước sau cho phần behavior classification:

```bash
# 1. Tạo data_user500.csv (từ Kaggle REES46 distribution)
python ai_service/scripts/prepare_user_data.py

# 2. Train RNN/LSTM/BiLSTM models
python ai_service/scripts/train_behavior_models.py

# 3. Build KB_Graph trong Neo4j
python ai_service/scripts/build_kb_graph.py

# 4. Restart ai-service để load endpoints mới
docker compose restart ai-service

# 5. Chạy test (34 tests)
python ai_service/scripts/test_all.py
```

Sau khi hoàn thành:
- Chat UI: http://localhost:8080/api/ai/integration/chat-ui/
- Neo4j Browser: http://localhost:7474

### Option B - Local run (without app containers)

If you run Django directly on host, use Python 3.11+ and install dependencies for both services:

```bash
python -m pip install -r requirements.txt
python -m pip install -r product_service/requirements.txt

# Start infra only
docker compose up -d db product-db neo4j redis

# Migrate (subshell keeps your cwd safe even if command fails)
(cd product_service && python manage.py migrate)
python manage.py migrate

# Seed + training
(cd product_service && python manage.py seed_products)
python manage.py seed_products
python ai_service/scripts/simulate_interactions.py --users 50 --actions 500
python ai_service/scripts/train_embeddings.py
python ai_service/scripts/export_graph.py
python ai_service/scripts/train_gnn.py
python ai_service/scripts/build_index.py
```

Run servers in 2 terminals:

```bash
# Terminal 1
cd product_service
python manage.py runserver 8001
```

```bash
# Terminal 2 (project root)
python manage.py runserver 8000
```

If you use Python 3.13 and get `ImproperlyConfigured: Error loading psycopg2 or psycopg module`, run:

```bash
python -m pip install "psycopg[binary]>=3.2,<3.3"
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

### User Behavior Data

500 users × 8 behaviors, dựa trên phân phối thống kê từ dataset REES46 (Kaggle):

- **Source:** https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop
- **Behaviors:** view, click, cart, purchase, search, wishlist, review, share
- **Segments:** high_value (90), browser (139), bargain_hunter (92), new_user (65), regular (114)
- **File:** `data/data_user500.csv`

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
| POST | `/api/ai/behavior/chat/` | ai-service → `/api/behavior/chat/` |
| GET | `/api/ai/behavior/segment/<id>/` | ai-service → `/api/behavior/segment/<id>/` |
| GET | `/api/ai/behavior/recommend/<id>/` | ai-service → `/api/behavior/recommend/<id>/` |
| GET | `/api/ai/integration/search/` | ai-service → `/api/integration/search/` |
| GET | `/api/ai/integration/cart/<id>/` | ai-service → `/api/integration/cart/<id>/` |
| GET | `/api/ai/integration/chat-ui/` | ai-service → `/api/integration/chat-ui/` |
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
| POST | `/api/behavior/chat/` | RAG Chat on KB_Graph (behavior) |
| GET | `/api/behavior/segment/<user_id>/` | User segment prediction (RNN) |
| GET | `/api/behavior/recommend/<user_id>/` | Behavior-based recommendations |
| GET | `/api/integration/search/?q=&user_id=` | Search + behavior recs |
| GET | `/api/integration/cart/<user_id>/` | Cart page recommendations |
| GET | `/api/integration/chat-ui/` | Custom chat UI (HTML) |

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
