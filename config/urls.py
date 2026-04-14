from django.urls import path, include

urlpatterns = [
    path("api/", include("ai_service.api.urls")),
]
