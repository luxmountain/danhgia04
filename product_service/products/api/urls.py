from django.urls import path
from products.api import views

urlpatterns = [
    path("products/", views.product_list),
    path("products/search/", views.product_search),
    path("products/<int:product_id>/", views.product_detail),
]
