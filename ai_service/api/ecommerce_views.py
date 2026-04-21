"""
E-Commerce Integration Views
Integrates RAG & Chat with Product Listing
"""

import json
import pickle
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

# ==================== LOAD RESOURCES ====================

df = pd.read_csv('data_user500.csv')

try:
    with open('product_embeddings.pkl', 'rb') as f:
        product_embeddings = pickle.load(f)
except:
    product_embeddings = {}

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
        'image': f'/static/products/product_{product_id}.jpg'
    }

# Intent detection keywords
INTENT_KEYWORDS = {
    'recommend': ['recommend', 'suggest', 'gợi ý', 'suggestion', 'help'],
    'cheap': ['cheap', 'rẻ', 'budget', 'affordable', 'tiết kiệm'],
    'compare': ['compare', 'so sánh', 'difference', 'vs'],
    'similar': ['similar', 'tương tự', 'like', 'giống'],
    'best': ['best', 'tốt nhất', 'top', 'popular', 'bán chạy'],
    'category': ['category', 'danh mục', 'type', 'loại'],
}

def detect_intent(query: str) -> str:
    """Detect user intent"""
    q = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                return intent
    return 'default'

def get_user_interaction_history(user_id: int, limit: int = 10):
    """Get user's interaction history"""
    user_interactions = df[df['user_id'] == user_id]
    
    if len(user_interactions) == 0:
        return []
    
    product_scores = defaultdict(float)
    for _, row in user_interactions.iterrows():
        pid = row['product_id']
        product_scores[pid] += row['behavior_score']
    
    top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [int(pid) for pid, _ in top_products]

def get_category_products(category: str, limit: int = 20):
    """Get products in category"""
    cat_products = [pid for pid, p in product_db.items() if p['category'] == category]
    
    # Sort by interaction count
    cat_products.sort(key=lambda p: product_db[p]['interaction_count'], reverse=True)
    return cat_products[:limit]

def get_best_products(limit: int = 20):
    """Get best/popular products"""
    best = sorted(product_db.items(), 
                  key=lambda x: x[1]['interaction_count'], reverse=True)
    return [pid for pid, _ in best[:limit]]

def search_products(query: str, limit: int = 20):
    """Search products by name/category"""
    q = query.lower()
    results = []
    
    for pid, pdata in product_db.items():
        if q in pdata['name'].lower() or q in pdata['category'].lower():
            results.append(pid)
    
    # Sort by relevance (interaction count)
    results.sort(key=lambda p: product_db[p]['interaction_count'], reverse=True)
    return results[:limit]

# ==================== DJANGO VIEWS ====================

def home(request):
    """Home page - Product listing"""
    user_id = request.GET.get('user_id', 63)
    try:
        user_id = int(user_id)
    except:
        user_id = 63
    
    # Get featured products
    featured_ids = get_best_products(limit=12)
    featured_products = [
        {
            **product_db[pid],
            'image_url': f'/static/product_{pid}.jpg'
        }
        for pid in featured_ids
    ]
    
    categories = sorted(set(p['category'] for p in product_db.values()))
    
    context = {
        'user_id': user_id,
        'featured_products': featured_products,
        'categories': categories,
        'page_title': 'E-Commerce Store',
    }
    
    return render(request, 'ecommerce/home.html', context)

def products_list(request):
    """Product listing page with filtering"""
    user_id = request.GET.get('user_id', 63)
    category = request.GET.get('category', None)
    search_q = request.GET.get('search', None)
    
    try:
        user_id = int(user_id)
    except:
        user_id = 63
    
    # Determine products to show
    if search_q and search_q.strip():
        product_ids = search_products(search_q, limit=50)
        page_title = f'Search: {search_q}'
    elif category and category.strip():
        product_ids = get_category_products(category, limit=50)
        page_title = f'Category: {category}'
    else:
        product_ids = get_best_products(limit=50)
        page_title = 'All Products'
    
    # Build product list
    products = [
        {
            **product_db[pid],
            'image_url': f'/static/product_{pid}.jpg'
        }
        for pid in product_ids
    ]
    
    categories = sorted(set(p['category'] for p in product_db.values()))
    
    context = {
        'user_id': user_id,
        'products': products,
        'categories': categories,
        'current_category': category,
        'search_query': search_q,
        'page_title': page_title,
        'product_count': len(products),
    }
    
    return render(request, 'ecommerce/products.html', context)

