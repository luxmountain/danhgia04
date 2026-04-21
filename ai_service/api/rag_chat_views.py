"""
RAG & Chat System - Django API Integration
Provides REST endpoints for chat functionality
"""

import json
import pickle
import numpy as np
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from collections import defaultdict

# Load data and embeddings
df = pd.read_csv('data_user500.csv')
with open('product_embeddings.pkl', 'rb') as f:
    product_embeddings = pickle.load(f)

with open('rag_chat_config.json', 'r') as f:
    config = json.load(f)

# ==================== INTENT DETECTION ====================

INTENT_KEYWORDS = {
    'recommend': ['recommend', 'suggest', 'gợi ý', 'recommendation', 'help', 'đề xuất'],
    'cheap': ['cheap', 'rẻ', 'budget', 'giá rẻ', 'affordable', 'tiết kiệm'],
    'compare': ['compare', 'so sánh', 'khác nhau', 'difference', 'vs', 'giống'],
    'similar': ['similar', 'tương tự', 'giống', 'like', 'bộ sưu tập'],
    'best': ['best', 'tốt nhất', 'top', 'popular', 'bán chạy', 'hàng đầu'],
    'category': ['category', 'danh mục', 'type', 'loại', 'kind'],
}

def detect_intent(query: str) -> str:
    """Detect user intent from query"""
    q = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                return intent
    return 'default'

# ==================== PRODUCT DATABASE ====================

product_db = {}
for product_id in df['product_id'].unique():
    product_df = df[df['product_id'] == product_id].iloc[0]
    product_db[product_id] = {
        'id': product_id,
        'category': product_df['category'],
        'interaction_count': len(df[df['product_id'] == product_id]),
        'behavior_score': float(product_df['behavior_score'])
    }

# ==================== RETRIEVAL FUNCTIONS ====================

def get_user_interaction_history(user_id: int, limit: int = 5):
    """Get user's top interactions"""
    user_interactions = df[df['user_id'] == user_id]
    
    if len(user_interactions) == 0:
        return []
    
    product_scores = defaultdict(float)
    for _, row in user_interactions.iterrows():
        pid = row['product_id']
        product_scores[pid] += row['behavior_score']
    
    top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{'product_id': int(pid), 'score': float(score)} for pid, score in top_products]

def get_similar_products(product_id: int, limit: int = 5):
    """Get products similar to given product"""
    if product_id not in product_embeddings:
        return []
    
    product_emb = product_embeddings[product_id]
    similarities = []
    
    for pid, emb in product_embeddings.items():
        if pid != product_id:
            sim = np.dot(product_emb, emb) / (np.linalg.norm(product_emb) * np.linalg.norm(emb) + 1e-8)
            similarities.append((int(pid), float(sim)))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [{'product_id': pid, 'similarity': sim} for pid, sim in similarities[:limit]]

def get_category_products(category: str, limit: int = 5):
    """Get popular products in a category"""
    cat_products = [(p['id'], p) for p in product_db.values() if p['category'] == category]
    
    if not cat_products:
        return []
    
    cat_products.sort(key=lambda x: x[1]['interaction_count'], reverse=True)
    return [
        {
            'product_id': int(pid),
            'category': p['category'],
            'interaction_count': p['interaction_count']
        }
        for pid, p in cat_products[:limit]
    ]

def vector_search(query_embedding: np.ndarray, k: int = 5):
    """Fallback: cosine similarity search"""
    similarities = []
    q_norm = np.linalg.norm(query_embedding)
    
    for pid, emb in product_embeddings.items():
        e_norm = np.linalg.norm(emb)
        if q_norm > 0 and e_norm > 0:
            sim = np.dot(query_embedding, emb) / (q_norm * e_norm)
        else:
            sim = 0
        similarities.append((int(pid), float(sim)))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [{'product_id': pid, 'similarity_score': sim} for pid, sim in similarities[:k]]

# ==================== RESPONSE TEMPLATES ====================

