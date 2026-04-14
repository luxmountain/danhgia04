# AI-Service for E-Commerce

AI layer cho hệ thống e-commerce microservice Django — hỗ trợ khách hàng dựa trên hành vi (view, click, cart, purchase, search) với Knowledge Graph + GNN + RAG Chat.

**Toàn bộ model tự train, không dùng external API hay pretrained model.**

## Architecture

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
├── manage.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── DESIGN.md
├── TASKS.md
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── ai_service/
    ├── models/
    │   ├── django_models.py        # Category, Product, Interaction
    │   └── gnn.py                  # GNNEncoder (GraphSAGE) + RecModel (BPR)
    ├── services/
    │   ├── graph.py                # Neo4j service
    │   ├── embedding.py            # Self-trained TF-IDF + Autoencoder
    │   ├── vector_store.py         # FAISS IndexFlatIP
    │   └── llm.py                  # Self-built response generator
    ├── scripts/
    │   ├── simulate_interactions.py # Data collection (user behavior)
    │   ├── train_embeddings.py     # Train text encoder
    │   ├── export_graph.py         # Neo4j → JSON
    │   ├── train_gnn.py            # Train GNN → embeddings
    │   └── build_index.py          # Build FAISS index + SIMILAR edges
    ├── management/
    │   └── commands/
    │       └── seed_products.py    # Seed 1000 products from Amazon dataset
    └── api/
        ├── serializers.py
        ├── views.py                # 7 endpoints
        └── urls.py
```

## Setup

```bash
# 1. Config
cp .env.example .env

# 2. Start infrastructure
docker-compose up -d

# 3. Migrate & seed
python manage.py migrate
python manage.py seed_products --sync-neo4j

# 4. Collect data (simulate user interactions)
python ai_service/scripts/simulate_interactions.py --users 50 --actions 500

# 5. Train all models
python ai_service/scripts/train_embeddings.py     # Text encoder
python ai_service/scripts/export_graph.py          # Export graph
python ai_service/scripts/train_gnn.py             # GNN model
python ai_service/scripts/build_index.py           # FAISS index

# 6. Run server
python manage.py runserver
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

### Product Service

#### GET `/api/products/`
List products with filtering and pagination.

```
GET /api/products/?category=Electronics&brand=Sony&page=1&size=10
```

Response:
```json
{
  "total": 4,
  "page": 1,
  "size": 10,
  "results": [
    {
      "id": 4,
      "name": "Sony WH-1000XM5 Noise Cancelling Headphones",
      "price": "26990.00",
      "brand": "Sony",
      "image_url": "https://m.media-amazon.com/images/I/51aXvjzcukL._SL1500_.jpg",
      "rating": 4.5,
      "rating_count": 12890,
      "category_name": "Electronics"
    }
  ]
}
```

#### GET `/api/products/<id>/`
Get product detail.

#### GET `/api/products/search/?q=<keyword>`
Search products by name, description, or brand.

```
GET /api/products/search/?q=headphones&limit=5
```

### AI Service

#### POST `/api/track/`
Log user interaction → PostgreSQL + Neo4j.

```json
{"user_id": 1, "product_id": 42, "event_type": "view"}
```
Event types: `view`, `click`, `cart`, `purchase`, `search`

#### GET `/api/recommend/<user_id>/`
Collaborative filtering recommendations từ Neo4j graph.

#### GET `/api/similar/<product_id>/`
Tìm sản phẩm tương tự qua FAISS (self-trained embeddings).

#### POST `/api/chat/`
GraphRAG chat — self-built response generator (no external API).

```json
{"user_id": 1, "query": "Tôi muốn mua điện thoại giá rẻ"}
```

Response:
```json
{
  "answer": "Các sản phẩm giá tốt phù hợp với bạn:\n  1. Samsung Galaxy M14 5G (Samsung) — ₹13490, ⭐ 4.2\n  ...",
  "sources": {
    "graph_context": [...],
    "vector_results": [...]
  }
}
```

## Training Pipeline

```bash
# Full pipeline (chạy lại khi có data mới)
python ai_service/scripts/train_embeddings.py     # TF-IDF + Autoencoder
python ai_service/scripts/export_graph.py          # Neo4j → JSON
python ai_service/scripts/train_gnn.py             # GraphSAGE + BPR loss
python ai_service/scripts/build_index.py           # FAISS index + SIMILAR edges
```

## Key Design Decisions

- **Self-trained only**: Không dùng OpenAI, SentenceTransformer, hay bất kỳ pretrained model nào
- **Text Embedding**: TF-IDF (5000 features, bigrams) → Autoencoder (128d) — train trên product data
- **GNN**: GraphSAGE 2-layer + BPR loss — train trên user-product interaction graph
- **Response Generator**: Intent detection (6 intents) + template matching + graph/vector context
- **Data Collection**: Simulate realistic user behavior (conversion funnel) + seed từ Kaggle
- **Edge weight**: `w(u,p) = 1·clicks + 3·cart + 5·purchases`
- **Embedding fusion**: Text (128d) + GNN (128d) → concat (256d) → normalize → FAISS
