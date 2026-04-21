# 📍 HƯỚNG DẪN CHI TIẾT: VỊ TRÍ FILE VÀ CHỖ CHÈN ẢNH

## YÊU CẦU 2: MÔ TẢ AI-SERVICE

### File chính
📄 **Location**: `d:/AI-SERVICE/danhgia04/REPORT_2_AISERVICE_DESCRIPTION.md`

### Chỗ chèn ảnh
**Section: 2.3 API Endpoints**
- Sau phần "### API Endpoints"
- Trước phần "### Request/Response Examples"
- **Copy ảnh**: `VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png` (hình các component)

**Cấu trúc:**
```markdown
## 2.3 API Endpoints

[TABLE các endpoints]

📊 **System Architecture Diagram** ← PASTE ẢNH VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png

### Request/Response Examples
```

---

## YÊU CẦU 3: COPY 20 DÒNG DATA

### File chính
📊 **Location**: `d:/AI-SERVICE/danhgia04/data_user500_sample.csv`

### Chỗ chèn ảnh
**File này là dữ liệu CSV, KHÔNG CHÈN ẢNH**
- File này dùng để bạn copy dữ liệu trực tiếp
- Open file bằng Excel hoặc text editor
- Chọn 20 dòng đầu (+ header)
- Paste vào báo cáo của bạn

**Nếu muốn hình ảnh biểu diễn data:**
- **Copy ảnh**: `VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png` (bar chart & pie chart của 20 dòng)
- Paste vào báo cáo để minh họa dữ liệu

---

## YÊU CẦU 4: YC 2a - RNN/LSTM/BiLSTM

### File chính
📄 **Location**: `d:/AI-SERVICE/danhgia04/REPORT_2A_LSTM_MODELS.md`

### Chỗ chèn ảnh - 1

**Section: 3.4 Comparison & Results**
- Sau phần "## 3.4 Comparison & Results"
- Sau bảng comparison
- Trước phần "## 3.5 Model Selection"

```markdown
## 3.4 Comparison & Results

| Model | Accuracy | Precision | ... |
|-------|----------|-----------|-----|
| ... |

📊 **Model Performance Visualization** ← PASTE ẢNH VISUALIZATIONS_4_MODEL_COMPARISON.png

## 3.5 Model Selection
```

---

## YÊU CẦU 5: YC 2b - KNOWLEDGE GRAPH

### File chính
📄 **Location**: `d:/AI-SERVICE/danhgia04/REPORT_2B_KNOWLEDGE_GRAPH.md`

### Chỗ chèn ảnh - 1: Graph visualization

**Section: 4.5 Data Sample (20 rows)**
- Sau phần dữ liệu 20 dòng
- Sau bảng "User-Product Interactions Graph"
- Trước phần "## 4.6 Graph Visualization"

```markdown
## 4.5 Data Sample (20 rows)

[DỮ LIỆU CSV 20 ROWS]

### User-Product Interactions Graph

| User_ID | Product_ID | ... |
|---------|------------|-----|

📊 **Knowledge Graph Structure** ← PASTE ẢNH VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png

## 4.6 Graph Visualization
```

### Chỗ chèn ảnh - 2: Node & Edge Distribution

**Section: 4.6 Graph Visualization**
- Sau phần "### Degree Distribution"
- Trước phần "## 4.7 Optimization Strategies"

```markdown
### Degree Distribution

[TEXT mô tả distribution]

📊 **Graph Statistics & Degree Distribution Visualization** ← PASTE ẢNH VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png (same or alternative)

## 4.7 Optimization Strategies
```

---

## YÊU CẦU 6: YC 2c & 2d - RAG CHAT & INTEGRATION

### File chính
📄 **Location**: `d:/AI-SERVICE/danhgia04/REPORT_2C_2D_RAG_CHAT_INTEGRATION.md`

### Chỗ chèn ảnh - 1: RAG Pipeline

**Section: 5.1 RAG Architecture**
- Sau phần mô tả pipeline text
- Trước phần "## 5.2 Component Breakdown"

```markdown
## 5.1 RAG Architecture

[TEXT mô tả RAG]

User Query
    ↓
1. Intent Detection
    ↓
...

📊 **RAG Pipeline Flow Diagram** ← PASTE ẢNH VISUALIZATIONS_5_RAG_PIPELINE.png

## 5.2 Component Breakdown
```

### Chỗ chèn ảnh - 2: Intent Detection

**Section: 5.2 Component Breakdown - A. Intent Detection**
- Sau phần "Code:"
- Sau function `_detect_intent`
- Trước phần "### B. Text Embedding Pipeline"

```markdown
### A. Intent Detection

[TEXT & CODE]

def _detect_intent(query: str) -> str:
    ...

📊 **6 Intent Types Distribution** ← PASTE ẢNH VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png (hoặc tạo intent chart mới)

### B. Text Embedding Pipeline
```

### Chỗ chèn ảnh - 3: System Architecture

**Section: 6.1 Complete Integration**
- Sau phần "### Architecture Diagram"
- Trước phần "### All Endpoints"

```markdown
## 5.4 Complete Integration (2d)

### Architecture Diagram

[TEXT mô tả architecture]

┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
│              POST /api/track/ or /api/chat/                 │
└─────────────────────────────────────────────────────────────┘

📊 **Complete System Architecture** ← PASTE ẢNH VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png

### All Endpoints
```

