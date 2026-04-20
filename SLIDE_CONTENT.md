# TÀI LIỆU SLIDE — HỆ THỐNG AI-SERVICE CHO E-COMMERCE

> Nội dung dưới đây được chia theo từng slide. Bạn copy nội dung vào PowerPoint/Google Slides, mỗi phần "---" là 1 slide.

---

## SLIDE 1: TRANG BÌA

**HỆ THỐNG GỢI Ý SẢN PHẨM THÔNG MINH CHO E-COMMERCE**

Ứng dụng Knowledge Graph + GNN + RAG Chat

Công nghệ: Django · Neo4j · PyTorch · FAISS

---

## SLIDE 2: MỤC LỤC

1. Giới thiệu & Bài toán
2. Kiến trúc tổng quan (Microservices)
3. Product Service
4. AI Service — Tổng quan
5. Knowledge Graph (Neo4j)
6. Mô hình tự huấn luyện — Text Embedding
7. Mô hình tự huấn luyện — GNN (GraphSAGE)
8. Embedding Fusion & FAISS Vector Search
9. GraphRAG Chat (Tự xây dựng)
10. Training Pipeline
11. API Endpoints
12. Docker & Triển khai
13. Dữ liệu & Mô phỏng
14. Tổng kết

---

## SLIDE 3: GIỚI THIỆU & BÀI TOÁN

**Bài toán:** Xây dựng hệ thống AI hỗ trợ khách hàng e-commerce dựa trên hành vi người dùng

**Các chức năng chính:**
- Gợi ý sản phẩm cá nhân hóa (Recommendation)
- Tìm sản phẩm tương tự (Similarity Search)
- Chat hỏi đáp thông minh (GraphRAG Chat)

**Nguyên tắc thiết kế:**
- ✅ Toàn bộ model tự huấn luyện (self-trained)
- ✅ Không dùng OpenAI, SentenceTransformer, hay bất kỳ pretrained model nào
- ✅ Kiến trúc Microservice, giao tiếp qua HTTP

---

## SLIDE 4: KIẾN TRÚC TỔNG QUAN

```
┌─────────────────────┐          HTTP          ┌──────────────────────────────┐
│   Product Service   │◄───────────────────────│        AI Service            │
│     (Port 8001)     │                        │       (Port 8000)            │
│                     │                        │                              │
│  PostgreSQL         │                        │  PostgreSQL + Neo4j + Redis  │
│  Product Catalog    │                        │  Recommendations             │
│  Search             │                        │  Similarity                  │
│                     │                        │  RAG Chat                    │
└─────────────────────┘                        └──────────────────────────────┘
```

**6 Docker containers:**

| Container | Công nghệ | Port |
|---|---|---|
| db | PostgreSQL 16 (AI Service) | 5432 |
| product-db | PostgreSQL 16 (Product Service) | 5433 |
| neo4j | Neo4j 5 (Knowledge Graph) | 7474, 7687 |
| redis | Redis 7 (Cache) | 6379 |
| product-service | Django + Gunicorn | 8001 |
| ai-service | Django + Gunicorn | 8000 |

---

## SLIDE 5: PRODUCT SERVICE

**Vai trò:** Quản lý danh mục sản phẩm, cung cấp API cho AI Service

**Models:**

| Model | Trường chính |
|---|---|
| Category | name (unique) |
| Product | name, description, price, category (FK), brand, image_url, rating, rating_count |

**API Endpoints (Port 8001):**

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | /api/products/ | Danh sách sản phẩm (filter category/brand, phân trang) |
| GET | /api/products/{id}/ | Chi tiết sản phẩm |
| GET | /api/products/search/?q= | Tìm kiếm theo từ khóa |

**Dữ liệu:** 1000 sản phẩm thực từ Amazon (Bright Data dataset), 15+ danh mục

---

## SLIDE 6: AI SERVICE — TỔNG QUAN

**Vai trò:** Xử lý AI — gợi ý, tìm tương tự, chat thông minh

**Thành phần chính:**

