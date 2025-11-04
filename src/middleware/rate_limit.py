"""Rate limiting middleware

Implements IP-based rate limiting with slowapi and Redis backend.
Fixes HIGH-004: Missing Rate Limiting (CVSS 7.1)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import config

# Create rate limiter with IP-based key function
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],  # Anonymous default from config
    storage_uri=str(config.redis.url).replace("/0", "/1"),  # Use Redis DB 1 for rate limiting
    strategy="fixed-window",  # Fixed window counting strategy
    headers_enabled=True,  # Add rate limit headers to responses
)
