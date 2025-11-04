"""Authentication service"""

from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserLevelEnum
from src.schemas.auth import UserRegister, UserLogin
from src.core.security import hash_password, verify_password, create_access_token
from src.core.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from src.services.point_service import PointService


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserRegister) -> User:
        """Register a new user"""
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

        # Award registration bonus
        point_service = PointService(self.db)
        await point_service.award_registration_bonus(new_user.id)

        # Refresh user to get updated points
        await self.db.refresh(new_user)

        return new_user

    async def login(self, login_data: UserLogin) -> tuple[User, str]:
        """Login user and return user + access token"""
        # Find user by username or email
        user_result = await self.db.execute(
            select(User).where(
                or_(User.username == login_data.username, User.email == login_data.username)
            )
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise InvalidCredentialsError("Invalid username/email or password")

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsError("Invalid username/email or password")

        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive")

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # Generate access token
        access_token = create_access_token(data={"sub": str(user.id), "username": user.username})

        return user, access_token

    async def get_user_by_token(self, user_id: int) -> User:
        """Get user by ID from token"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        if not user.is_active:
            raise InvalidCredentialsError("Account is inactive")

        return user
