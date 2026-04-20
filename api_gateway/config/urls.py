from django.urls import path, re_path
from gateway.views import proxy_product_service, proxy_ai_service, health_check

urlpatterns = [
    path("health/", health_check),
    re_path(r"^api/products/(?P<path>.*)$", proxy_product_service),
    re_path(r"^api/ai/(?P<path>.*)$", proxy_ai_service),
]
