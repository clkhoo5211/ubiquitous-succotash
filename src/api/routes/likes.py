"""Likes API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.like import (
    LikeResponse,
    LikeListResponse
)
from src.core.dependencies import (
    get_db,
    get_current_user
)
from src.models.user import User
from src.services.like_service import LikeService

router = APIRouter()


@router.post("/posts/{post_id}/like", response_model=LikeResponse, status_code=status.HTTP_201_CREATED, summary="Like a post")
async def like_post(
    post_id: int = Path(..., description="Post ID to like"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Like a post.

    **Requirements:**
    - Must be authenticated
    - Cannot like your own post
    - Cannot like the same post twice

    **Effects:**
    - Increments post's like_count
    - Creates like record
    """
    like_service = LikeService(db)
    like = await like_service.like_post(post_id, current_user.id)
    return like


@router.delete("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT, summary="Unlike a post")
async def unlike_post(
    post_id: int = Path(..., description="Post ID to unlike"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove like from a post.

    **Requirements:**
    - Must have previously liked the post

    **Effects:**
    - Decrements post's like_count
    - Deletes like record
    """
    like_service = LikeService(db)
    await like_service.unlike_post(post_id, current_user.id)
    return None


@router.post("/comments/{comment_id}/like", response_model=LikeResponse, status_code=status.HTTP_201_CREATED, summary="Like a comment")
async def like_comment(
    comment_id: int = Path(..., description="Comment ID to like"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Like a comment.

    **Requirements:**
    - Must be authenticated
    - Cannot like your own comment
    - Cannot like the same comment twice

    **Effects:**
    - Increments comment's like_count
    - Creates like record
    """
    like_service = LikeService(db)
    like = await like_service.like_comment(comment_id, current_user.id)
    return like


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT, summary="Unlike a comment")
async def unlike_comment(
    comment_id: int = Path(..., description="Comment ID to unlike"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove like from a comment.

    **Requirements:**
    - Must have previously liked the comment

    **Effects:**
    - Decrements comment's like_count
    - Deletes like record
    """
    like_service = LikeService(db)
    await like_service.unlike_comment(comment_id, current_user.id)
    return None


@router.get("/posts/{post_id}/likes", response_model=LikeListResponse, summary="Get users who liked a post")
async def get_post_likes(
    post_id: int = Path(..., description="Post ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Likes per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users who liked a post.

    **Returns:**
    - Paginated list of likes with user info
    - Sorted by most recent first
    """
    like_service = LikeService(db)
    likes, total = await like_service.get_post_likes(
        post_id=post_id,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return LikeListResponse(
        likes=likes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/comments/{comment_id}/likes", response_model=LikeListResponse, summary="Get users who liked a comment")
async def get_comment_likes(
    comment_id: int = Path(..., description="Comment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Likes per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users who liked a comment.

    **Returns:**
    - Paginated list of likes with user info
    - Sorted by most recent first
    """
    like_service = LikeService(db)
    likes, total = await like_service.get_comment_likes(
        comment_id=comment_id,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return LikeListResponse(
        likes=likes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}/likes", response_model=LikeListResponse, summary="Get user's likes")
async def get_user_likes(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Likes per page"),
    content_type: Optional[str] = Query(None, description="Filter by content type: 'post' or 'comment'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all content liked by a user.

    **Filters:**
    - `content_type`: Filter by "post" or "comment"

    **Returns:**
    - Paginated list of likes
    - Includes both posts and comments liked by the user
    - Sorted by most recent first
    """
    like_service = LikeService(db)
    likes, total = await like_service.get_user_likes(
        user_id=user_id,
        page=page,
        page_size=page_size,
        content_type=content_type
    )

    total_pages = (total + page_size - 1) // page_size

    return LikeListResponse(
        likes=likes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
