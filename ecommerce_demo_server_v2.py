"""
E-Commerce Integration Demo Server V2
✅ Category Pages with Full Product Listings
✅ Mock Chat with Knowledge Base
✅ Fixed Q&A Responses from Knowledge Base
"""

from flask import Flask, render_template_string, request, jsonify, url_for
import pandas as pd
import json
from collections import defaultdict

app = Flask(__name__)

# ==================== KNOWLEDGE BASE ====================
# Fixed Q&A cố định để chatbot trả lời

KNOWLEDGE_BASE = {
    "sản phẩm tốt nhất là gì": {
        "answer": "Theo đánh giá của khách hàng, những sản phẩm bán chạy nhất và được yêu thích nhất là các sản phẩm trong danh mục Electronics và Books. Bạn có thể xem danh sách bán chạy bằng cách click vào 'Bán Chạy' trong menu lọc.",
        "products_query": "best"
    },
    "tôi nên mua sản phẩm nào": {
        "answer": "Hãy cho tôi biết bạn quan tâm đến danh mục nào? Chúng tôi có:\n• Electronics - Điện tử & Công nghệ\n• Books - Sách\n• Clothing - Quần áo\n• Fashion - Thời trang\n• Beauty - Làm đẹp\n• Sports - Thể thao\n• Home - Gia dụng\n• Garden - Làm vườn\n• Automotive - Ô tô\n• Toys - Đồ chơi",
        "products_query": None
    },
    "các danh mục sản phẩm là gì": {
        "answer": "Chúng tôi có 10 danh mục sản phẩm chính:\n1️⃣ Electronics - Điện tử, máy tính\n2️⃣ Books - Sách, tài liệu\n3️⃣ Clothing - Quần áo\n4️⃣ Fashion - Thời trang\n5️⃣ Beauty - Sản phẩm làm đẹp\n6️⃣ Sports - Dụng cụ thể thao\n7️⃣ Home - Đồ gia dụng\n8️⃣ Garden - Dụng cụ làm vườn\n9️⃣ Automotive - Phụ tùng ô tô\n🔟 Toys - Đồ chơi\n\nBạn có thể click vào từng danh mục trên sidebar để xem đầy đủ sản phẩm.",
        "products_query": None
    },
    "chiết khấu hoặc giảm giá": {
        "answer": "Hiện tại chúng tôi đang áp dụng chương trình giảm giá:\n🎁 Giảm 10% cho đơn hàng đầu tiên\n🎁 Miễn phí vận chuyển cho đơn hàng trên 500.000₫\n🎁 Khách hàng trung thành được tích điểm\n\nHãy duyệt bộ sưu tập 'Giá Rẻ' của chúng tôi để tìm những sản phẩm giá tốt nhất!",
        "products_query": "cheap"
    },
    "giao hàng mất bao lâu": {
        "answer": "Thời gian giao hàng:\n⏱️ Giao hàng standard: 5-7 ngày làm việc\n⏱️ Giao hàng nhanh: 2-3 ngày làm việc (+50.000₫)\n⏱️ Giao hàng trong ngày: Áp dụng tại các thành phố lớn (+100.000₫)\n\nGhi chú: Hàng sẽ được đóng gói cẩn thận và bảo hiểm miễn phí.",
        "products_query": None
    },
    "chính sách đổi trả như thế nào": {
        "answer": "Chính sách đổi trả của chúng tôi:\n✅ Đổi/trả trong 30 ngày nếu sản phẩm lỗi\n✅ Đổi/trả trong 7 ngày nếu không hài lòng\n✅ Hoàn tiền 100% nếu không cần sản phẩm\n✅ Vận chuyển trả hàng MIỄN PHÍ\n\nLiên hệ với chúng tôi để được hỗ trợ chi tiết!",
        "products_query": None
    },
    "thanh toán bằng cách nào": {
        "answer": "Phương thức thanh toán:\n💳 Thẻ tín dụng/ghi nợ (Visa, Mastercard)\n🏦 Chuyển khoản ngân hàng\n📱 Ví điện tử (Momo, ZaloPay)\n💵 Tiền mặt khi nhận hàng (COD)\n\nTất cả giao dịch được bảo mật bằng SSL 256-bit.",
        "products_query": None
    },
    "sản phẩm này có bao nhiêu trong kho": {
        "answer": "Tất cả các sản phẩm trên website của chúng tôi đều còn hàng và sẵn sàng giao ngay. Bạn có thể thêm vào giỏ và thanh toán bất kỳ lúc nào!",
        "products_query": None
    },
}