def product_detail(request, product_id):
    """Product detail page"""
    user_id = request.GET.get('user_id', 63)
    
    try:
        user_id = int(user_id)
        product_id = int(product_id)
    except:
        return HttpResponse('Invalid product', status=404)
    
    if product_id not in product_db:
        return HttpResponse('Product not found', status=404)
    
    product = product_db[product_id]
    
    # Get similar products
    similar_ids = get_category_products(product['category'], limit=6)
    similar_ids = [p for p in similar_ids if p != product_id][:5]
    
    similar_products = [
        {
            **product_db[pid],
            'image_url': f'/static/product_{pid}.jpg'
        }
        for pid in similar_ids
    ]
    
    context = {
        'user_id': user_id,
        'product': {
            **product,
            'image_url': f'/static/product_{product_id}.jpg'
        },
        'similar_products': similar_products,
        'page_title': product['name'],
    }
    
    return render(request, 'ecommerce/product_detail.html', context)

def cart(request):
    """Shopping cart page"""
    user_id = request.GET.get('user_id', 63)
    
    try:
        user_id = int(user_id)
    except:
        user_id = 63
    
    # Get user's interaction history (recommended products for cart)
    recommended_ids = get_user_interaction_history(user_id, limit=5)
    
    recommended_products = [
        {
            **product_db[pid],
            'image_url': f'/static/product_{pid}.jpg'
        }
        for pid in recommended_ids if pid in product_db
    ]
    
    context = {
        'user_id': user_id,
        'recommended_products': recommended_products,
        'page_title': 'Shopping Cart',
    }
    
    return render(request, 'ecommerce/cart.html', context)

# ==================== RAG CHAT ENDPOINTS ====================

@csrf_exempt
@require_http_methods(["POST"])
def rag_chat_api(request):
    """RAG Chat API endpoint for frontend"""
    try:
        data = json.loads(request.body)
        user_id = int(data.get('user_id', 63))
        message = str(data.get('message', '')).strip()
        
        if not message:
            return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)
        
        # Detect intent
        intent = detect_intent(message)
        
        # Retrieve products based on intent
        product_ids = []
        retrieval_source = 'default'
        
        if intent == 'recommend':
            product_ids = get_user_interaction_history(user_id, limit=5)
            retrieval_source = 'user_history'
        elif intent == 'best':
            product_ids = get_best_products(limit=5)
            retrieval_source = 'popularity'
        elif intent == 'category':
            # Extract category from message
            categories = sorted(set(p['category'] for p in product_db.values()))
            for cat in categories:
                if cat.lower() in message.lower():
                    product_ids = get_category_products(cat, limit=5)
                    retrieval_source = 'category'
                    break
            if not product_ids:
                product_ids = get_best_products(limit=5)
        else:
            # Default: search or popular
            if len(message) > 2:
                product_ids = search_products(message, limit=5)
                retrieval_source = 'search'
            if not product_ids:
                product_ids = get_best_products(limit=5)
        
        # Build product details
        products = [
            {
                'id': pid,
                'name': product_db[pid]['name'],
                'category': product_db[pid]['category'],
                'price': product_db[pid]['price'],
                'rating': product_db[pid]['rating'],
                'image_url': f'/static/product_{pid}.jpg',
                'interaction_count': product_db[pid]['interaction_count']
            }
            for pid in product_ids if pid in product_db
        ]
        
        # Generate response message
        templates = {
            'recommend': 'Dựa trên lịch sử của bạn, đây là những sản phẩm được gợi ý:',
            'cheap': 'Những sản phẩm giá tốt cho bạn:',
            'best': 'Sản phẩm bán chạy nhất của chúng tôi:',
            'category': 'Sản phẩm trong danh mục này:',
            'default': 'Những sản phẩm bạn có thể quan tâm:',
        }
        
        bot_message = templates.get(intent, templates['default'])
        
        return JsonResponse({
            'status': 'success',
            'user_message': message,
            'bot_message': bot_message,
            'intent': intent,
            'products': products,
            'retrieval_source': retrieval_source,
            'product_count': len(products),
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def api_categories(request):
    """Get all categories"""
    categories = sorted(set(p['category'] for p in product_db.values()))
    
    return JsonResponse({
        'status': 'success',
        'categories': categories,
        'count': len(categories)
    })

@csrf_exempt
@require_http_methods(["GET"])
def api_product_details(request):
    """Get product details"""
    product_id = request.GET.get('product_id')
    
    try:
        product_id = int(product_id)
    except:
        return JsonResponse({'status': 'error'}, status=400)
    
    if product_id not in product_db:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)
    
    product = product_db[product_id]
    
    return JsonResponse({
        'status': 'success',
        'product': {
            **product,
            'image_url': f'/static/product_{product_id}.jpg'
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_search(request):
    """Search products"""
    try:
        data = json.loads(request.body)
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
                'image_url': f'/static/product_{pid}.jpg'
            }
            for pid in product_ids
        ]
        
        return JsonResponse({
            'status': 'success',
            'query': query,
            'products': products,
            'count': len(products)
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
