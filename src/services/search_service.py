"""Search service"""

from typing import List, Tuple
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import Post, Comment, ContentStatus
from src.models.user import User


class SearchService:
    """Service for search operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_posts(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """Search posts by title and body"""
        search_filter = or_(Post.title.ilike(f"%{query}%"), Post.body.ilike(f"%{query}%"))

        stmt = (
            select(Post)
            .options(selectinload(Post.author), selectinload(Post.channel), selectinload(Post.tags))
            .where(search_filter, Post.status == ContentStatus.ACTIVE)
        )

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(Post)
            .where(search_filter, Post.status == ContentStatus.ACTIVE)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Sort by relevance (title matches first) then by created_at
        stmt = stmt.order_by(Post.created_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        posts = result.scalars().unique().all()

        return list(posts), total

    async def search_users(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[User], int]:
        """Search users by username and display name"""
        search_filter = or_(
            User.username.ilike(f"%{query}%"), User.display_name.ilike(f"%{query}%")
        )

        stmt = select(User).where(search_filter, User.is_active)

        # Get total count
        count_stmt = select(func.count()).select_from(User).where(search_filter, User.is_active)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Sort by points (most popular first)
        stmt = stmt.order_by(User.points.desc())

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return list(users), total

    async def search_comments(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Comment], int]:
        """Search comments by body"""
        search_filter = Comment.body.ilike(f"%{query}%")

        stmt = (
            select(Comment)
            .options(selectinload(Comment.author))
            .where(search_filter, Comment.status == ContentStatus.ACTIVE)
        )

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(Comment)
            .where(search_filter, Comment.status == ContentStatus.ACTIVE)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Sort by created_at desc
        stmt = stmt.order_by(Comment.created_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        comments = result.scalars().all()

        return list(comments), total
