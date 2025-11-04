"""Posts API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.post import (
    PostCreate,
    PostUpdate,
    PostModerationUpdate,
    PostResponse,
    PostDetailResponse,
    PostListResponse,
    PostSortBy,
    ContentStatus
)
from src.core.dependencies import (
    get_db,
    get_current_user,
    get_optional_current_user,
    require_moderator
)
from src.models.user import User
from src.services.post_service import PostService

router = APIRouter()


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="Create a post")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post.

    **Required fields:**
    - `title`: Post title (3-300 characters)
    - `body`: Post content (10-50000 characters)

    **Optional fields:**
    - `channel_id`: Channel to post in (must exist)
    - `tag_ids`: List of tag IDs to attach to the post
    """
    post_service = PostService(db)
    new_post = await post_service.create_post(post_data, current_user.id)
    return new_post


@router.get("/{post_id}", response_model=PostDetailResponse, summary="Get post by ID")
async def get_post_by_id(
    post_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a post by its ID.

    Increments the view count automatically.
    If authenticated, includes whether the current user has liked the post.
    """
    post_service = PostService(db)
    post = await post_service.get_post_by_id(post_id, increment_view=True)

    # Check if current user liked this post
    user_has_liked = False
    if current_user:
        user_has_liked = await post_service.check_user_liked_post(post_id, current_user.id)

    # Create response with user_has_liked field
    post_dict = {
        **post.__dict__,
        "user_has_liked": user_has_liked
    }

    return post_dict


@router.get("/", response_model=PostListResponse, summary="List posts")
async def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Posts per page"),
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    status: Optional[ContentStatus] = Query(ContentStatus.ACTIVE, description="Filter by status"),
    sort_by: PostSortBy = Query(PostSortBy.CREATED_DESC, description="Sort order"),
    search: Optional[str] = Query(None, description="Search in title and body"),
    tag_ids: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    db: AsyncSession = Depends(get_db)
):
    """
    List posts with pagination and filters.

    **Filters:**
    - `channel_id`: Filter by channel
    - `author_id`: Filter by author
    - `status`: Filter by status (ACTIVE, PENDING_REVIEW, HIDDEN, DELETED)
    - `search`: Search in title and body (case-insensitive)
    - `tag_ids`: Filter by tags (comma-separated IDs, e.g., "1,2,3")

    **Sorting:**
    - `created_desc`: Newest first (default)
    - `created_asc`: Oldest first
    - `popular`: Most liked
    - `trending`: Recent activity
    - `commented`: Most commented
    """
    # Parse tag_ids
    tag_ids_list = None
    if tag_ids:
        try:
            tag_ids_list = [int(tag_id.strip()) for tag_id in tag_ids.split(",")]
        except ValueError:
            tag_ids_list = None

    post_service = PostService(db)
    posts, total = await post_service.list_posts(
        page=page,
        page_size=page_size,
        channel_id=channel_id,
        author_id=author_id,
        status=status,
        sort_by=sort_by,
        search=search,
        tag_ids=tag_ids_list
    )

    total_pages = (total + page_size - 1) // page_size

    return PostListResponse(
        posts=posts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/{post_id}", response_model=PostResponse, summary="Update a post")
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing post.

    Only the post author can update their own posts.
    Locked posts cannot be edited.

    **Updatable fields:**
    - `title`: Post title
    - `body`: Post content
    - `channel_id`: Channel (must exist)
    """
    post_service = PostService(db)
    updated_post = await post_service.update_post(post_id, post_data, current_user.id)
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a post")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post (soft delete - marks as DELETED status).

    Only the post author or moderators can delete posts.
    """
    from src.models.user import UserLevelEnum

    is_moderator = current_user.level in [UserLevelEnum.MODERATOR, UserLevelEnum.SENIOR_MODERATOR]

    post_service = PostService(db)
    await post_service.delete_post(post_id, current_user.id, is_moderator=is_moderator)
    return None


@router.patch("/{post_id}/moderate", response_model=PostResponse, summary="Moderate a post")
async def moderate_post(
    post_id: int,
    moderation_data: PostModerationUpdate,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db)
):
    """
    Moderate a post (moderator only).

    **Moderation actions:**
    - `status`: Change status (ACTIVE, PENDING_REVIEW, HIDDEN, DELETED)
    - `is_pinned`: Pin/unpin post
    - `is_locked`: Lock/unlock post (prevents editing)
    """
    post_service = PostService(db)
    moderated_post = await post_service.moderate_post(post_id, moderation_data)
    return moderated_post
