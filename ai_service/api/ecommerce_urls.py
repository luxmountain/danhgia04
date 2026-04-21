"""
E-Commerce Integration URLs
"""

from django.urls import path
from .ecommerce_views import (
    home,
    products_list,
    product_detail,
    cart,
    rag_chat_api,
    api_categories,
    api_product_details,
    api_search,
)

urlpatterns = [
    # Pages
    path('', home, name='home'),
    path('products/', products_list, name='products'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('cart/', cart, name='cart'),
    
    # APIs
    path('api/chat/', rag_chat_api, name='rag_chat'),
    path('api/categories/', api_categories, name='api_categories'),
    path('api/product/', api_product_details, name='api_product'),
    path('api/search/', api_search, name='api_search'),
]
