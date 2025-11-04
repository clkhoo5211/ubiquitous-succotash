"""Comment service - Business logic for comment operations"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import Comment, ContentStatus, Post, Like
from src.schemas.comment import CommentCreate, CommentUpdate, CommentModerationUpdate
from src.core.exceptions import (
    CommentNotFoundError,
    PostNotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class CommentService:
    """Service for comment-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(
        self, post_id: int, comment_data: CommentCreate, author_id: int
    ) -> Comment:
        """Create a new comment on a post"""
        # Verify post exists
        post_result = await self.db.execute(select(Post).where(Post.id == post_id))
        post = post_result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        # Check if post is locked
        if post.is_locked:
            raise PermissionDeniedError("This post is locked and cannot receive comments")

        # If parent_id provided, verify parent comment exists and belongs to same post
        if comment_data.parent_id:
            parent_result = await self.db.execute(
                select(Comment).where(Comment.id == comment_data.parent_id)
            )
            parent_comment = parent_result.scalar_one_or_none()
            if not parent_comment:
                raise CommentNotFoundError(
                    f"Parent comment with ID {comment_data.parent_id} not found"
                )
            if parent_comment.post_id != post_id:
                raise ValidationError("Parent comment does not belong to this post")

        # Sanitize HTML
        body_html = self._sanitize_html(comment_data.body)

        # Create comment
        new_comment = Comment(
            post_id=post_id,
            user_id=author_id,
            parent_id=comment_data.parent_id,
            body=comment_data.body,
            body_html=body_html,
            like_count=0,
            status=ContentStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(new_comment)

        # Update post comment count and last_activity_at
        post.comment_count += 1
        post.last_activity_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(new_comment, ["author", "post"])

        return new_comment

    async def get_comment_by_id(self, comment_id: int) -> Comment:
        """Get comment by ID"""
        result = await self.db.execute(
            select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise CommentNotFoundError(f"Comment with ID {comment_id} not found")

        return comment

    async def update_comment(
        self, comment_id: int, comment_data: CommentUpdate, user_id: int
    ) -> Comment:
        """Update a comment"""
        comment = await self.get_comment_by_id(comment_id)

        # Check ownership
        if comment.user_id != user_id:
            raise PermissionDeniedError("You can only edit your own comments")

        # Update content
        comment.body = comment_data.body
        comment.body_html = self._sanitize_html(comment_data.body)
        comment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment, ["author"])

        return comment

    async def delete_comment(
        self, comment_id: int, user_id: int, is_moderator: bool = False
    ) -> None:
        """Delete a comment (soft delete)"""
        comment = await self.get_comment_by_id(comment_id)

        # Check permissions
        if not is_moderator and comment.user_id != user_id:
            raise PermissionDeniedError("You can only delete your own comments")

        # Soft delete
        comment.status = ContentStatus.DELETED
        comment.updated_at = datetime.utcnow()

        # Decrement post comment count
        post_result = await self.db.execute(select(Post).where(Post.id == comment.post_id))
        post = post_result.scalar_one_or_none()
        if post and post.comment_count > 0:
            post.comment_count -= 1

        await self.db.commit()

    async def moderate_comment(
        self, comment_id: int, moderation_data: CommentModerationUpdate
    ) -> Comment:
        """Moderate a comment (moderator only)"""
        comment = await self.get_comment_by_id(comment_id)

        # Update status
        comment.status = moderation_data.status
        comment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment, ["author"])

        return comment

    async def list_comments(
        self,
        post_id: int,
        page: int = 1,
        page_size: int = 50,
        parent_id: Optional[int] = None,
        status: Optional[ContentStatus] = ContentStatus.ACTIVE,
    ) -> tuple[List[Comment], int]:
        """List comments for a post with pagination"""
        query = select(Comment).options(selectinload(Comment.author))

        # Filter by post
        query = query.where(Comment.post_id == post_id)

        # Filter by parent (for nested replies)
        if parent_id is None:
            # Get only root comments (no parent)
            query = query.where(Comment.parent_id.is_(None))
        else:
            # Get replies to a specific comment
            query = query.where(Comment.parent_id == parent_id)

        # Filter by status
        if status:
            query = query.where(Comment.status == status)

        # Get total count
        count_query = select(func.count()).select_from(Comment)
        count_query = count_query.where(Comment.post_id == post_id)
        if parent_id is None:
            count_query = count_query.where(Comment.parent_id.is_(None))
        else:
            count_query = count_query.where(Comment.parent_id == parent_id)
        if status:
            count_query = count_query.where(Comment.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Sort by created_at (oldest first for better thread reading)
        query = query.order_by(Comment.created_at.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def get_comment_tree(self, post_id: int, max_depth: int = 5) -> List[Comment]:
        """Get nested comment tree for a post (up to max_depth levels)"""
        # Get all active comments for the post
        result = await self.db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(and_(Comment.post_id == post_id, Comment.status == ContentStatus.ACTIVE))
            .order_by(Comment.created_at.asc())
        )
        all_comments = result.scalars().all()

        # Build comment tree structure
        comment_dict = {comment.id: comment for comment in all_comments}
        root_comments = []

        for comment in all_comments:
            # Add replies list to each comment (for response schema)
            if not hasattr(comment, "replies_list"):
                comment.replies_list = []
            if not hasattr(comment, "replies_count"):
                comment.replies_count = 0

            if comment.parent_id is None:
                root_comments.append(comment)
            elif comment.parent_id in comment_dict:
                parent = comment_dict[comment.parent_id]
                if not hasattr(parent, "replies_list"):
                    parent.replies_list = []
                parent.replies_list.append(comment)
                parent.replies_count = len(parent.replies_list)

        return root_comments

    async def check_user_liked_comment(self, comment_id: int, user_id: int) -> bool:
        """Check if user has liked a comment"""
        result = await self.db.execute(
            select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

    async def get_replies_count(self, comment_id: int) -> int:
        """Get count of direct replies to a comment"""
        result = await self.db.execute(
            select(func.count())
            .select_from(Comment)
            .where(and_(Comment.parent_id == comment_id, Comment.status == ContentStatus.ACTIVE))
        )
        return result.scalar()

    def _sanitize_html(self, body: str) -> str:
        """Sanitize HTML content (basic implementation)"""
        # TODO: Implement proper HTML sanitization using bleach library
        import html

        escaped = html.escape(body)
        html_content = escaped.replace("\n", "<br>")
        return html_content
