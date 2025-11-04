"""Post service - Business logic for post operations"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import Post, ContentStatus, Like
from src.models.organization import Channel, PostTag
from src.schemas.post import PostCreate, PostUpdate, PostModerationUpdate, PostSortBy
from src.core.exceptions import PostNotFoundError, ChannelNotFoundError, PermissionDeniedError


class PostService:
    """Service for post-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_post(self, post_data: PostCreate, author_id: int) -> Post:
        """Create a new post"""
        # Validate channel exists if provided
        if post_data.channel_id:
            channel_result = await self.db.execute(
                select(Channel).where(Channel.id == post_data.channel_id)
            )
            if not channel_result.scalar_one_or_none():
                raise ChannelNotFoundError(f"Channel with ID {post_data.channel_id} not found")

        # Sanitize HTML (basic implementation - should use bleach or similar)
        body_html = self._sanitize_html(post_data.body)

        # Create post
        new_post = Post(
            user_id=author_id,
            channel_id=post_data.channel_id,
            title=post_data.title,
            body=post_data.body,
            body_html=body_html,
            like_count=0,
            comment_count=0,
            view_count=0,
            status=ContentStatus.ACTIVE,
            is_pinned=False,
            is_locked=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
        )

        self.db.add(new_post)
        await self.db.commit()
        await self.db.refresh(new_post)

        # Add tags if provided
        if post_data.tag_ids:
            for tag_id in post_data.tag_ids:
                post_tag = PostTag(post_id=new_post.id, tag_id=tag_id)
                self.db.add(post_tag)
            await self.db.commit()

        # Load relationships
        await self.db.refresh(new_post, ["author", "channel", "tags"])

        return new_post

    async def get_post_by_id(self, post_id: int, increment_view: bool = False) -> Post:
        """Get post by ID"""
        result = await self.db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.channel),
                selectinload(Post.tags),
                selectinload(Post.media),
            )
            .where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        # Increment view count
        if increment_view:
            post.view_count += 1
            await self.db.commit()

        return post

    async def update_post(self, post_id: int, post_data: PostUpdate, user_id: int) -> Post:
        """Update a post"""
        post = await self.get_post_by_id(post_id)

        # Check ownership
        if post.user_id != user_id:
            raise PermissionDeniedError("You can only edit your own posts")

        # Check if post is locked
        if post.is_locked:
            raise PermissionDeniedError("This post is locked and cannot be edited")

        # Update fields
        if post_data.title is not None:
            post.title = post_data.title
        if post_data.body is not None:
            post.body = post_data.body
            post.body_html = self._sanitize_html(post_data.body)
        if post_data.channel_id is not None:
            # Validate new channel exists
            if post_data.channel_id:
                channel_result = await self.db.execute(
                    select(Channel).where(Channel.id == post_data.channel_id)
                )
                if not channel_result.scalar_one_or_none():
                    raise ChannelNotFoundError(f"Channel with ID {post_data.channel_id} not found")
            post.channel_id = post_data.channel_id

        post.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(post, ["author", "channel", "tags"])

        return post

    async def delete_post(self, post_id: int, user_id: int, is_moderator: bool = False) -> None:
        """Delete a post (soft delete)"""
        post = await self.get_post_by_id(post_id)

        # Check permissions
        if not is_moderator and post.user_id != user_id:
            raise PermissionDeniedError("You can only delete your own posts")

        # Soft delete
        post.status = ContentStatus.DELETED
        post.updated_at = datetime.utcnow()

        await self.db.commit()

    async def moderate_post(self, post_id: int, moderation_data: PostModerationUpdate) -> Post:
        """Moderate a post (moderator only)"""
        post = await self.get_post_by_id(post_id)

        # Update moderation fields
        if moderation_data.status is not None:
            post.status = moderation_data.status
        if moderation_data.is_pinned is not None:
            post.is_pinned = moderation_data.is_pinned
        if moderation_data.is_locked is not None:
            post.is_locked = moderation_data.is_locked

        post.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(post, ["author", "channel", "tags"])

        return post

    async def list_posts(
        self,
        page: int = 1,
        page_size: int = 20,
        channel_id: Optional[int] = None,
        author_id: Optional[int] = None,
        status: Optional[ContentStatus] = ContentStatus.ACTIVE,
        sort_by: PostSortBy = PostSortBy.CREATED_DESC,
        search: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
    ) -> tuple[List[Post], int]:
        """List posts with pagination and filters"""
        query = select(Post).options(
            selectinload(Post.author),
            selectinload(Post.channel),
            selectinload(Post.tags),
            selectinload(Post.media),
        )

        # Apply filters
        if channel_id:
            query = query.where(Post.channel_id == channel_id)
        if author_id:
            query = query.where(Post.user_id == author_id)
        if status:
            query = query.where(Post.status == status)
        if search:
            search_filter = or_(Post.title.ilike(f"%{search}%"), Post.body.ilike(f"%{search}%"))
            query = query.where(search_filter)

        # Filter by tags if provided
        if tag_ids:
            query = query.join(PostTag).where(PostTag.tag_id.in_(tag_ids))

        # Get total count
        count_query = select(func.count()).select_from(Post)
        if channel_id:
            count_query = count_query.where(Post.channel_id == channel_id)
        if author_id:
            count_query = count_query.where(Post.user_id == author_id)
        if status:
            count_query = count_query.where(Post.status == status)
        if search:
            count_query = count_query.where(search_filter)
        if tag_ids:
            count_query = count_query.join(PostTag).where(PostTag.tag_id.in_(tag_ids))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        if sort_by == PostSortBy.CREATED_DESC:
            query = query.order_by(desc(Post.created_at))
        elif sort_by == PostSortBy.CREATED_ASC:
            query = query.order_by(asc(Post.created_at))
        elif sort_by == PostSortBy.POPULAR:
            query = query.order_by(desc(Post.like_count))
        elif sort_by == PostSortBy.TRENDING:
            query = query.order_by(desc(Post.last_activity_at))
        elif sort_by == PostSortBy.COMMENTED:
            query = query.order_by(desc(Post.comment_count))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        posts = result.scalars().unique().all()

        return list(posts), total

    async def check_user_liked_post(self, post_id: int, user_id: int) -> bool:
        """Check if user has liked a post"""
        result = await self.db.execute(
            select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

    def _sanitize_html(self, body: str) -> str:
        """Sanitize HTML content - supports both Markdown and raw HTML"""
        import re

        # Check if body contains HTML tags
        has_html = re.search(r"<[^>]+>", body)

        if has_html:
            # If HTML is detected, use it as-is for interactive content
            # We allow interactive HTML including forms, buttons, canvas, etc.
            # Scripts are allowed for interactivity (user explicitly wants HTML)

            # Return HTML as-is - it will be rendered with |safe in template
            # Note: In production, consider using Content Security Policy (CSP)
            # to restrict script execution for security
            return body
        else:
            # No HTML tags - treat as Markdown and convert
            import html

            escaped = html.escape(body)
            html_content = escaped.replace("\n", "<br>")
            return html_content

    async def update_last_activity(self, post_id: int) -> None:
        """Update post's last activity timestamp (called when new comment added)"""
        post = await self.get_post_by_id(post_id)
        post.last_activity_at = datetime.utcnow()
        await self.db.commit()
