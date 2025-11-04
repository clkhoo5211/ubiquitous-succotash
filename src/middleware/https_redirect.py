"""HTTPS enforcement middleware

Forces all HTTP requests to redirect to HTTPS in production.
Fixes CRT-003: Missing HTTPS Enforcement (CVSS 9.0)
"""

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import config


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production

    Security Impact:
        - Prevents session cookies from being sent over unencrypted HTTP
        - Protects against man-in-the-middle attacks
        - Enforces TLS/SSL encryption for all communications

    Usage:
        app.add_middleware(HTTPSRedirectMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # Only enforce HTTPS in production
        if config.app.environment == "production":
            # Check if request is HTTP
            if request.url.scheme == "http":
                # Redirect to HTTPS with 301 Moved Permanently
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url), status_code=status.HTTP_301_MOVED_PERMANENTLY)

        # Continue with request
        response = await call_next(request)
        return response
