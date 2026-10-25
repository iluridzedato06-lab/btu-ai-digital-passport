from rest_framework.views import exception_handler


def handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": getattr(exc, "default_code", "error"), "detail": str(response.data["detail"])}
    return response
