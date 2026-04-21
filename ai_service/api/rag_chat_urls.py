"""
RAG & Chat API URL Routing
"""

from django.urls import path
from .rag_chat_views import (
    start_chat,
    chat_message,
    chat_history,
    recommend_products,
    system_stats
)

urlpatterns = [
    # Chat endpoints
    path('chat/start/', start_chat, name='start_chat'),
    path('chat/message/', chat_message, name='chat_message'),
    path('chat/history/', chat_history, name='chat_history'),
    path('chat/recommend/', recommend_products, name='recommend_products'),
    
    # System endpoints
    path('stats/', system_stats, name='system_stats'),
]
