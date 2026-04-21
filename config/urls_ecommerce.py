"""
Main URL Configuration
Include both RAG Chat and E-Commerce URLs
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # E-Commerce with integrated RAG Chat
    path('', include('ai_service.api.ecommerce_urls')),
    
    # Original RAG Chat API endpoints
    path('api/rag/', include('ai_service.api.rag_chat_urls')),
]