### Chỗ chèn ảnh - 4: Data Flow Example

**Section: 5.5 Data Flow Example**
- Sau phần "**Scenario**: User queries..."
- Sau các bước 1-7
- Trước phần "## 5.6 Training Pipeline Integration"

```markdown
## 5.5 Data Flow Example

**Scenario**: User queries "Gợi ý sản phẩm rẻ"

1. REQUEST ARRIVES
   ...
   
7. RESPONSE RETURNED
   ...

📊 **Chat Flow Visualization** ← PASTE ẢNH VISUALIZATIONS_5_RAG_PIPELINE.png

## 5.6 Training Pipeline Integration
```

---

## 📌 BẢNG TÓMLƯỢC: ẢNH CẦN CHÈN VÀO ĐÂU

| Yêu Cầu | File | Section | Ảnh | Vị Trí |
|---------|------|---------|-----|--------|
| **2** | REPORT_2_AISERVICE_DESCRIPTION.md | 2.3 API Endpoints | VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png | Sau bảng endpoints |
| **3** | data_user500_sample.csv | - | VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png | Copy dữ liệu + optional ảnh |
| **4** | REPORT_2A_LSTM_MODELS.md | 3.4 Comparison | VISUALIZATIONS_4_MODEL_COMPARISON.png | Sau bảng comparison |
| **5a** | REPORT_2B_KNOWLEDGE_GRAPH.md | 4.5 Data Sample | VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png | Sau dữ liệu 20 rows |
| **5b** | REPORT_2B_KNOWLEDGE_GRAPH.md | 4.6 Visualization | VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png | Phần graph distribution |
| **6a** | REPORT_2C_2D_RAG_CHAT_INTEGRATION.md | 5.1 RAG Architecture | VISUALIZATIONS_5_RAG_PIPELINE.png | Sau mô tả RAG flow |
| **6b** | REPORT_2C_2D_RAG_CHAT_INTEGRATION.md | 5.2 A. Intent Detection | VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png | Sau code intent |
| **6c** | REPORT_2C_2D_RAG_CHAT_INTEGRATION.md | 5.4 Architecture | VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png | Sau text architecture |
| **6d** | REPORT_2C_2D_RAG_CHAT_INTEGRATION.md | 5.5 Data Flow | VISUALIZATIONS_5_RAG_PIPELINE.png | Sau bước 7 response |

---

## 🎯 QUICK REFERENCE: CHỈNH SỬA TỪng FILE

### REPORT_2_AISERVICE_DESCRIPTION.md
```
Tìm chỗ: "### Request/Response Examples:"
Chèn TRƯỚC: VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png
```

### REPORT_2A_LSTM_MODELS.md
```
Tìm chỗ: "## 3.5 Model Selection"
Chèn TRƯỚC: VISUALIZATIONS_4_MODEL_COMPARISON.png
```

### REPORT_2B_KNOWLEDGE_GRAPH.md
```
Tìm chỗ: "## 4.6 Graph Visualization"
Chèn TRƯỚC: VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png

Tìm chỗ: "## 4.7 Optimization Strategies"
Chèn TRƯỚC: VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png (lần 2)
```

### REPORT_2C_2D_RAG_CHAT_INTEGRATION.md
```
Tìm chỗ 1: "## 5.2 Component Breakdown"
Chèn TRƯỚC: VISUALIZATIONS_5_RAG_PIPELINE.png

Tìm chỗ 2: "### B. Text Embedding Pipeline"
Chèn TRƯỚC: VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png

Tìm chỗ 3: "### All Endpoints"
Chèn TRƯỚC: VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png

Tìm chỗ 4: "## 5.6 Training Pipeline Integration"
Chèn TRƯỚC: VISUALIZATIONS_5_RAG_PIPELINE.png (lần 2)
```

---

## 📸 CÁC BƯỚC THỰC HIỆN

### Bước 1: Copy dữ liệu
1. Mở file: `d:/AI-SERVICE/danhgia04/data_user500_sample.csv`
2. Select 20 dòng đầu (kể cả header)
3. Copy vào báo cáo YÊU CẦU 3

### Bước 2: Mở các ảnh
```
Các file ảnh trong: d:/AI-SERVICE/danhgia04/
- VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png
- VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png
- VISUALIZATIONS_4_MODEL_COMPARISON.png
- VISUALIZATIONS_5_RAG_PIPELINE.png
- VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png
```

### Bước 3: Copy ảnh vào file theo bảng trên
1. Mở file markdown (REPORT_2_*.md)
2. Tìm vị trí cần chèn (theo Quick Reference)
3. Paste ảnh vào

### Bước 4: Copy code từ ai_service/
```
Code files:
- ai_service/models/gnn.py              ← BiLSTM code
- ai_service/services/graph.py          ← Neo4j code
- ai_service/services/llm.py            ← Intent detection
- ai_service/api/views.py               ← API endpoints

Copy relevant sections vào báo cáo
```

---

**Tóm tắt**: 
- 5 file markdown đã có
- 5 ảnh PNG cần chèn
- Mỗi ảnh có vị trí cụ thể trong file
- Copy dữ liệu từ CSV file
- Copy code từ ai_service folder