| Module | Chức năng |
|---|---|
| `models/django_models.py` | Lưu Interaction (view, click, cart, purchase, search) |
| `models/gnn.py` | GNN Encoder (GraphSAGE) + RecModel (BPR loss) |
| `services/graph.py` | Quản lý Knowledge Graph trên Neo4j |
| `services/embedding.py` | Text Embedding (TF-IDF + Autoencoder) |
| `services/vector_store.py` | FAISS Vector Search |
| `services/llm.py` | Response Generator (Intent + Template) |
| `services/product_client.py` | HTTP Client gọi Product Service |

**API Endpoints (Port 8000):**

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | /api/track/ | Ghi nhận hành vi → PostgreSQL + Neo4j |
| GET | /api/recommend/{user_id}/ | Gợi ý sản phẩm (Collaborative Filtering trên Graph) |
| GET | /api/similar/{product_id}/ | Sản phẩm tương tự (FAISS) |
| POST | /api/chat/ | Chat GraphRAG |

---

## SLIDE 7: KNOWLEDGE GRAPH (Neo4j)

**Các loại Node:**

| Node | Thuộc tính |
|---|---|
| User | id |
| Product | id, name, description, price |
| Category | id, name |
| Query | text |

**Các loại Edge (Quan hệ):**

| Edge | Từ → Đến | Thuộc tính |
|---|---|---|
| INTERACTED | User → Product | weight, types[] |
| SEARCHED | User → Query | — |
| BELONGS_TO | Product → Category | — |
| SIMILAR | Product ↔ Product | score |

**Công thức trọng số cạnh:**

```
w(user, product) = 1 × clicks + 3 × cart + 5 × purchases
```

**Ứng dụng:**
- Collaborative Filtering: Tìm user tương tự → gợi ý sản phẩm
- Cung cấp context cho RAG Chat
- Lưu trữ quan hệ SIMILAR từ FAISS

---

## SLIDE 8: MÔ HÌNH TỰ HUẤN LUYỆN — TEXT EMBEDDING

**Pipeline:**

```
Product Text → TF-IDF (5000 features, bigrams) → Autoencoder → Dense Vector (128 chiều)
```

**Chi tiết TF-IDF:**
- max_features = 5000
- ngram_range = (1, 2) — unigram + bigram
- sublinear_tf = True

**Chi tiết Autoencoder:**

```
Encoder: Linear(5000 → 256) → ReLU → Linear(256 → 128)
Decoder: Linear(128 → 256) → ReLU → Linear(256 → 5000)
```

- Loss: MSE (Mean Squared Error)
- Optimizer: Adam, lr = 0.001
- Epochs: 100
- Đầu ra: Vector 128 chiều, L2 normalized

**Fallback:** Trước khi train, dùng hash-based embedding (deterministic)

---

## SLIDE 9: MÔ HÌNH TỰ HUẤN LUYỆN — GNN (GraphSAGE)

**Kiến trúc:**

```
Bipartite Graph (User ↔ Product)
    ↓
GNN Encoder: 2-layer GraphSAGE (dim = 128)
    ↓
User Embeddings (128d) + Product Embeddings (128d)
```

**Chi tiết RecModel:**
- User Embedding: nn.Embedding(num_users, 128)
- Product Embedding: nn.Embedding(num_products, 128)
- Encoder: SAGEConv → ReLU → SAGEConv (2 layers)
- Bidirectional edges (user↔product)

**Huấn luyện:**
- Loss: BPR (Bayesian Personalized Ranking)
- Negative Sampling: Random negative products
- Optimizer: Adam, lr = 0.003
- Epochs: 50

**Công thức BPR Loss:**

```
L = -mean(log σ(score_pos - score_neg))
```

Trong đó: score = dot_product(user_emb, product_emb)

---

## SLIDE 10: EMBEDDING FUSION & FAISS VECTOR SEARCH

**Kết hợp 2 loại embedding:**

```
Text Embedding (128d) + GNN Embedding (128d)
    ↓ Concatenate
Fused Vector (256d)
    ↓ L2 Normalize
    ↓ FAISS IndexFlatIP (Inner Product ≈ Cosine Similarity)
```

**FAISS Vector Store:**
- Index type: IndexFlatIP (Inner Product trên normalized vectors = Cosine Similarity)
- Hỗ trợ: search top-K sản phẩm tương tự
- Kết quả SIMILAR được ghi ngược lại Neo4j (SIMILAR edges)

