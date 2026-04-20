import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse


def health_check(request):
    return JsonResponse({"status": "ok", "service": "gateway"})


def _proxy(request, upstream_base, upstream_path):
    """Forward request to upstream service, return its response."""
    url = f"{upstream_base}/{upstream_path}"
    if request.META.get("QUERY_STRING"):
        url += f"?{request.META['QUERY_STRING']}"

    headers = {
        k: v for k, v in {
            "Content-Type": request.content_type,
            "Accept": request.headers.get("Accept"),
        }.items() if v
    }

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.body if request.body else None,
            timeout=settings.PROXY_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Service unavailable"}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Service timeout"}, status=504)

    response = HttpResponse(
        content=resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("Content-Type", "application/json"),
    )
    return response


def proxy_product_service(request, path=""):
    upstream_path = f"api/products/{path}"
    return _proxy(request, settings.PRODUCT_SERVICE_URL, upstream_path)


def proxy_ai_service(request, path=""):
    upstream_path = f"api/{path}"
    return _proxy(request, settings.AI_SERVICE_URL, upstream_path)
