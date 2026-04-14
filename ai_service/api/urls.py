from django.urls import path
from ai_service.api import views

urlpatterns = [
    path("track/", views.track_event),
    path("recommend/<int:user_id>/", views.recommend),
    path("similar/<int:product_id>/", views.similar_products),
    path("chat/", views.chat),
]
