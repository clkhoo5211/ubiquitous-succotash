"""Content-related database models (posts, comments, likes, media)"""

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
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ContentStatus(str, enum.Enum):
    """Content moderation status"""

    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    HIDDEN = "hidden"
    DELETED = "deleted"


class MediaType(str, enum.Enum):
    """Supported media types"""

    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"


class Post(Base):
    """Forum post model"""

    __tablename__ = "posts"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("channels.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)  # Sanitized HTML

    # Engagement Metrics
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Moderation
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.ACTIVE, nullable=False, index=True
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="posts")
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        "Like", back_populates="post", cascade="all, delete-orphan"
    )
    media: Mapped[List["Media"]] = relationship(
        "Media", back_populates="post", cascade="all, delete-orphan"
    )
    tags: Mapped[List["PostTag"]] = relationship(
        "PostTag", back_populates="post", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="Report.post_id",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_posts_created_at_desc", created_at.desc()),
        Index("idx_posts_like_count_desc", like_count.desc()),
        Index("idx_posts_user_id_created_at", user_id, created_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title={self.title[:30]}, author_id={self.user_id})>"


class Comment(Base):
    """Comment model with nested reply support"""

    __tablename__ = "comments"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Content
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)  # Sanitized HTML

    # Engagement Metrics
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Moderation
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.ACTIVE, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment", remote_side=[id], back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="parent", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        "Like", back_populates="comment", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="Report.comment_id",
        back_populates="comment",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (Index("idx_comments_post_id_created_at", post_id, created_at),)

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.user_id})>"


class Like(Base):
    """Like model for posts and comments"""

    __tablename__ = "likes"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="likes")
    post: Mapped[Optional["Post"]] = relationship("Post", back_populates="likes")
    comment: Mapped[Optional["Comment"]] = relationship("Comment", back_populates="likes")

    # Indexes (prevent duplicate likes)
    __table_args__ = (
        Index("idx_likes_user_post", user_id, post_id, unique=True),
        Index("idx_likes_user_comment", user_id, comment_id, unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<Like(user_id={self.user_id}, post_id={self.post_id}, comment_id={self.comment_id})>"
        )


class Media(Base):
    """Media attachments for posts (IPFS storage)"""

    __tablename__ = "media"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # File Info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # IPFS Storage
    ipfs_hash: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    ipfs_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post: Mapped[Optional["Post"]] = relationship("Post", back_populates="media")
    uploader: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, file_name={self.file_name}, ipfs_hash={self.ipfs_hash})>"


# Import to avoid circular dependencies
from src.models.moderation import Report  # noqa: E402
from src.models.organization import Channel, PostTag  # noqa: E402
from src.models.user import User  # noqa: E402