TEMPLATES = {
    'recommend': {
        'header': "Dựa trên lịch sử của bạn, tôi gợi ý các sản phẩm sau:",
        'empty': "Bạn chưa có lịch sử mua hàng. Hãy tìm hiểu các sản phẩm phổ biến."
    },
    'cheap': {
        'header': "Các sản phẩm giá tốt dành cho bạn:",
        'empty': "Không có sản phẩm nào phù hợp với tiêu chí."
    },
    'compare': {
        'header': "So sánh các sản phẩm liên quan:",
        'empty': "Vui lòng chỉ định sản phẩm để so sánh."
    },
    'similar': {
        'header': "Sản phẩm tương tự mà bạn có thể quan tâm:",
        'empty': "Không tìm thấy sản phẩm tương tự."
    },
    'best': {
        'header': "Sản phẩm bán chạy và được yêu thích:",
        'empty': "Không có dữ liệu sản phẩm."
    },
    'category': {
        'header': "Sản phẩm phổ biến trong danh mục này:",
        'empty': "Danh mục không tồn tại."
    },
    'default': {
        'header': "Dưới đây là những gợi ý cho bạn:",
        'empty': "Vui lòng nhập một câu hỏi rõ ràng hơn."
    }
}

# ==================== CHAT SESSIONS ====================

chat_sessions = {}

