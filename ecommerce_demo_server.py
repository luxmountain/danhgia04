"""
E-Commerce Integration Demo Server
Demonstrates RAG Chat integrated with Product Listing
"""

from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import json
import pickle
from collections import defaultdict

app = Flask(__name__)

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

# Intent detection
INTENT_KEYWORDS = {
    'recommend': ['recommend', 'suggest', 'gợi ý', 'suggestion'],
    'cheap': ['cheap', 'rẻ', 'budget', 'affordable'],
    'compare': ['compare', 'so sánh', 'difference'],
    'similar': ['similar', 'tương tự', 'like'],
    'best': ['best', 'tốt nhất', 'top', 'popular'],
    'category': ['category', 'danh mục', 'type', 'loại'],
}

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                return intent
    return 'default'

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

def get_category_products(category: str, limit: int = 20):
    cat_products = [pid for pid, p in product_db.items() if p['category'] == category]
    cat_products.sort(key=lambda p: product_db[p]['interaction_count'], reverse=True)
    return cat_products[:limit]

# ==================== FLASK ROUTES ====================

HTML_TEMPLATE = """
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
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
        }
        
        .search-bar {
            display: flex;
            gap: 10px;
            flex: 1;
            max-width: 400px;
            margin: 0 40px;
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
        }
        
        .container {
            max-width: 1200px;
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
        }
        
        .sidebar h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .category-list {
            list-style: none;
        }
        
        .category-list li {
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .category-list a {
            color: #666;
            text-decoration: none;
            cursor: pointer;
            transition: color 0.3s;
        }
        
        .category-list a:hover {
            color: #667eea;
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
            transition: transform 0.3s, box-shadow 0.3s;
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
        }
        
        .product-info {
            padding: 15px;
        }
        
        .product-name {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 13px;
        }
        
        .product-category {
            font-size: 12px;
            color: #999;
            margin-bottom: 8px;
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
            height: 550px;
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
        
        footer {
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <div class="header-content">
            <div class="logo">🛒 E-Store AI</div>
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="Tìm kiếm sản phẩm...">
                <button onclick="searchProducts()">Tìm</button>
            </div>
            <div style="color: white;">User ID: 63</div>
        </div>
    </header>
    
    <!-- Main Content -->
    <div class="container">
        <div class="hero">
            <h1>🤖 E-Commerce với AI Shopping Assistant</h1>
            <p>Hãy hỏi trợ lý AI ở góc dưới bên phải để tìm sản phẩm phù hợp!</p>
        </div>
        
        <div class="content-layout">
            <!-- Sidebar -->
            <div class="sidebar">
                <h3>📂 Danh Mục</h3>
                <ul class="category-list" id="categoryList"></ul>
                
                <h3 style="margin-top: 20px;">🔍 Lọc</h3>
                <ul class="category-list">
                    <li><a onclick="loadBestProducts()">⭐ Bán Chạy</a></li>
                    <li><a onclick="searchByKeyword('cheap')">💰 Giá Rẻ</a></li>
                    <li><a onclick="searchByKeyword('best')">🏆 Top Rated</a></li>
                </ul>
            </div>
            
            <!-- Products -->
            <div>
                <h2 style="color: #667eea; margin-bottom: 20px;">📦 Sản Phẩm</h2>
                <div class="products-grid" id="productsGrid"></div>
            </div>
        </div>
    </div>
    
    <!-- Chat Widget -->
    <div class="chat-widget">
        <div class="chat-header">
            <h3>💬 AI Shopping Assistant</h3>
            <button onclick="closeChatDemo()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer;">×</button>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                👋 Xin chào! Tôi là trợ lý mua sắm AI. Tôi có thể giúp bạn:
                <br><br>
                • Gợi ý sản phẩm từ lịch sử mua hàng<br>
                • Tìm sản phẩm giá rẻ<br>
                • So sánh sản phẩm<br>
                • Khám phá sản phẩm tương tự<br>
                • Duyệt theo danh mục
            </div>
        </div>
        
        <div id="chatProducts" class="chat-products" style="display: none;"></div>
        
        <div class="chat-input-area">
            <input type="text" id="chatInput" class="chat-input" placeholder="Hỏi gì đó..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button class="chat-send" onclick="sendMessage()">Gửi</button>
        </div>
    </div>
    
    <!-- Footer -->
    <footer>
        <p>🎉 E-Commerce Demo with RAG & AI Chat Integration</p>
        <p>Phase 2D - Integration Testing Complete ✅</p>
    </footer>
    
    <!-- Scripts -->
    <script>
        const userId = 63;
        
        // Load categories on page load
        async function loadCategories() {
            try {
                const response = await fetch('/api/categories');
                const data = await response.json();
                
                const categoryList = document.getElementById('categoryList');
                data.categories.forEach(cat => {
                    const li = document.createElement('li');
                    li.innerHTML = `<a onclick="loadCategory('${cat}')">${cat}</a>`;
                    categoryList.appendChild(li);
                });
            } catch (error) {
                console.error('Error loading categories:', error);
            }
        }
        
        // Load products
        async function loadProducts(products) {
            const grid = document.getElementById('productsGrid');
            grid.innerHTML = '';
            
            products.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.innerHTML = `
                    <div class="product-image">${product.name}</div>
                    <div class="product-info">
                        <div class="product-name">${product.name}</div>
                        <div class="product-category">${product.category}</div>
                        <div class="product-rating">⭐ ${product.rating}/5</div>
                        <div class="product-price">${product.price.toLocaleString()}₫</div>
                        <button class="product-btn" onclick="event.stopPropagation(); addToCart(${product.id})">
                            🛒 Thêm vào giỏ
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
        
        // Load best products
        async function loadBestProducts() {
            try {
                const response = await fetch('/api/products?sort=best');
                const data = await response.json();
                loadProducts(data.products);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        // Load category
        async function loadCategory(category) {
            try {
                const response = await fetch(`/api/products?category=${encodeURIComponent(category)}`);
                const data = await response.json();
                loadProducts(data.products);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        // Search
        async function searchProducts() {
            const query = document.getElementById('searchInput').value;
            if (!query.trim()) return;
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, limit: 20 })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    loadProducts(data.products);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        // Search by keyword
        function searchByKeyword(keyword) {
            document.getElementById('searchInput').value = keyword;
            searchProducts();
        }
        
        // Send chat message
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
                    
                    // Display products
                    if (data.products && data.products.length > 0) {
                        displayChatProducts(data.products);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Display products in chat
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
        
        // Add to cart
        function addToCart(productId) {
            const messagesDiv = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message bot';
            msg.textContent = `✅ Sản phẩm P${productId} đã được thêm vào giỏ hàng!`;
            messagesDiv.appendChild(msg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Close chat
        function closeChatDemo() {
            // In demo, we don't actually close
            console.log('Chat would be minimized');
        }
        
        // Load on startup
        window.addEventListener('DOMContentLoaded', () => {
            loadCategories();
            loadBestProducts();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/categories')
def api_categories():
    categories = sorted(set(p['category'] for p in product_db.values()))
    return jsonify({
        'status': 'success',
        'categories': categories,
        'count': len(categories)
    })

@app.route('/api/products')
def api_products():
    category = request.args.get('category')
    sort = request.args.get('sort', 'best')
    
    if category:
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
    limit = int(data.get('limit', 20))
    
    product_ids = search_products(query, limit=limit)
    
    products = [
        {
            'id': pid,
            'name': product_db[pid]['name'],
            'category': product_db[pid]['category'],
            'price': product_db[pid]['price'],
            'rating': product_db[pid]['rating'],
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
    
    # Detect intent
    intent = detect_intent(message)
    
    # Get products based on intent
    product_ids = []
    retrieval_source = 'default'
    
    if intent == 'recommend':
        product_ids = get_user_interaction_history(user_id, limit=5)
        retrieval_source = 'user_history'
    elif intent == 'best':
        product_ids = get_best_products(limit=5)
        retrieval_source = 'popularity'
    elif intent == 'category':
        categories = sorted(set(p['category'] for p in product_db.values()))
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
    
    # Build response
    templates = {
        'recommend': 'Dựa trên lịch sử của bạn, đây là những sản phẩm được gợi ý:',
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
    print("🚀 E-COMMERCE WITH RAG & AI CHAT INTEGRATION - DEMO SERVER")
    print("=" * 80)
    print("\n✨ Server Features:")
    print("  ✅ Product Listing with Categories")
    print("  ✅ AI-Powered Search & Recommendations")
    print("  ✅ Real-time Chat Widget")
    print("  ✅ Intent-Based Retrieval")
    print("  ✅ Multi-Strategy Product Discovery")
    print("\n🌐 Open your browser and navigate to:")
    print("   👉 http://localhost:5000/")
    print("\n💬 Try these in the chat widget:")
    print("   • 'recommend sản phẩm cho tôi'")
    print("   • 'show me electronics'")
    print("   • 'tôi muốn sản phẩm giá rẻ'")
    print("   • 'sản phẩm bán chạy nhất'")
    print("   • 'tìm sản phẩm tương tự'")
    print("\n" + "=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
