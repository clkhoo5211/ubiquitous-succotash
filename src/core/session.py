"""Secure session management using Redis

Implements cryptographically secure session tokens with Redis backend.
Fixes CRT-002: Insecure Session Token Generation (CVSS 9.1)
"""

import secrets
from datetime import timedelta
from typing import Optional

from redis.asyncio import Redis

from src.core.config import config

# Global Redis client for sessions
redis_client: Optional[Redis] = None


async def init_redis():
    """Initialize Redis connection for session storage

    Should be called during application startup.
    """
    global redis_client
    redis_client = Redis.from_url(
        str(config.redis.url),
        max_connections=config.redis.max_connections,
        decode_responses=config.redis.decode_responses,
    )


async def close_redis():
    """Close Redis connection

    Should be called during application shutdown.
    """
    if redis_client:
        await redis_client.close()


async def create_session(user_id: int) -> str:
    """Create a new session for a user

    Args:
        user_id: User ID to create session for

    Returns:
        Cryptographically secure session ID (256 bits of entropy)

    Security:
        - Uses secrets.token_urlsafe() for cryptographic randomness
        - Session ID is 43 characters (256 bits of entropy)
        - No predictable components (no user ID, timestamp, etc.)
        - Stored in Redis with automatic expiration
    """
    # Generate cryptographically random session ID (256 bits)
    session_id = secrets.token_urlsafe(32)

    # Store user_id in Redis with automatic expiration
    await redis_client.setex(
        f"session:{session_id}",
        timedelta(hours=config.security.session_expiration_hours),
        user_id,
    )

    return session_id


async def get_session(session_id: str) -> Optional[int]:
    """Get user ID from session ID

    Args:
        session_id: Session ID from cookie

    Returns:
        User ID if session is valid, None if expired or invalid
    """
    if not session_id or not redis_client:
        return None

    user_id = await redis_client.get(f"session:{session_id}")
    return int(user_id) if user_id else None


async def delete_session(session_id: str) -> bool:
    """Delete a session (logout)

    Args:
        session_id: Session ID to delete

    Returns:
        True if session was deleted, False if it didn't exist
    """
    if not session_id or not redis_client:
        return False

    result = await redis_client.delete(f"session:{session_id}")
    return result > 0


async def refresh_session(session_id: str) -> bool:
    """Refresh session expiration time

    Args:
        session_id: Session ID to refresh

    Returns:
        True if session was refreshed, False if it doesn't exist
    """
    if not session_id or not redis_client:
        return False

    # Extend TTL without changing the value
    result = await redis_client.expire(
        f"session:{session_id}",
        timedelta(hours=config.security.session_expiration_hours),
    )
    return result


async def invalidate_user_sessions(user_id: int) -> int:
    """Invalidate all sessions for a user

    Useful for logout all devices, password reset, account suspension, etc.

    Args:
        user_id: User ID whose sessions to invalidate

    Returns:
        Number of sessions invalidated
    """
    if not redis_client:
        return 0

    # Find all session keys for this user
    # Note: This is potentially slow for large numbers of sessions
    # Consider maintaining a user_id -> session_ids mapping for better performance
    cursor = 0
    deleted = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match="session:*", count=100)
        for key in keys:
            value = await redis_client.get(key)
            if value and int(value) == user_id:
                await redis_client.delete(key)
                deleted += 1
        if cursor == 0:
            break

    return deleted


async def get_session_count(user_id: int) -> int:
    """Get number of active sessions for a user

    Args:
        user_id: User ID to check

    Returns:
        Number of active sessions
    """
    if not redis_client:
        return 0

    cursor = 0
    count = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match="session:*", count=100)
        for key in keys:
            value = await redis_client.get(key)
            if value and int(value) == user_id:
                count += 1
        if cursor == 0:
            break

    return count
