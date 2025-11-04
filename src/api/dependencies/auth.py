"""Authentication dependencies

Provides dependency injection for user authentication and authorization.
"""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import verify_access_token
from src.models.user import User, UserLevelEnum


async def get_current_user(
    session_id: Optional[str] = Cookie(None),
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current authenticated user from session or JWT token

    Args:
        session_id: Session cookie
        authorization: Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    user_id = None

    # Try session cookie first (FIX CRT-002: Use Redis session lookup)
    if session_id:
        # Get user_id from Redis session store
        from src.core.session import get_session

        user_id = await get_session(session_id)

    # Try JWT token
    if not user_id and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            payload = verify_access_token(token)
            if payload:
                user_id = payload.get("sub")

    # Fetch user from database
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.is_active and not user.is_banned:
            return user

    return None


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authenticated user

    Raises:
        HTTPException: If user is not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_moderator(
    current_user: User = Depends(require_auth),
) -> User:
    """Require moderator or higher level (community-driven moderation)

    Raises:
        HTTPException: If user is not a moderator
    """
    moderator_levels = [
        UserLevelEnum.MODERATOR,
        UserLevelEnum.SENIOR_MODERATOR,
    ]
    if current_user.level not in moderator_levels:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required",
        )
    return current_user


async def require_senior_moderator(
    current_user: User = Depends(require_auth),
) -> User:
    """Require senior moderator level (highest level for critical actions)

    Raises:
        HTTPException: If user is not a senior moderator
    """
    if current_user.level != UserLevelEnum.SENIOR_MODERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senior moderator privileges required",
        )
    return current_user
