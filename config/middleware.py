from django.conf import settings

# App pages: no inline scripts. Inline style attributes remain in templates (style-src 'unsafe-inline'; style
# injection is far lower risk than script). Origins: Bootstrap (jsDelivr, SRI-pinned) and Google Charts (gstatic).
APP_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://cdn.jsdelivr.net https://www.gstatic.com",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.gstatic.com",
    "img-src 'self' data:",
    "font-src 'self' data: https://cdn.jsdelivr.net",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

# Jazzmin's admin templates rely on inline <script> blocks and Google Fonts, so /admin/ cannot run the strict
# script policy. It still blocks plugins, framing, <base> hijacking and foreign form targets.
# ponytail: admin keeps 'unsafe-inline' scripts; tighten only if Jazzmin drops inline scripts or admin is re-themed.
ADMIN_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data:",
    "font-src 'self' data: https://fonts.gstatic.com",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


class ContentSecurityPolicyMiddleware:
    """Adds Content-Security-Policy (or -Report-Only when CSP_REPORT_ONLY=True) to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        header = 'Content-Security-Policy-Report-Only' if settings.CSP_REPORT_ONLY else 'Content-Security-Policy'
        if header not in response:
            response[header] = ADMIN_POLICY if request.path.startswith('/admin/') else APP_POLICY
        return response
