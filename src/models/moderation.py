"""Moderation-related database models (reports, bans)"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ReportStatus(str, enum.Enum):
    """Report moderation status"""

    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ReportReason(str, enum.Enum):
    """Reasons for reporting content"""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    NSFW = "nsfw"
    MISINFORMATION = "misinformation"
    COPYRIGHT = "copyright"
    OTHER = "other"


class Report(Base):
    """Content report model"""

    __tablename__ = "reports"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    reporter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Report Details
    reason: Mapped[ReportReason] = mapped_column(Enum(ReportReason), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True
    )

    # Review Details
    moderator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    reporter: Mapped["User"] = relationship(
        "User", foreign_keys=[reporter_id], back_populates="reports_made"
    )
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
    post: Mapped[Optional["Post"]] = relationship("Post", back_populates="reports")
    comment: Mapped[Optional["Comment"]] = relationship("Comment", back_populates="reports")

    # Indexes
    __table_args__ = (
        Index("idx_reports_status_created_at", status, created_at),
        Index("idx_reports_reporter_id_created_at", reporter_id, created_at),
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, reason={self.reason}, status={self.status})>"


class Ban(Base):
    """User ban model"""

    __tablename__ = "bans"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    banned_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )

    # Ban Details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Duration
    banned_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # NULL = permanent

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    lifted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lifted_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    banned_user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="bans"
    )
    banned_by: Mapped["User"] = relationship("User", foreign_keys=[banned_by_id])
    lifted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[lifted_by_id])

    # Indexes
    __table_args__ = (
        Index("idx_bans_user_id_created_at", user_id, created_at),
        Index("idx_bans_banned_until", banned_until),
    )

    def __repr__(self) -> str:
        return f"<Ban(user_id={self.user_id}, banned_until={self.banned_until})>"


# Import to avoid circular dependencies
from src.models.content import Comment, Post  # noqa: E402
from src.models.user import User  # noqa: E402