def get_or_create_session(user_id: int):
    """Get or create chat session"""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = {
            'user_id': user_id,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
    chat_sessions[user_id]['last_activity'] = datetime.now().isoformat()
    return chat_sessions[user_id]

# ==================== DJANGO VIEWS ====================

@csrf_exempt
@require_http_methods(["POST"])
def start_chat(request):
    """
    Start a new chat session
    
    POST /api/chat/start/
    Request: {"user_id": 123}
    Response: {"status": "ok", "message": "...", "session_id": user_id}
    """
    try:
        data = json.loads(request.body)
        user_id = int(data.get('user_id'))
        
        session = get_or_create_session(user_id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Xin chào! Tôi là trợ lý mua sắm AI. Tôi có thể giúp bạn gợi ý sản phẩm, so sánh, tìm kiếm... Hỏi tôi bất cứ điều gì!',
            'session_id': user_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def chat_message(request):
    """
    Send chat message and get response
    
    POST /api/chat/message/
    Request: {
        "user_id": 123,
        "message": "recommend sản phẩm",
        "context": {"product_id": 456, "category": "Electronics"}
    }
    Response: {
        "status": "ok",
        "user_message": "...",
        "bot_response": "...",
        "intent": "recommend",
        "products": [123, 456, ...],
        "timestamp": "..."
    }
    """
    try:
        data = json.loads(request.body)
        user_id = int(data.get('user_id'))
        message = str(data.get('message', '')).strip()
        context = data.get('context', {})
        
        if not message:
            return JsonResponse({
                'status': 'error',
                'message': 'Pesan kosong'
            }, status=400)
        
        # Get session
        session = get_or_create_session(user_id)
        
        # Detect intent
        intent = detect_intent(message)
        
        # Retrieve products based on intent
        products = []
        retrieval_source = 'default'
        
        if intent == 'recommend':
            # Get user interaction history
            products_data = get_user_interaction_history(user_id, limit=5)
            products = [p['product_id'] for p in products_data]
            retrieval_source = 'user_history'
            
        elif intent == 'similar' and 'product_id' in context:
            # Get similar products
            pid = int(context['product_id'])
            products_data = get_similar_products(pid, limit=5)
            products = [p['product_id'] for p in products_data]
            retrieval_source = 'similarity'
            
        elif intent == 'category' and 'category' in context:
            # Get category products
            cat = context['category']
            products_data = get_category_products(cat, limit=5)
            products = [p['product_id'] for p in products_data]
            retrieval_source = 'category'
            
        elif intent == 'best':
            # Get top products by interaction count
            top_products = sorted(
                product_db.values(),
                key=lambda x: x['interaction_count'],
                reverse=True
            )[:5]
            products = [p['id'] for p in top_products]
            retrieval_source = 'popularity'
            
        else:
            # Default: vector search
            # Get popular products as fallback
            popular = sorted(
                product_db.values(),
                key=lambda x: x['interaction_count'],
                reverse=True
            )[:5]
            products = [p['id'] for p in popular]
            retrieval_source = 'vector_search'
        
        # Generate response text
        template = TEMPLATES.get(intent, TEMPLATES['default'])
        response_text = template['header'] + "\n"
        
        if products:
            for idx, pid in enumerate(products, 1):
                if pid in product_db:
                    pdata = product_db[pid]
                    response_text += f"{idx}. [{pdata['category']}] Sản phẩm P{pid}\n"
        else:
            response_text = template.get('empty', 'Không tìm thấy sản phẩm nào.')
        
        # Build response
        response = {
            'status': 'success',
            'user_message': message,
            'bot_response': response_text,
            'intent': intent,
            'products': [int(p) for p in products],
            'retrieval_source': retrieval_source,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in session
        session['messages'].append({
            'user_message': message,
            'bot_response': response_text,
            'intent': intent,
            'timestamp': datetime.now().isoformat()
        })
        
        return JsonResponse(response)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def chat_history(request):
    """
    Get chat history for a user
    
    GET /api/chat/history/?user_id=123
    Response: {
        "status": "ok",
        "user_id": 123,
        "message_count": 5,
        "created_at": "...",
        "messages": [...]
    }
    """
    try:
        user_id = int(request.GET.get('user_id'))
        
        if user_id not in chat_sessions:
            return JsonResponse({
                'status': 'error',
                'message': 'Phiên chat không tồn tại'
            }, status=404)
        
        session = chat_sessions[user_id]
        
        return JsonResponse({
            'status': 'success',
            'user_id': user_id,
            'message_count': len(session['messages']),
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'messages': session['messages']
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def recommend_products(request):
    """
    Get product recommendations for a user
    
    POST /api/chat/recommend/
    Request: {
        "user_id": 123,
        "limit": 10,
        "strategy": "history"  # or "popular", "similar"
    }
    Response: {
        "status": "ok",
        "user_id": 123,
        "products": [{product details}],
        "strategy": "history"
    }
    """
    try:
        data = json.loads(request.body)
        user_id = int(data.get('user_id'))
        limit = int(data.get('limit', 10))
        strategy = data.get('strategy', 'history')
        
        products = []
        
        if strategy == 'history':
            products_data = get_user_interaction_history(user_id, limit=limit)
            products = products_data
        
        elif strategy == 'popular':
            top_products = sorted(
                product_db.values(),
                key=lambda x: x['interaction_count'],
                reverse=True
            )[:limit]
            products = [
                {
                    'product_id': p['id'],
                    'category': p['category'],
                    'interaction_count': p['interaction_count'],
                    'behavior_score': p['behavior_score']
                }
                for p in top_products
            ]
        
        else:
            # Random selection
            import random
            random_products = random.sample(list(product_db.items()), min(limit, len(product_db)))
            products = [
                {
                    'product_id': int(pid),
                    'category': p['category'],
                    'interaction_count': p['interaction_count'],
                    'behavior_score': p['behavior_score']
                }
                for pid, p in random_products
            ]
        
        return JsonResponse({
            'status': 'success',
            'user_id': user_id,
            'product_count': len(products),
            'strategy': strategy,
            'products': products,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def system_stats(request):
    """
    Get RAG/Chat system statistics
    
    GET /api/chat/stats/
    """
    try:
        return JsonResponse({
            'status': 'success',
            'system': {
                'name': 'RAG & Chat System',
                'version': '1.0'
            },
            'database': {
                'products': len(product_db),
                'categories': len(set(p['category'] for p in product_db.values())),
                'embeddings': len(product_embeddings)
            },
            'intents': list(INTENT_KEYWORDS.keys()),
            'templates': list(TEMPLATES.keys()),
            'active_sessions': len(chat_sessions),
            'total_messages': sum(len(s['messages']) for s in chat_sessions.values()),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
