"""Organization models (channels, tags)"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Channel(Base):
    """Forum channel/category model"""

    __tablename__ = "channels"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Channel Info
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Emoji or icon name
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")  # Hex color

    # Metrics
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Display Order
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="channel")

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name={self.name}, slug={self.slug})>"


class Tag(Base):
    """Post tag model"""

    __tablename__ = "tags"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Tag Info
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6B7280")  # Hex color

    # Metrics
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post_tags: Mapped[List["PostTag"]] = relationship(
        "PostTag", back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"


class PostTag(Base):
    """Many-to-many relationship between posts and tags"""

    __tablename__ = "post_tags"

    # Composite Primary Key
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="post_tags")

    # Indexes
    __table_args__ = (Index("idx_post_tags_tag_id", tag_id),)

    def __repr__(self) -> str:
        return f"<PostTag(post_id={self.post_id}, tag_id={self.tag_id})>"


# Import to avoid circular dependencies
from src.models.content import Post  # noqa: E402
