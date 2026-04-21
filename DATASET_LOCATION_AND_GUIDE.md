# 📊 DATASET - VỊ TRÍ VÀ HƯỚNG DẪN SỬ DỤNG

## ✅ DATASET ĐÃ ĐƯỢC TẠO

### 📂 Vị Trí File

**Full Dataset (500 users, 4000 records)**
```
📁 d:/AI-SERVICE/danhgia04/data_user500_full.csv
```

**Sample Dataset (20 users, 20 records)**
```
📁 d:/AI-SERVICE/danhgia04/data_user500_sample.csv
```

---

## 📈 DATASET THỐNG KÊ

### Full Dataset (data_user500_full.csv)

| Thông Tin | Giá Trị |
|-----------|--------|
| **Tổng Records** | 4,000 |
| **Số Users** | 500 |
| **Số Products** | 978 |
| **Số Categories** | 10 |
| **Thời gian** | 2024-03-22 đến 2024-04-20 (30 ngày) |
| **Avg per user** | 8 interactions |

### Action Types Distribution

| Action | Count | % |
|--------|-------|---|
| view | 459 | 11.5% |
| click | 519 | 13.0% |
| add_to_cart | 531 | 13.3% |
| purchase | 519 | 13.0% |
| search | 465 | 11.6% |
| wishlist | 486 | 12.2% |
| share | 530 | 13.2% |
| review | 491 | 12.3% |

### Categories

```
• Automotive   (380 - 9.5%)
• Beauty       (360 - 9.0%)
• Books        (438 - 10.9%)
• Clothing     (417 - 10.4%)
• Electronics  (419 - 10.5%)
• Fashion      (401 - 10.0%)
• Garden       (380 - 9.5%)
• Home         (418 - 10.4%)
• Sports       (391 - 9.8%)
• Toys         (396 - 9.9%)
```

---

## 📋 CẤU TRÚC DỮ LIỆU

### Columns trong CSV

```
user_id        : Integer (1-500)
product_id     : Integer (1-978)
action         : String (view, click, add_to_cart, purchase, search, wishlist, share, review)
timestamp      : DateTime (YYYY-MM-DD HH:MM:SS)
behavior_score : Float (0.2-1.0)
category       : String (10 categories)
session_id     : String (sess_USER_DATE)
```

### Sample Records

```csv
user_id,product_id,action,timestamp,behavior_score,category,session_id
493,23,view,2024-03-22 00:11:00,0.2,Beauty,sess_493_20240322
456,443,click,2024-03-22 00:45:00,0.4,Fashion,sess_456_20240322
314,257,search,2024-03-22 01:15:00,0.3,Garden,sess_314_20240322
52,150,add_to_cart,2024-03-22 02:30:00,0.7,Electronics,sess_52_20240322
417,450,purchase,2024-03-22 03:45:00,1.0,Electronics,sess_417_20240322
```

---

## 🚀 CÁCH SỬ DỤNG DATASET

### 1️⃣ Cho YC2a (Training RNN/LSTM/BiLSTM)

**File**: `data_user500_full.csv`

**Cách dùng**:
```python
import pandas as pd

# Load dataset
df = pd.read_csv('data_user500_full.csv')

# Prepare sequences for LSTM training
user_sequences = df.groupby('user_id')['action'].apply(list)

# Convert actions to numeric
action_map = {
    'view': 0, 'click': 1, 'add_to_cart': 2,
    'purchase': 3, 'search': 4, 'wishlist': 5,
    'share': 6, 'review': 7
}

sequences = []
for seq in user_sequences:
    encoded_seq = [action_map[a] for a in seq]
    sequences.append(encoded_seq)

# Create training data (sliding windows)
for seq in sequences:
    for i in range(len(seq) - 10):
        X.append(seq[i:i+10])
        y.append(seq[i+10])
```

### 2️⃣ Cho YC2b (Neo4j Graph Population)

**File**: `data_user500_full.csv`

