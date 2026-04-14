from django.urls import path
from ai_service.api import views

urlpatterns = [
    # Product service
    path("products/", views.product_list),
    path("products/search/", views.product_search),
    path("products/<int:product_id>/", views.product_detail),
    # AI service
    path("track/", views.track_event),
    path("recommend/<int:user_id>/", views.recommend),
    path("similar/<int:product_id>/", views.similar_products),
    path("chat/", views.chat),
]