**Quy trình tìm sản phẩm tương tự:**

```
Product ID → Lấy text từ Product Service
           → Embed text (TF-IDF + Autoencoder)
           → Merge với GNN embedding (nếu có)
           → FAISS search top-K
           → Trả về danh sách sản phẩm tương tự
```

---

## SLIDE 11: GraphRAG CHAT (TỰ XÂY DỰNG)

**Không dùng LLM bên ngoài — Tự xây dựng hoàn toàn**

**Pipeline xử lý câu hỏi:**

```
User Query
    ↓
1. Intent Detection (6 intents: recommend, cheap, compare, similar, best, info)
    ↓
2. Graph Context: Lấy lịch sử tương tác từ Neo4j
    ↓
3. Vector Context: Embed query → FAISS search → top-5 sản phẩm
    ↓
4. Lấy thông tin sản phẩm từ Product Service (HTTP)
    ↓
5. Template Matching: Chọn template theo intent → Điền dữ liệu
    ↓
Response (tiếng Việt)
```

**6 Intent được hỗ trợ:**

| Intent | Từ khóa nhận diện |
|---|---|
| recommend | recommend, suggest, gợi ý, đề xuất, nên mua, tư vấn |
| cheap | cheap, rẻ, giá rẻ, budget, tiết kiệm |
| compare | compare, so sánh, khác nhau, vs |
| similar | similar, tương tự, giống, alternative |
| best | best, tốt nhất, top, popular, phổ biến |
| info | info, thông tin, chi tiết, detail, là gì |

---

## SLIDE 12: TRAINING PIPELINE

**Quy trình huấn luyện 7 bước:**

```
Bước 1: Seed sản phẩm từ CSV → Product DB (product-service)
    ↓
Bước 2: Sync sản phẩm → Neo4j (ai-service)
    ↓
Bước 3: Mô phỏng hành vi người dùng → PostgreSQL + Neo4j
         (50 users, 500 actions, conversion funnel)
    ↓
Bước 4: Train Text Embedding (TF-IDF + Autoencoder, 100 epochs)
    ↓
Bước 5: Export graph từ Neo4j → JSON
    ↓
Bước 6: Train GNN (GraphSAGE + BPR, 50 epochs)
    ↓
Bước 7: Build FAISS Index + Ghi SIMILAR edges vào Neo4j
```

**Conversion Funnel (Mô phỏng):**

| Hành vi | Xác suất |
|---|---|
| view | 100% |
| click | 50% |
| cart | 20% |
| purchase | 8% |

---

## SLIDE 13: LUỒNG DỮ LIỆU TỔNG THỂ

```
[Người dùng] ──── Hành vi (view/click/cart/purchase/search) ────→ POST /api/track/
                                                                       │
                                                          ┌────────────┼────────────┐
                                                          ↓                         ↓
                                                    PostgreSQL                   Neo4j
                                                   (Interaction)          (User-Product Graph)
                                                                                    │
                                                                          ┌─────────┴─────────┐
                                                                          ↓                   ↓
                                                                   Training Pipeline    Collaborative
                                                                   (Embedding + GNN)    Filtering
                                                                          ↓                   ↓
                                                                    FAISS Index        GET /recommend/
                                                                          ↓
                                                                   GET /similar/
                                                                   POST /chat/
```

---

## SLIDE 14: TECH STACK

| Tầng | Công nghệ | Vai trò |
|---|---|---|
| API Framework | Django 5.1 + DRF 3.15 | REST API cho cả 2 service |
| Graph Database | Neo4j 5 (Cypher) | Knowledge Graph |
| Vector Database | FAISS (faiss-cpu) | Tìm kiếm tương tự |
| GNN Framework | PyTorch 2.3 + PyG 2.5 | Huấn luyện GraphSAGE |
| Text Processing | scikit-learn (TF-IDF) | Trích xuất đặc trưng văn bản |
| Relational DB | PostgreSQL 16 | Lưu trữ sản phẩm, tương tác |
| Cache | Redis 7 | Caching |
| Container | Docker Compose | Triển khai microservices |
| Web Server | Gunicorn 22 | Production WSGI server |
| Language | Python 3.11 | Ngôn ngữ chính |

