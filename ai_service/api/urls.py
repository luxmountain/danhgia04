from django.urls import path
from ai_service.api import views
from ai_service.api import integration_views

urlpatterns = [
    path("track/", views.track_event),
    path("recommend/<int:user_id>/", views.recommend),
    path("similar/<int:product_id>/", views.similar_products),
    path("chat/", views.chat),
    # Behavior KB_Graph endpoints
    path("behavior/chat/", views.behavior_chat),
    path("behavior/segment/<int:user_id>/", views.user_segment),
    path("behavior/recommend/<int:user_id>/", views.behavior_recommend),
    # E-commerce integration
    path("integration/search/", integration_views.integration_search),
    path("integration/cart/<int:user_id>/", integration_views.integration_cart),
    path("integration/chat-ui/", integration_views.chat_ui),
]
