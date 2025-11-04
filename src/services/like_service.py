"""Like service - Business logic for like operations"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import Like, Post, Comment
from src.models.points import TransactionType
from src.core.exceptions import (
    PostNotFoundError,
    CommentNotFoundError,
    DuplicateLikeError,
    SelfLikeError,
    ValidationError,
)


class LikeService:
    """Service for like-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def like_post(self, post_id: int, user_id: int) -> Like:
        """Like a post"""
        from src.services.point_service import PointService
        from src.models.user import User

        # Verify post exists
        post_result = await self.db.execute(select(Post).where(Post.id == post_id))
        post = post_result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        # Check if user is trying to like their own post
        if post.user_id == user_id:
            raise SelfLikeError("You cannot like your own post")

        # Check if already liked
        existing_like = await self.db.execute(
            select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
        )
        if existing_like.scalar_one_or_none():
            raise DuplicateLikeError("You have already liked this post")

        # Get point service and economy config
        point_service = PointService(self.db)
        config = await point_service.get_economy_config()

        # Deduct like cost from liker
        try:
            await point_service.create_transaction(
                user_id=user_id,
                amount=config.like_cost,  # -1 point
                transaction_type=TransactionType.LIKE_CONTENT,
                description=f"Liked post {post_id}",
                reference_type="post",
                reference_id=post_id,
            )
        except Exception as e:
            raise ValidationError(f"Failed to process like transaction: {str(e)}")

        # Award like reward to post author (get updated author with new points)
        post_author_result = await self.db.execute(select(User).where(User.id == post.user_id))
        post_author = post_author_result.scalar_one()

        # Calculate reward based on like count tiers
        reward_amount = config.receive_like_tier1  # Default: +3 points
        if post_author.points >= 1000:
            reward_amount = config.receive_like_tier2  # +30 points for high reputation
        elif post.like_count + 1 >= 100:
            reward_amount = config.receive_like_tier3  # +350 points for viral post

        await point_service.create_transaction(
            user_id=post.user_id,
            amount=reward_amount,
            transaction_type=TransactionType.RECEIVE_LIKE,
            description=f"Received like on post {post_id}",
            reference_type="post",
            reference_id=post_id,
        )

        # Create like
        new_like = Like(
            user_id=user_id, post_id=post_id, comment_id=None, created_at=datetime.utcnow()
        )

        self.db.add(new_like)

        # Increment post like count
        post.like_count += 1

        await self.db.commit()
        await self.db.refresh(new_like, ["user"])

        return new_like

    async def unlike_post(self, post_id: int, user_id: int) -> None:
        """Unlike a post"""
        # Find the like
        like_result = await self.db.execute(
            select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
        )
        like = like_result.scalar_one_or_none()

        if not like:
            raise ValidationError("You have not liked this post")

        # Get post and decrement like count
        post_result = await self.db.execute(select(Post).where(Post.id == post_id))
        post = post_result.scalar_one_or_none()
        if post and post.like_count > 0:
            post.like_count -= 1

        # Delete the like
        await self.db.delete(like)
        await self.db.commit()

    async def like_comment(self, comment_id: int, user_id: int) -> Like:
        """Like a comment"""
        # Verify comment exists
        comment_result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = comment_result.scalar_one_or_none()
        if not comment:
            raise CommentNotFoundError(f"Comment with ID {comment_id} not found")

        # Check if user is trying to like their own comment
        if comment.user_id == user_id:
            raise SelfLikeError("You cannot like your own comment")

        # Check if already liked
        existing_like = await self.db.execute(
            select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
        )
        if existing_like.scalar_one_or_none():
            raise DuplicateLikeError("You have already liked this comment")

        # Create like
        new_like = Like(
            user_id=user_id, post_id=None, comment_id=comment_id, created_at=datetime.utcnow()
        )

        self.db.add(new_like)

        # Increment comment like count
        comment.like_count += 1

        await self.db.commit()
        await self.db.refresh(new_like, ["user"])

        return new_like

    async def unlike_comment(self, comment_id: int, user_id: int) -> None:
        """Unlike a comment"""
        # Find the like
        like_result = await self.db.execute(
            select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
        )
        like = like_result.scalar_one_or_none()

        if not like:
            raise ValidationError("You have not liked this comment")

        # Get comment and decrement like count
        comment_result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = comment_result.scalar_one_or_none()
        if comment and comment.like_count > 0:
            comment.like_count -= 1

        # Delete the like
        await self.db.delete(like)
        await self.db.commit()

    async def get_post_likes(
        self, post_id: int, page: int = 1, page_size: int = 50
    ) -> tuple[List[Like], int]:
        """Get users who liked a post"""
        query = select(Like).options(selectinload(Like.user))
        query = query.where(Like.post_id == post_id)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(Like).where(Like.post_id == post_id)
        )
        total = count_result.scalar()

        # Sort by created_at desc (most recent first)
        query = query.order_by(Like.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        likes = result.scalars().all()

        return list(likes), total

    async def get_comment_likes(
        self, comment_id: int, page: int = 1, page_size: int = 50
    ) -> tuple[List[Like], int]:
        """Get users who liked a comment"""
        query = select(Like).options(selectinload(Like.user))
        query = query.where(Like.comment_id == comment_id)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(Like).where(Like.comment_id == comment_id)
        )
        total = count_result.scalar()

        # Sort by created_at desc (most recent first)
        query = query.order_by(Like.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        likes = result.scalars().all()

        return list(likes), total

    async def get_user_likes(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
        content_type: Optional[str] = None,  # "post" or "comment"
    ) -> tuple[List[Like], int]:
        """Get all likes by a user"""
        query = select(Like).options(
            selectinload(Like.user), selectinload(Like.post), selectinload(Like.comment)
        )
        query = query.where(Like.user_id == user_id)

        # Filter by content type
        if content_type == "post":
            query = query.where(Like.post_id.isnot(None))
        elif content_type == "comment":
            query = query.where(Like.comment_id.isnot(None))

        # Get total count
        count_query = select(func.count()).select_from(Like).where(Like.user_id == user_id)
        if content_type == "post":
            count_query = count_query.where(Like.post_id.isnot(None))
        elif content_type == "comment":
            count_query = count_query.where(Like.comment_id.isnot(None))

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Sort by created_at desc
        query = query.order_by(Like.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        likes = result.scalars().all()

        return list(likes), total