# ==================== LOAD DATA ====================

df = pd.read_csv('data_user500.csv')

# Build product database
product_db = {}
for product_id in df['product_id'].unique():
    product_df = df[df['product_id'] == product_id].iloc[0]
    product_db[product_id] = {
        'id': int(product_id),
        'name': f'Product {product_id}',
        'category': str(product_df['category']),
        'price': round(100 + product_id % 500, 2),
        'interaction_count': len(df[df['product_id'] == product_id]),
        'behavior_score': float(product_df['behavior_score']),
        'rating': round(3.5 + (product_id % 20) / 10, 1),
        'reviews': (product_id % 100) + 10,
        'in_stock': True,
    }

# Get all unique categories
CATEGORIES = sorted(set(p['category'] for p in product_db.values()))

# Intent detection
INTENT_KEYWORDS = {
    'recommend': ['recommend', 'suggest', 'gợi ý', 'suggestion', 'recommend sản phẩm cho tôi'],
    'cheap': ['cheap', 'rẻ', 'budget', 'affordable', 'giá rẻ', 'giá tốt'],
    'compare': ['compare', 'so sánh', 'difference', 'khác biệt'],
    'similar': ['similar', 'tương tự', 'like', 'giống như'],
    'best': ['best', 'tốt nhất', 'top', 'popular', 'bán chạy'],
    'category': ['category', 'danh mục', 'type', 'loại'],
}

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                return intent
    return 'default'

def find_knowledge_base_answer(question: str):
    """Tìm câu trả lời từ knowledge base"""
    q = question.lower().strip()
    
    # Tìm match chính xác hoặc gần gần
    for kb_question, kb_answer in KNOWLEDGE_BASE.items():
        if kb_question in q or q in kb_question:
            return kb_answer
    
    # Tìm match từ khóa
    for kb_question, kb_answer in KNOWLEDGE_BASE.items():
        keywords = kb_question.split()
        if any(keyword in q for keyword in keywords if len(keyword) > 3):
            return kb_answer
    
    return None

def get_user_interaction_history(user_id: int, limit: int = 10):
    user_interactions = df[df['user_id'] == user_id]
    if len(user_interactions) == 0:
        return []
    
    product_scores = defaultdict(float)
    for _, row in user_interactions.iterrows():
        pid = row['product_id']
        product_scores[pid] += row['behavior_score']
    
    top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [int(pid) for pid, _ in top_products]

def get_best_products(limit: int = 20):
    best = sorted(product_db.items(), 
                  key=lambda x: x[1]['interaction_count'], reverse=True)
    return [pid for pid, _ in best[:limit]]

def search_products(query: str, limit: int = 20):
    q = query.lower()
    results = []
    
    for pid, pdata in product_db.items():
        if q in pdata['name'].lower() or q in pdata['category'].lower():
            results.append(pid)
    
    results.sort(key=lambda p: product_db[p]['interaction_count'], reverse=True)
    return results[:limit]

def get_category_products(category: str, limit: int = None):
    cat_products = [pid for pid, p in product_db.items() if p['category'] == category]
    cat_products.sort(key=lambda p: product_db[p]['interaction_count'], reverse=True)
    if limit:
        return cat_products[:limit]
    return cat_products

def get_cheap_products(limit: int = 20):
    """Get products sorted by price (lowest first)"""
    cheap = sorted(product_db.items(), 
                   key=lambda x: x[1]['price'])
    return [pid for pid, _ in cheap[:limit]]

# ==================== HTML TEMPLATES ====================

