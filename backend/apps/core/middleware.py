class SecurityHeadersMiddleware:
    """Adds conservative security headers to every API / admin response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.path.startswith("/api/"):
            response.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            response.setdefault("Cache-Control", "no-store")
        return response