---

## SLIDE 15: DỮ LIỆU

**Nguồn dữ liệu:** 1000 sản phẩm thực từ Amazon (Bright Data dataset)

**Phân bố theo danh mục:**

| Danh mục | Số sản phẩm |
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
| + 6 danh mục khác | ~214 |

**Thông tin mỗi sản phẩm:** title, description, price, brand, image_url, rating, reviews_count, categories

---

## SLIDE 16: DOCKER & TRIỂN KHAI

**Khởi chạy hệ thống:**

```bash
# 1. Cấu hình
cp .env.example .env

# 2. Khởi động tất cả services
docker-compose up -d

# 3. Migrate databases
docker-compose exec product-service python manage.py migrate
docker-compose exec ai-service python manage.py migrate

# 4. Seed dữ liệu
docker-compose exec product-service python manage.py seed_products
docker-compose exec ai-service python manage.py seed_products

# 5. Mô phỏng & Huấn luyện
docker-compose exec ai-service python ai_service/scripts/simulate_interactions.py
docker-compose exec ai-service python ai_service/scripts/train_embeddings.py
docker-compose exec ai-service python ai_service/scripts/export_graph.py
docker-compose exec ai-service python ai_service/scripts/train_gnn.py
docker-compose exec ai-service python ai_service/scripts/build_index.py
```

---

## SLIDE 17: TỔNG KẾT

**Điểm nổi bật của hệ thống:**

✅ **Self-trained hoàn toàn** — Không phụ thuộc API hay pretrained model bên ngoài

✅ **Kiến trúc Microservice** — Product Service + AI Service tách biệt, giao tiếp HTTP

✅ **Knowledge Graph** — Neo4j lưu trữ quan hệ User-Product-Category, hỗ trợ Collaborative Filtering

✅ **GNN (GraphSAGE + BPR)** — Học embedding từ đồ thị tương tác, cá nhân hóa gợi ý

✅ **Embedding Fusion** — Kết hợp Text (TF-IDF+Autoencoder) + GNN → Vector 256 chiều

✅ **FAISS Vector Search** — Tìm kiếm sản phẩm tương tự nhanh chóng

✅ **GraphRAG Chat** — Tự xây dựng chatbot không cần LLM, dùng Intent Detection + Template + Graph/Vector context

✅ **Docker Compose** — Triển khai đầy đủ 6 containers, sẵn sàng production

---

## SLIDE 18: CẢM ƠN

**Cảm ơn thầy/cô và các bạn đã lắng nghe!**

Câu hỏi?

---

## PHỤ LỤC: SƠ ĐỒ KIẾN TRÚC CHI TIẾT (Slide bổ sung nếu cần)

```
                    ┌──────────────┐
                    │   Người dùng │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         POST /track   GET /recommend  POST /chat
              │            │            │
              ↓            ↓            ↓
    ┌─────────────────────────────────────────────┐
    │              AI SERVICE (8000)               │
    │                                              │
    │  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
    │  │ graph.py │  │embedding │  │vector_store│  │
    │  │ (Neo4j)  │  │ (TF-IDF+ │  │  (FAISS)  │  │
    │  │          │  │Autoencoder│  │           │  │
    │  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
    │       │              │              │        │
    │  ┌────┴─────┐  ┌────┴─────┐  ┌─────┴─────┐  │
    │  │  gnn.py  │  │  llm.py  │  │product_   │  │
    │  │(GraphSAGE│  │(Intent+  │  │client.py  │  │
    │  │ +BPR)    │  │Template) │  │  (HTTP)   │  │
    │  └──────────┘  └──────────┘  └─────┬─────┘  │
    └────────────────────────────────────┬┘        │
                                         │         │
                                         ↓         │
                              ┌──────────────────┐ │
                              │ PRODUCT SERVICE  │ │
                              │    (8001)        │ │
                              │  PostgreSQL      │ │
                              └──────────────────┘ │
    ┌──────────────────────────────────────────────┘
    │
    ↓
┌───────┐  ┌───────┐  ┌───────┐
│Neo4j  │  │Postgres│  │ Redis │
│(Graph)│  │ (Data) │  │(Cache)│
└───────┘  └────────┘  └───────┘
```
