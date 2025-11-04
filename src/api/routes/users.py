"""Users API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import (
    UserResponse,
    UserDetailResponse,
    UserUpdate,
    UserPasswordChange,
    UserEmailChange,
    UserListResponse,
    UserStatsResponse
)
from src.core.dependencies import (
    get_db
)
from src.api.dependencies.auth import require_auth
from src.models.user import User, UserLevelEnum
from src.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserDetailResponse, summary="Get current user profile")
async def get_current_user_profile(
    current_user: User = Depends(require_auth)
):
    """
    Get the authenticated user's detailed profile.

    Returns private information like email, wallet address, etc.
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public profile of a user by their ID.

    Returns only public information (username, display name, bio, avatar, points, level).
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    return user


@router.get("/", response_model=UserListResponse, summary="List users")
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of users per page"),
    search: Optional[str] = Query(None, description="Search by username or display name"),
    level: Optional[UserLevelEnum] = Query(None, description="Filter by user level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List users with pagination and optional filters.

    **Filters:**
    - `search`: Search by username or display name (case-insensitive)
    - `level`: Filter by user level (NEW_USER, ACTIVE_USER, TRUSTED_USER, MODERATOR, SENIOR_MODERATOR)
    - `is_active`: Filter by active status

    **Pagination:**
    - `page`: Page number (default: 1)
    - `page_size`: Users per page (default: 20, max: 100)
    """
    user_service = UserService(db)
    users, total = await user_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        level=level,
        is_active=is_active
    )

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/me", response_model=UserDetailResponse, summary="Update current user profile")
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the authenticated user's profile.

    **Updatable fields:**
    - `display_name`: User's display name
    - `bio`: User biography
    - `avatar_url`: Avatar image URL
    - `bnb_wallet_address`: BNB Chain wallet address (must start with 0x and be 42 chars)
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_data)
    return updated_user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT, summary="Change password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the authenticated user's password.

    **Requirements:**
    - Must provide current password
    - New password must be at least 8 characters
    - New password must contain uppercase, lowercase, and digit
    """
    user_service = UserService(db)
    await user_service.change_password(current_user.id, password_data)
    return None


@router.post("/me/change-email", response_model=UserDetailResponse, summary="Change email")
async def change_email(
    email_data: UserEmailChange,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the authenticated user's email address.

    **Requirements:**
    - Must provide password for verification
    - New email must not be in use by another user
    - Email will be marked as unverified after change
    """
    user_service = UserService(db)
    updated_user = await user_service.change_email(current_user.id, email_data)
    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete account")
async def delete_account(
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate) the authenticated user's account.

    This is a soft delete - account is marked as inactive but data is retained.
    """
    user_service = UserService(db)
    await user_service.delete_user(current_user.id)
    return None


@router.get("/{user_id}/stats", response_model=UserStatsResponse, summary="Get user statistics")
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for a user.

    **Statistics include:**
    - Total posts and comments
    - Total likes received and given
    - Current points and level
    - Account age in days
    - Activity this month
    """
    user_service = UserService(db)
    stats = await user_service.get_user_stats(user_id)
    return stats