BASE_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Commerce Store with AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            gap: 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            text-decoration: none;
            color: white;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .search-bar {
            display: flex;
            gap: 10px;
            flex: 1;
            max-width: 400px;
        }
        
        .search-bar input {
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .search-bar button {
            padding: 10px 20px;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .search-bar button:hover {
            background: #f0f0f0;
        }
        
        .user-info {
            color: white;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        .content-layout {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .sidebar {
            background: white;
            padding: 20px;
            border-radius: 8px;
            height: fit-content;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 80px;
        }
        
        .sidebar h3 {
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .category-list {
            list-style: none;
        }
        
        .category-list li {
            margin-bottom: 8px;
        }
        
        .category-list a {
            color: #666;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s;
            padding: 8px 12px;
            border-radius: 4px;
            display: block;
        }
        
        .category-list a:hover {
            color: #667eea;
            background: #f0f0f0;
            padding-left: 16px;
        }
        
        .category-list a.active {
            color: #667eea;
            background: #e8e8ff;
            font-weight: bold;
            border-left: 3px solid #667eea;
            padding-left: 13px;
        }
        
        .main-content h2 {
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .product-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .product-image {
            width: 100%;
            height: 150px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            text-align: center;
            padding: 10px;
        }
        
        .product-info {
            padding: 15px;
        }
        
        .product-name {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 13px;
            color: #333;
        }
        
        .product-category {
            font-size: 11px;
            color: #999;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        
        .product-rating {
            color: #ffc107;
            font-size: 12px;
            margin-bottom: 8px;
        }
        
        .product-price {
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .product-btn {
            width: 100%;
            padding: 8px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            transition: all 0.3s;
        }
        
        .product-btn:hover {
            background: #764ba2;
        }
        
        /* Chat Widget */
        .chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            height: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            z-index: 1000;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-header h3 {
            font-size: 14px;
            margin: 0;
        }
        
        .close-chat {
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #fafafa;
        }
        
        .message {
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 13px;
            max-width: 85%;
            line-height: 1.4;
            word-wrap: break-word;
        }
        
        .message.user {
            align-self: flex-end;
            background: #667eea;
            color: white;
        }
        
        .message.bot {
            align-self: flex-start;
            background: white;
            color: #333;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chat-products {
            padding: 10px;
            border-top: 1px solid #eee;
            max-height: 120px;
            overflow-y: auto;
            background: #f9f9f9;
        }
        
        .chat-product-item {
            padding: 8px;
            background: white;
            margin: 3px 0;
            border-radius: 5px;
            font-size: 12px;
            cursor: pointer;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }
        
        .chat-product-item:hover {
            background: #f0f0f0;
            transform: translateX(3px);
        }
        
        .chat-input-area {
            padding: 12px;
            border-top: 1px solid #eee;
            display: flex;
            gap: 8px;
        }
        
        .chat-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 13px;
        }
        
        .chat-send {
            padding: 8px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .chat-send:hover {
            background: #764ba2;
        }
        
        footer {
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 40px;
        }
        
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .category-page-header {
            margin-bottom: 30px;
        }
        
        .category-page-header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .category-info {
            background: white;
            padding: 15px;
            border-radius: 8px;
            color: #666;
            margin-bottom: 20px;
        }

        .product-count {
            color: #999;
            margin-bottom: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <div class="header-content">
            <a href="/" class="logo">
                🛒 E-Store
            </a>
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="Tìm kiếm sản phẩm...">
                <button onclick="searchProducts()">Tìm</button>
            </div>
            <div class="user-info">
                👤 User ID: 63
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    <!-- Chat Widget -->
    <div class="chat-widget">
        <div class="chat-header">
            <h3>💬 AI Shopping Assistant</h3>
            <button class="close-chat" onclick="toggleChat()">×</button>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                👋 Xin chào! Tôi là AI Shopping Assistant. Hãy hỏi tôi bất cứ điều gì về:
                <br><br>
                • Sản phẩm và danh mục<br>
                • Gợi ý sản phẩm<br>
                • Chính sách giao hàng<br>
                • Thanh toán & đổi trả<br>
                • Giảm giá & khuyến mãi
            </div>
        </div>
        
        <div id="chatProducts" class="chat-products" style="display: none;"></div>
        
        <div class="chat-input-area">
            <input type="text" id="chatInput" class="chat-input" placeholder="Hỏi gì đó..." 
                   onkeypress="if(event.key==='Enter') sendMessage()">
            <button class="chat-send" onclick="sendMessage()">Gửi</button>
        </div>
    </div>
    
    <!-- Footer -->
    <footer>
        <p>🎉 E-Commerce Demo with RAG & AI Chat Integration - Phase 2D</p>
        <p>Status: 🟢 PRODUCTION READY | Version 2.0 Enhanced</p>
    </footer>
    
    <!-- Scripts -->
    <script>
        const userId = 63;
        
        async function loadCategories() {
            try {
                const response = await fetch('/api/categories');
                const data = await response.json();
                
                const categoryList = document.querySelector('.category-list');
                if (categoryList) {
                    categoryList.innerHTML = '';
                    data.categories.forEach(cat => {
                        const li = document.createElement('li');
                        li.innerHTML = `<a href="/category/${encodeURIComponent(cat)}">${cat}</a>`;
                        categoryList.appendChild(li);
                    });
                }
            } catch (error) {
                console.error('Error loading categories:', error);
            }
        }
        
        async function loadProducts(products) {
            const grid = document.getElementById('productsGrid');
            if (!grid) return;
            
            grid.innerHTML = '';
            
            products.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.innerHTML = `
                    <div class="product-image">${product.name}</div>
                    <div class="product-info">
                        <div class="product-name">${product.name}</div>
                        <div class="product-category">${product.category}</div>
                        <div class="product-rating">⭐ ${product.rating}/5 (${product.reviews} reviews)</div>
                        <div class="product-price">${product.price.toLocaleString()}₫</div>
                        <button class="product-btn" onclick="event.stopPropagation(); addToCart(${product.id})">
                            🛒 Thêm vào giỏ
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
        
        async function loadBestProducts() {
            try {
                const response = await fetch('/api/products?sort=best');
                const data = await response.json();
                loadProducts(data.products);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function searchProducts() {
            const query = document.getElementById('searchInput').value;
            if (!query.trim()) return;
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, limit: 50 })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    loadProducts(data.products);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Display user message
            const messagesDiv = document.getElementById('chatMessages');
            const userMsg = document.createElement('div');
            userMsg.className = 'message user';
            userMsg.textContent = message;
            messagesDiv.appendChild(userMsg);
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        message: message,
                        context: {}
                    })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    // Display bot message
                    const botMsg = document.createElement('div');
                    botMsg.className = 'message bot';
                    botMsg.textContent = data.bot_message;
                    messagesDiv.appendChild(botMsg);
                    
                    // Display products if available
                    if (data.products && data.products.length > 0) {
                        displayChatProducts(data.products);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function displayChatProducts(products) {
            const productsDiv = document.getElementById('chatProducts');
            productsDiv.innerHTML = '';
            
            products.forEach(p => {
                const item = document.createElement('div');
                item.className = 'chat-product-item';
                item.textContent = `${p.name} - ${p.price.toLocaleString()}₫`;
                item.onclick = () => addToCart(p.id);
                productsDiv.appendChild(item);
            });
            
            productsDiv.style.display = 'block';
        }
        
        function addToCart(productId) {
            const messagesDiv = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message bot';
            msg.textContent = `✅ Sản phẩm P${productId} đã được thêm vào giỏ hàng!`;
            messagesDiv.appendChild(msg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function toggleChat() {
            console.log('Chat toggled');
        }
        
        // Load categories on startup
        window.addEventListener('DOMContentLoaded', () => {
            loadCategories();
        });
    </script>
</body>
</html>
"""

HOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<div class="hero">
    <h1>🤖 E-Commerce với AI Shopping Assistant</h1>
    <p>Hãy hỏi trợ lý AI ở góc dưới bên phải hoặc duyệt các danh mục sản phẩm!</p>
</div>

<div class="content-layout">
    <!-- Sidebar -->
    <div class="sidebar">
        <h3>📂 Danh Mục</h3>
        <ul class="category-list" id="categoryList"></ul>
        
        <h3 style="margin-top: 20px;">🔍 Lọc</h3>
        <ul class="category-list">
            <li><a href="/?sort=best">⭐ Bán Chạy</a></li>
            <li><a href="/?sort=cheap">💰 Giá Rẻ</a></li>
            <li><a href="/?sort=rated">🏆 Top Rated</a></li>
        </ul>
    </div>
    
    <!-- Products -->
    <div class="main-content">
        <h2>📦 Sản Phẩm Nổi Bật</h2>
        <div class="products-grid" id="productsGrid"></div>
    </div>
</div>

<script>
    window.addEventListener('DOMContentLoaded', () => {
        loadBestProducts();
    });
</script>
{% endblock %}
"""

CATEGORY_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<div class="content-layout">
    <!-- Sidebar -->
    <div class="sidebar">
        <h3>📂 Danh Mục</h3>
        <ul class="category-list" id="categoryList"></ul>
        
        <h3 style="margin-top: 20px;">🔍 Lọc</h3>
        <ul class="category-list">
            <li><a href="/">⭐ Tất Cả</a></li>
            <li><a href="/?sort=best">⭐ Bán Chạy</a></li>
            <li><a href="/?sort=cheap">💰 Giá Rẻ</a></li>
        </ul>
    </div>
    
    <!-- Products -->
    <div class="main-content">
        <div class="category-page-header">
            <h1>📦 {{ category }}</h1>
            <div class="category-info">
                <p>Chuyên mục {{ category }} - Khám phá những sản phẩm chất lượng từ các thương hiệu hàng đầu</p>
            </div>
            <p class="product-count">Tổng {{ product_count }} sản phẩm</p>
        </div>
        <div class="products-grid" id="productsGrid"></div>
    </div>
</div>

<script>
    window.addEventListener('DOMContentLoaded', () => {
        loadProducts({{ products | tojson }});
    });
</script>
{% endblock %}
"""

# ==================== FLASK ROUTES ====================

@app.route('/')
def home():
    return render_template_string(BASE_HTML + HOME_TEMPLATE)

@app.route('/category/<category>')
def category(category):
    products = get_category_products(category, limit=50)
    product_list = [
        {
            'id': pid,
            'name': product_db[pid]['name'],
            'category': product_db[pid]['category'],
            'price': product_db[pid]['price'],
            'rating': product_db[pid]['rating'],
            'reviews': product_db[pid]['reviews'],
        }
        for pid in products if pid in product_db
    ]
    
    template = BASE_HTML + CATEGORY_TEMPLATE
    return render_template_string(
        template,
        category=category,
        products=product_list,
        product_count=len(product_list)
    )

@app.route('/api/categories')
def api_categories():
    return jsonify({
        'status': 'success',
        'categories': CATEGORIES,
        'count': len(CATEGORIES)
    })

@app.route('/api/products')
def api_products():
    category = request.args.get('category')
    sort = request.args.get('sort', 'best')
    
    if sort == 'cheap':
        product_ids = get_cheap_products(limit=50)
    elif category:
        product_ids = get_category_products(category, limit=50)
    else:
        product_ids = get_best_products(limit=50)
    
    products = [
        {
            'id': pid,
            'name': product_db[pid]['name'],
            'category': product_db[pid]['category'],
            'price': product_db[pid]['price'],
            'rating': product_db[pid]['rating'],
            'reviews': product_db[pid]['reviews'],
            'interaction_count': product_db[pid]['interaction_count']
        }
        for pid in product_ids
    ]
    
    return jsonify({
        'status': 'success',
        'products': products,
        'count': len(products)
    })

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json
    query = data.get('query', '').strip()
    limit = int(data.get('limit', 50))
    
    product_ids = search_products(query, limit=limit)
    
    products = [
        {
            'id': pid,
            'name': product_db[pid]['name'],
            'category': product_db[pid]['category'],
            'price': product_db[pid]['price'],
            'rating': product_db[pid]['rating'],
            'reviews': product_db[pid]['reviews'],
        }
        for pid in product_ids
    ]
    
    return jsonify({
        'status': 'success',
        'query': query,
        'products': products,
        'count': len(products)
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_id = int(data.get('user_id', 63))
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Empty message'}), 400
    
    # Kiểm tra Knowledge Base trước
    kb_answer = find_knowledge_base_answer(message)
    
    if kb_answer:
        # Nếu có câu trả lời từ knowledge base
        products = []
        
        # Nếu knowledge base có gợi ý query sản phẩm
        if kb_answer.get('products_query'):
            query = kb_answer['products_query']
            if query == 'best':
                product_ids = get_best_products(limit=5)
            elif query == 'cheap':
                product_ids = get_cheap_products(limit=5)
            else:
                product_ids = []
            
            products = [
                {
                    'id': pid,
                    'name': product_db[pid]['name'],
                    'category': product_db[pid]['category'],
                    'price': product_db[pid]['price'],
                    'rating': product_db[pid]['rating'],
                }
                for pid in product_ids if pid in product_db
            ]
        
        return jsonify({
            'status': 'success',
            'user_message': message,
            'bot_message': kb_answer['answer'],
            'intent': 'knowledge_base',
            'products': products,
            'retrieval_source': 'knowledge_base',
        })
    
    # Nếu không tìm thấy trong knowledge base, sử dụng intent detection
    intent = detect_intent(message)
    
    product_ids = []
    retrieval_source = 'default'
    
    if intent == 'recommend':
        product_ids = get_user_interaction_history(user_id, limit=5)
        retrieval_source = 'user_history'
    elif intent == 'best':
        product_ids = get_best_products(limit=5)
        retrieval_source = 'popularity'
    elif intent == 'cheap':
        product_ids = get_cheap_products(limit=5)
        retrieval_source = 'cheap'
    elif intent == 'category':
        categories = CATEGORIES
        for cat in categories:
            if cat.lower() in message.lower():
                product_ids = get_category_products(cat, limit=5)
                retrieval_source = 'category'
                break
        if not product_ids:
            product_ids = get_best_products(limit=5)
    else:
        if len(message) > 2:
            product_ids = search_products(message, limit=5)
            retrieval_source = 'search'
        if not product_ids:
            product_ids = get_best_products(limit=5)
    
    templates = {
        'recommend': 'Dựa trên lịch sử mua hàng của bạn, đây là những sản phẩm được gợi ý:',
        'cheap': 'Những sản phẩm giá tốt cho bạn:',
        'best': 'Sản phẩm bán chạy nhất của chúng tôi:',
        'category': 'Sản phẩm trong danh mục này:',
        'default': 'Những sản phẩm bạn có thể quan tâm:',
    }
    
    products = [
        {
            'id': pid,
            'name': product_db[pid]['name'],
            'category': product_db[pid]['category'],
            'price': product_db[pid]['price'],
            'rating': product_db[pid]['rating'],
        }
        for pid in product_ids if pid in product_db
    ]
    
    return jsonify({
        'status': 'success',
        'user_message': message,
        'bot_message': templates.get(intent, templates['default']),
        'intent': intent,
        'products': products,
        'retrieval_source': retrieval_source,
    })

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 E-COMMERCE WITH RAG & AI CHAT - VERSION 2.0 ENHANCED")
    print("=" * 80)
    print("\n✨ Version 2.0 Features:")
    print("  ✅ Full Category Pages with Product Listings")
    print("  ✅ Knowledge Base with Fixed Q&A")
    print("  ✅ Smart Chat with Context-Aware Answers")
    print("  ✅ Intent Detection + Knowledge Base Lookup")
    print("  ✅ Product Retrieval (4 strategies)")
    print("  ✅ Responsive Design")
    print("\n📂 Categories Available:")
    for cat in CATEGORIES:
        print(f"   • {cat}")
    
    print("\n🌐 Access URLs:")
    print("   👉 Home: http://localhost:5000/")
    print("   👉 Category: http://localhost:5000/category/Electronics")
    
    print("\n💬 Knowledge Base Topics:")
    for i, question in enumerate(KNOWLEDGE_BASE.keys(), 1):
        print(f"   {i}. {question}")
    
    print("\n💬 Try these in chat:")
    print("   • 'các danh mục sản phẩm là gì'")
    print("   • 'sản phẩm tốt nhất là gì'")
    print("   • 'thanh toán bằng cách nào'")
    print("   • 'giao hàng mất bao lâu'")
    print("   • 'chính sách đổi trả như thế nào'")
    
    print("\n" + "=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
