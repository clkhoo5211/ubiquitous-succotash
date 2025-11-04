"""User service - Business logic for user operations"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserLevelEnum
from src.models.content import Post, Comment, Like
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserEmailChange,
    UserStatsResponse,
)
from src.core.security import hash_password, verify_password
from src.core.exceptions import UserAlreadyExistsError, UserNotFoundError, InvalidCredentialsError


class UserService:
    """Service for user-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if email already exists
        existing_email = await self.db.execute(select(User).where(User.email == user_data.email))
        if existing_email.scalar_one_or_none():
            raise UserAlreadyExistsError(f"Email {user_data.email} already registered")

        # Check if username already exists
        existing_username = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing_username.scalar_one_or_none():
            raise UserAlreadyExistsError(f"Username {user_data.username} already taken")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash,
            display_name=user_data.display_name or user_data.username,
            bio=user_data.bio,
            avatar_url=user_data.avatar_url,
            points=0,
            level=UserLevelEnum.NEW_USER,
            is_active=True,
            email_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        return user

    async def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError(f"User {username} not found")

        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError(f"User with email {email} not found")

        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user profile"""
        user = await self.get_user_by_id(user_id)

        # Update fields
        if user_data.display_name is not None:
            user.display_name = user_data.display_name
        if user_data.bio is not None:
            user.bio = user_data.bio
        if user_data.avatar_url is not None:
            user.avatar_url = user_data.avatar_url

        # Update wallet address if provided in request (including None to disconnect)
        # In Pydantic v2, None values are included in model_dump(exclude_unset=True)
        # So we check if the field was explicitly provided by checking user_data object
        try:
            update_fields = user_data.model_dump(exclude_unset=True)
        except AttributeError:
            update_fields = user_data.dict(exclude_unset=True)

        if "bnb_wallet_address" in update_fields:
            user.bnb_wallet_address = update_fields["bnb_wallet_address"]

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(self, user_id: int, password_data: UserPasswordChange) -> None:
        """Change user password"""
        user = await self.get_user_by_id(user_id)

        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")

        # Hash and set new password
        user.password_hash = hash_password(password_data.new_password)
        user.updated_at = datetime.utcnow()

        await self.db.commit()

    async def change_email(self, user_id: int, email_data: UserEmailChange) -> User:
        """Change user email"""
        user = await self.get_user_by_id(user_id)

        # Verify password
        if not verify_password(email_data.password, user.password_hash):
            raise InvalidCredentialsError("Password is incorrect")

        # Check if new email already exists
        existing_email = await self.db.execute(
            select(User).where(and_(User.email == email_data.new_email, User.id != user_id))
        )
        if existing_email.scalar_one_or_none():
            raise UserAlreadyExistsError(f"Email {email_data.new_email} already in use")

        # Update email and mark as unverified
        user.email = email_data.new_email
        user.email_verified = False
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_user(self, user_id: int) -> None:
        """Soft delete user (deactivate account)"""
        user = await self.get_user_by_id(user_id)

        user.is_active = False
        user.updated_at = datetime.utcnow()

        await self.db.commit()

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        level: Optional[UserLevelEnum] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """List users with pagination and filters"""
        query = select(User)

        # Apply filters
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"), User.display_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        if level:
            query = query.where(User.level == level)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(User)
        if search:
            count_query = count_query.where(search_filter)
        if level:
            count_query = count_query.where(User.level == level)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(User.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def get_user_stats(self, user_id: int) -> UserStatsResponse:
        """Get user statistics"""
        user = await self.get_user_by_id(user_id)

        # Count posts
        posts_count = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.user_id == user_id)
        )
        total_posts = posts_count.scalar()

        # Count comments
        comments_count = await self.db.execute(
            select(func.count()).select_from(Comment).where(Comment.user_id == user_id)
        )
        total_comments = comments_count.scalar()

        # Count likes received on posts
        likes_received_posts = await self.db.execute(
            select(func.count()).select_from(Like).join(Post).where(Post.user_id == user_id)
        )
        likes_posts = likes_received_posts.scalar() or 0

        # Count likes received on comments
        likes_received_comments = await self.db.execute(
            select(func.count()).select_from(Like).join(Comment).where(Comment.user_id == user_id)
        )
        likes_comments = likes_received_comments.scalar() or 0

        total_likes_received = likes_posts + likes_comments

        # Count likes given
        likes_given = await self.db.execute(
            select(func.count()).select_from(Like).where(Like.user_id == user_id)
        )
        total_likes_given = likes_given.scalar()

        # Calculate account age
        account_age_days = (datetime.utcnow() - user.created_at).days

        # Posts/comments this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        posts_this_month = await self.db.execute(
            select(func.count())
            .select_from(Post)
            .where(and_(Post.user_id == user_id, Post.created_at >= month_start))
        )
        posts_month = posts_this_month.scalar()

        comments_this_month = await self.db.execute(
            select(func.count())
            .select_from(Comment)
            .where(and_(Comment.user_id == user_id, Comment.created_at >= month_start))
        )
        comments_month = comments_this_month.scalar()

        return UserStatsResponse(
            user_id=user.id,
            username=user.username,
            total_posts=total_posts,
            total_comments=total_comments,
            total_likes_received=total_likes_received,
            total_likes_given=total_likes_given,
            points=user.points,
            level=user.level,
            account_age_days=account_age_days,
            posts_this_month=posts_month,
            comments_this_month=comments_month,
        )

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        user = await self.get_user_by_id(user_id)
        user.last_login = datetime.utcnow()
        await self.db.commit()