**Script sẽ dùng**:
```bash
python ai_service/scripts/simulate_interactions.py
# hoặc import trực tiếp từ CSV
```

### 3️⃣ Cho YC3 (Report - 20 Sample Rows)

**File**: `data_user500_sample.csv`

**Cách dùng**:
- Copy 20 dòng từ file
- Paste vào báo cáo

---

## 📥 DOWNLOAD/COPY DATASET

### Option 1: Dùng Full Dataset
```
1. Mở: d:/AI-SERVICE/danhgia04/data_user500_full.csv
2. Select all (Ctrl+A)
3. Copy và sử dụng
```

### Option 2: Dùng Sample Dataset
```
1. Mở: d:/AI-SERVICE/danhgia04/data_user500_sample.csv
2. Select 20 rows + header
3. Copy vào báo cáo
```

### Option 3: Tạo lại Dataset (Nếu cần)
```bash
cd d:/AI-SERVICE/danhgia04
python generate_dataset.py

# Output: data_user500_full.csv (tạo mới)
```

---

## 🔧 SỬ DỤNG VỚI PROJECT

### Integrate vào Django Models

**File**: `ai_service/scripts/simulate_interactions.py`

```python
import pandas as pd
from ai_service.models.django_models import Interaction

# Load data
df = pd.read_csv('../data_user500_full.csv')

# Bulk insert
for _, row in df.iterrows():
    Interaction.objects.create(
        user_id=row['user_id'],
        product_id=row['product_id'],
        event_type=row['action'],
        query='' if row['action'] != 'search' else 'search_query',
        timestamp=row['timestamp']
    )
```

### Integrate vào Neo4j

**File**: `ai_service/services/graph.py`

```python
import pandas as pd
from ai_service.services.graph import graph_service

df = pd.read_csv('../data_user500_full.csv')

# Log interactions to Neo4j
for _, row in df.iterrows():
    if row['action'] != 'search':
        graph_service.log_interaction(
            user_id=row['user_id'],
            product_id=row['product_id'],
            event_type=row['action']
        )
    else:
        graph_service.log_search(row['user_id'], 'search_query')
```

---

## 📊 VISUALIZE DATASET (Optional)

### Generate Basic Stats
```bash
cd d:/AI-SERVICE/danhgia04

python << EOF
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data_user500_full.csv')

# Action distribution
df['action'].value_counts().plot(kind='bar')
plt.title('Action Distribution')
plt.savefig('action_distribution.png')

# Category distribution
df['category'].value_counts().plot(kind='bar')
plt.title('Category Distribution')
plt.savefig('category_distribution.png')

# User activity
df.groupby('user_id').size().hist(bins=20)
plt.title('User Activity Distribution')
plt.savefig('user_activity.png')

print("✓ Visualizations saved!")
EOF
```

---

## ✅ CHECKLIST

- [x] **data_user500_full.csv** - 500 users, 4000 records (MAIN DATASET)
- [x] **data_user500_sample.csv** - 20 sample rows (FOR REPORT)
- [x] **generate_dataset.py** - Script để tạo dataset lại (CUSTOM)
- [x] **ai_service/scripts/simulate_interactions.py** - Load dataset vào system

---

## 📝 FILE SUMMARY

| File | Location | Size | Purpose |
|------|----------|------|---------|
| data_user500_full.csv | `d:/AI-SERVICE/danhgia04/` | ~500KB | Full dataset |
| data_user500_sample.csv | `d:/AI-SERVICE/danhgia04/` | ~2KB | Sample (20 rows) |
| generate_dataset.py | `d:/AI-SERVICE/danhgia04/` | Python script | Generate dataset |

---

**Dataset Status**: ✅ **READY TO USE**

Bạn có thể:
1. **Copy 20 dòng** từ `data_user500_sample.csv` → Paste vào báo cáo
2. **Dùng full dataset** `data_user500_full.csv` → Cho training models
3. **Tạo lại dataset** → Chạy `python generate_dataset.py`
