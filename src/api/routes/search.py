"""Search API routes"""

import re
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.post import PostListResponse
from src.schemas.user import UserListResponse
from src.schemas.comment import CommentListResponse
from src.core.dependencies import get_db
from src.services.search_service import SearchService

router = APIRouter()


def strip_html(text):
    """Remove HTML tags from text"""
    if not text:
        return text
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    import html

    text = html.unescape(text)
    return text


@router.get("/posts", response_model=PostListResponse, summary="Search posts")
async def search_posts(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search posts by title and body content.

    **Query parameter:**
    - `q`: Search term (minimum 2 characters)

    **Returns:**
    - Posts matching the search query
    - Sorted by relevance and recency
    """
    search_service = SearchService(db)
    posts, total = await search_service.search_posts(q, page, page_size)

    total_pages = (total + page_size - 1) // page_size

    return PostListResponse(
        posts=posts, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/users", response_model=UserListResponse, summary="Search users")
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search users by username and display name.

    **Query parameter:**
    - `q`: Search term (minimum 2 characters)

    **Returns:**
    - Users matching the search query
    - Sorted by points (popularity)
    """
    search_service = SearchService(db)
    users, total = await search_service.search_users(q, page, page_size)

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        users=users, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/comments", response_model=CommentListResponse, summary="Search comments")
async def search_comments(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search comments by body content.

    **Query parameter:**
    - `q`: Search term (minimum 2 characters)

    **Returns:**
    - Comments matching the search query
    - Sorted by recency
    """
    search_service = SearchService(db)
    comments, total = await search_service.search_comments(q, page, page_size)

    total_pages = (total + page_size - 1) // page_size

    return CommentListResponse(
        comments=comments, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("", summary="Unified search across posts, users, and comments")
async def unified_search(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified search across posts, users, and comments.

    **Query parameter:**
    - `q`: Search term (minimum 2 characters)

    **Returns:**
    - Mixed results from posts, users, and comments
    """
    search_service = SearchService(db)

    # Search all types
    posts, _ = await search_service.search_posts(q, 1, 5)
    users, _ = await search_service.search_users(q, 1, 5)
    comments, _ = await search_service.search_comments(q, 1, 5)

    # Format results for frontend
    results = []

    for post in posts[:3]:
        body_text = strip_html(post.body) if post.body else ""
        excerpt = body_text[:150] + "..." if len(body_text) > 150 else body_text
        results.append(
            {"title": post.title, "excerpt": excerpt, "url": f"/posts/{post.id}", "type": "post"}
        )

    # Don't include users in search results for privacy/security
    # Users can search for users by username on profile pages instead

    return results
