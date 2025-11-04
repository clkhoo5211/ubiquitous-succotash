"""Moderation API schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ReportReason(str, Enum):
    """Report reasons"""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    NSFW = "nsfw"
    MISINFORMATION = "misinformation"
    COPYRIGHT = "copyright"
    OTHER = "other"


class ReportStatus(str, Enum):
    """Report status"""

    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ReportCreate(BaseModel):
    """Create a report"""

    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: ReportReason
    description: Optional[str] = Field(None, max_length=1000)


class ReportResolve(BaseModel):
    """Resolve a report"""

    status: ReportStatus
    moderator_notes: Optional[str] = Field(None, max_length=1000)
    resolution: Optional[str] = Field(None, max_length=1000)


class ReportResponse(BaseModel):
    """Report response"""

    id: int
    reporter_id: int
    post_id: Optional[int]
    comment_id: Optional[int]
    reason: ReportReason
    description: Optional[str]
    status: ReportStatus
    moderator_notes: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by_id: Optional[int]

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Paginated reports"""

    reports: list[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BanCreate(BaseModel):
    """Ban a user"""

    user_id: int
    reason: str = Field(..., min_length=10, max_length=500)
    duration_days: Optional[int] = Field(None, description="None = permanent ban")


class BanResponse(BaseModel):
    """Ban response"""

    id: int
    user_id: int
    banned_by_id: int
    reason: str
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
