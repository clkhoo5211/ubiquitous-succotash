"""Comments API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentModerationUpdate,
    CommentResponse,
    CommentListResponse,
    CommentTreeResponse,
    ContentStatus
)
from src.core.dependencies import (
    get_db,
    get_current_user,
    get_optional_current_user,
    require_moderator
)
from src.models.user import User
from src.services.comment_service import CommentService

router = APIRouter()


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, summary="Create a comment")
async def create_comment(
    post_id: int = Path(..., description="Post ID to comment on"),
    comment_data: CommentCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new comment on a post.

    **Required fields:**
    - `body`: Comment content (1-10000 characters)

    **Optional fields:**
    - `parent_id`: Parent comment ID for nested replies

    **Notes:**
    - Cannot comment on locked posts
    - Parent comment must belong to the same post
    """
    comment_service = CommentService(db)
    new_comment = await comment_service.create_comment(post_id, comment_data, current_user.id)

    # Add replies_count for response
    new_comment.replies_count = 0
    new_comment.user_has_liked = False

    return new_comment


@router.get("/{post_id}/comments", response_model=CommentListResponse, summary="List comments for a post")
async def list_comments(
    post_id: int = Path(..., description="Post ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Comments per page"),
    parent_id: Optional[int] = Query(None, description="Parent comment ID (null for root comments)"),
    status: Optional[ContentStatus] = Query(ContentStatus.ACTIVE, description="Filter by status"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List comments for a post with pagination.

    **Filters:**
    - `parent_id`: null for root comments, specific ID for replies to that comment
    - `status`: Filter by status (ACTIVE, PENDING_REVIEW, HIDDEN, DELETED)

    **Returns:**
    - Flat list of comments (use `/tree` endpoint for nested structure)
    - Sorted by creation time (oldest first)
    """
    comment_service = CommentService(db)
    comments, total = await comment_service.list_comments(
        post_id=post_id,
        page=page,
        page_size=page_size,
        parent_id=parent_id,
        status=status
    )

    # Add metadata for each comment
    for comment in comments:
        comment.replies_count = await comment_service.get_replies_count(comment.id)
        if current_user:
            comment.user_has_liked = await comment_service.check_user_liked_comment(
                comment.id, current_user.id
            )
        else:
            comment.user_has_liked = False

    total_pages = (total + page_size - 1) // page_size

    return CommentListResponse(
        comments=comments,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{post_id}/comments/tree", response_model=CommentTreeResponse, summary="Get comment tree")
async def get_comment_tree(
    post_id: int = Path(..., description="Post ID"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get nested comment tree for a post (up to 5 levels deep).

    **Returns:**
    - Root comments with nested replies
    - All active comments organized in tree structure
    - Sorted by creation time (oldest first)

    **Use case:**
    - Displaying full comment threads with replies
    - Better UX than flat pagination for discussions
    """
    comment_service = CommentService(db)
    root_comments = await comment_service.get_comment_tree(post_id, max_depth=5)

    # Recursively add metadata
    async def add_metadata(comment):
        if current_user:
            comment.user_has_liked = await comment_service.check_user_liked_comment(
                comment.id, current_user.id
            )
        else:
            comment.user_has_liked = False

        if hasattr(comment, 'replies_list'):
            for reply in comment.replies_list:
                await add_metadata(reply)

    for comment in root_comments:
        await add_metadata(comment)

    return CommentTreeResponse(
        comments=root_comments,
        total_root_comments=len(root_comments)
    )


@router.get("/comments/{comment_id}", response_model=CommentResponse, summary="Get comment by ID")
async def get_comment_by_id(
    comment_id: int = Path(..., description="Comment ID"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific comment by its ID.

    **Returns:**
    - Comment details
    - Whether current user has liked it (if authenticated)
    """
    comment_service = CommentService(db)
    comment = await comment_service.get_comment_by_id(comment_id)

    # Add metadata
    comment.replies_count = await comment_service.get_replies_count(comment_id)
    if current_user:
        comment.user_has_liked = await comment_service.check_user_liked_comment(
            comment_id, current_user.id
        )
    else:
        comment.user_has_liked = False

    return comment


@router.patch("/comments/{comment_id}", response_model=CommentResponse, summary="Update a comment")
async def update_comment(
    comment_id: int = Path(..., description="Comment ID"),
    comment_data: CommentUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing comment.

    **Requirements:**
    - Only the comment author can update their own comments

    **Updatable fields:**
    - `body`: Comment content
    """
    comment_service = CommentService(db)
    updated_comment = await comment_service.update_comment(comment_id, comment_data, current_user.id)

    # Add metadata
    updated_comment.replies_count = await comment_service.get_replies_count(comment_id)
    updated_comment.user_has_liked = await comment_service.check_user_liked_comment(
        comment_id, current_user.id
    )

    return updated_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a comment")
async def delete_comment(
    comment_id: int = Path(..., description="Comment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a comment (soft delete - marks as DELETED status).

    **Requirements:**
    - Only the comment author or moderators can delete comments

    **Effects:**
    - Decrements post's comment count
    - Nested replies remain visible
    """
    from src.models.user import UserLevelEnum

    is_moderator = current_user.level in [UserLevelEnum.MODERATOR, UserLevelEnum.SENIOR_MODERATOR]

    comment_service = CommentService(db)
    await comment_service.delete_comment(comment_id, current_user.id, is_moderator=is_moderator)
    return None


@router.patch("/comments/{comment_id}/moderate", response_model=CommentResponse, summary="Moderate a comment")
async def moderate_comment(
    comment_id: int = Path(..., description="Comment ID"),
    moderation_data: CommentModerationUpdate = ...,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db)
):
    """
    Moderate a comment (moderator only).

    **Moderation actions:**
    - `status`: Change status (ACTIVE, PENDING_REVIEW, HIDDEN, DELETED)
    """
    comment_service = CommentService(db)
    moderated_comment = await comment_service.moderate_comment(comment_id, moderation_data)

    # Add metadata
    moderated_comment.replies_count = await comment_service.get_replies_count(comment_id)
    moderated_comment.user_has_liked = False

    return moderated_comment
