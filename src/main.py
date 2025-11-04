"""Main FastAPI application entry point

Decentralized Autonomous Forum Platform
- Point economy with crypto rewards
- OAuth2 authentication (5 providers)
- IPFS decentralized storage
- BNB Chain integration
- Community-driven moderation
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.routes import (
    auth,
    users,
    posts,
    comments,
    likes,
    points,
    blockchain,
    media,
    moderation,
    search,
    channels,
    tags,
)
from src.routes import frontend
from src.core.config import config
from src.core.database import init_db, close_db
from src.core.session import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager

    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Decentralized Forum...")
    print(f"   Environment: {config.app.environment}")
    print(f"   Debug Mode: {config.app.debug}")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Initialize Redis for sessions
    await init_redis()
    print("✅ Redis session store initialized")

    yield

    # Shutdown
    print("🛑 Shutting down Decentralized Forum...")
    await close_db()
    print("✅ Database connections closed")

    await close_redis()
    print("✅ Redis connections closed")


# Create FastAPI application with enhanced docs
app = FastAPI(
    title="Decentralized Autonomous Forum API",
    description="""
## 🚀 Decentralized Forum Platform API

A modern decentralized forum with blockchain rewards, gamification, and community-driven moderation.

### Key Features
* **Authentication** - OAuth2 with Meta, Reddit, Twitter, Discord, Telegram
* **Posts & Comments** - Create, read, update with rich media support
* **Gamification** - Point economy with crypto rewards
* **Blockchain** - BNB Chain integration for rewards
* **Moderation** - Community-driven content moderation
* **Search** - Full-text search across all content
* **Channels** - Organized discussion channels

### Base URL
```
http://localhost:8000
```

### Version
1.0.0
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    swagger_ui_parameters={
        "deepLinking": True,
        "displayOperationId": False,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "syntaxHighlight": True,
        "requestSnippetsEnabled": True,
    },
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers (FIX HIGH-001: Add comprehensive security headers)
from src.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)

# HTTPS Redirect (FIX CRT-003: Enforce HTTPS in production)
from src.middleware.https_redirect import HTTPSRedirectMiddleware

if config.app.environment == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host (production only)
if config.app.environment == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.app.allowed_hosts)

# Rate Limiting (FIX HIGH-004: Prevent brute force and DoS)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.middleware.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# STATIC FILES & TEMPLATES
# ============================================================================

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Jinja2 Templates with custom configuration
templates = Jinja2Templates(directory="templates")


# Add custom Jinja2 filters and globals
def format_number(value):
    """Format number with thousand separators"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value


def truncate_text(text, length=100, suffix="..."):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix


def time_ago(dt):
    """Convert datetime to relative time string"""
    from datetime import datetime, timezone

    if not dt:
        return ""

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds / 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'


# Register custom filters
templates.env.filters["format_number"] = format_number
templates.env.filters["number_format"] = format_number  # Alias
templates.env.filters["truncate"] = truncate_text
templates.env.filters["time_ago"] = time_ago
templates.env.filters["timeago"] = time_ago  # Alias for template compatibility

# Add global functions
templates.env.globals["url_for"] = lambda name, **path_params: app.url_path_for(name, **path_params)
templates.env.globals["get_flashed_messages"] = (
    lambda with_categories=False: []
)  # Placeholder for flash messages


# ============================================================================
# ROUTES
# ============================================================================


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": config.app.environment,
        "version": "1.0.0",
    }


# API v1 routes
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{API_V1_PREFIX}/users", tags=["Users"])
app.include_router(posts.router, prefix=f"{API_V1_PREFIX}/posts", tags=["Posts"])
app.include_router(comments.router, prefix=f"{API_V1_PREFIX}/comments", tags=["Comments"])
app.include_router(likes.router, prefix=f"{API_V1_PREFIX}/likes", tags=["Likes"])
app.include_router(points.router, prefix=f"{API_V1_PREFIX}/points", tags=["Points"])
app.include_router(blockchain.router, prefix=f"{API_V1_PREFIX}/blockchain", tags=["Blockchain"])
app.include_router(media.router, prefix=f"{API_V1_PREFIX}/media", tags=["Media"])
app.include_router(moderation.router, prefix=f"{API_V1_PREFIX}/moderation", tags=["Moderation"])
app.include_router(search.router, prefix=f"{API_V1_PREFIX}/search", tags=["Search"])
app.include_router(channels.router, prefix=f"{API_V1_PREFIX}/channels", tags=["Channels"])
app.include_router(tags.router, prefix=f"{API_V1_PREFIX}/tags", tags=["Tags"])

# Frontend (HTML) routes - must come AFTER API routes
app.include_router(frontend.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.app.debug,
        log_level="info" if config.app.debug else "warning",
    )
