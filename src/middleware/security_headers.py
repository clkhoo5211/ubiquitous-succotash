"""Security headers middleware

Adds comprehensive security headers to all responses.
Fixes HIGH-001: Missing Security Headers (CVSS 7.4)
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses

    Security Headers Added:
        - Content-Security-Policy: Prevents XSS attacks
        - X-Frame-Options: Prevents clickjacking
        - X-Content-Type-Options: Prevents MIME sniffing
        - Referrer-Policy: Controls referrer information
        - Permissions-Policy: Restricts browser features
        - Strict-Transport-Security: Enforces HTTPS (HSTS)
        - X-XSS-Protection: Legacy XSS protection

    Usage:
        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy (prevent XSS)
        # Restricts where resources can be loaded from
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://bsc-dataseed.binance.org https://gateway.lighthouse.storage; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Clickjacking protection
        # Prevents the page from being loaded in an iframe
        response.headers["X-Frame-Options"] = "DENY"

        # MIME sniffing protection
        # Forces browsers to respect the Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer policy
        # Controls how much referrer information is sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature-Policy)
        # Restricts which browser features can be used
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS (HTTP Strict Transport Security) - only for HTTPS
        # Forces browsers to always use HTTPS for this domain
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # XSS protection (legacy but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
