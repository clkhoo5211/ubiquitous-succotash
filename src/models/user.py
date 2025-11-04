"""User-related database models"""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class UserLevelEnum(str, enum.Enum):
    """User level progression based on points (no admin - community-driven moderation)"""

    NEW_USER = "new_user"  # 0-99 points
    ACTIVE_USER = "active_user"  # 100-499 points
    TRUSTED_USER = "trusted_user"  # 500-1,999 points
    MODERATOR = "moderator"  # 2,000-9,999 points
    SENIOR_MODERATOR = "senior_moderator"  # 10,000+ points (highest level)


class OAuth2Provider(str, enum.Enum):
    """Supported OAuth2 providers"""

    META = "meta"
    REDDIT = "reddit"
    TWITTER = "twitter"
    DISCORD = "discord"
    TELEGRAM = "telegram"


class User(Base):
    """User account model"""

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Profile
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Gamification
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    level: Mapped[UserLevelEnum] = mapped_column(
        Enum(UserLevelEnum), default=UserLevelEnum.NEW_USER, nullable=False
    )

    # Blockchain
    bnb_wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42), nullable=True, unique=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[List["Post"]] = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        "Like", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    reports_made: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="Report.reporter_id",
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    bans: Mapped[List["Ban"]] = relationship(
        "Ban",
        foreign_keys="Ban.user_id",
        back_populates="banned_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, level={self.level})>"


class OAuthAccount(Base):
    """OAuth2 provider account linkage"""

    __tablename__ = "oauth_accounts"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # OAuth Data
    provider: Mapped[OAuth2Provider] = mapped_column(
        Enum(OAuth2Provider), nullable=False, index=True
    )
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Profile Data from OAuth provider
    oauth_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    oauth_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oauth_avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    # Constraints
    __table_args__ = (UniqueConstraint("provider", "oauth_id", name="unique_provider_oauth_id"),)

    def __repr__(self) -> str:
        return f"<OAuthAccount(provider={self.provider}, oauth_id={self.oauth_id})>"


class Level(Base):
    """User level/tier configuration"""

    __tablename__ = "levels"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Level Info
    name: Mapped[UserLevelEnum] = mapped_column(Enum(UserLevelEnum), unique=True, nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color

    # Permissions (stored as JSON)
    can_create_posts: Mapped[bool] = mapped_column(Boolean, default=True)
    can_create_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    can_like: Mapped[bool] = mapped_column(Boolean, default=True)
    can_report: Mapped[bool] = mapped_column(Boolean, default=False)
    can_moderate: Mapped[bool] = mapped_column(Boolean, default=False)
    can_ban: Mapped[bool] = mapped_column(Boolean, default=False)
    can_edit_others_posts: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Level(name={self.name}, min_points={self.min_points})>"


# Import to avoid circular dependencies
from src.models.content import Comment, Like, Post  # noqa: E402
from src.models.moderation import Ban, Report  # noqa: E402
from src.models.points import Transaction  # noqa: E402
