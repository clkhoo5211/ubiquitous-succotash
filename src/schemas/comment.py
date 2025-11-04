"""Comment API schemas for request/response validation"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ContentStatus(str, Enum):
    """Content moderation status"""
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    HIDDEN = "hidden"
    DELETED = "deleted"


# Base schemas
class CommentBase(BaseModel):
    """Base comment schema"""
    body: str = Field(..., min_length=1, max_length=10000)
    parent_id: Optional[int] = Field(None, description="Parent comment ID for nested replies")


# Request schemas
class CommentCreate(CommentBase):
    """Schema for creating a new comment"""

    @validator("body")
    def body_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Comment body cannot be empty")
        return v.strip()


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    body: str = Field(..., min_length=1, max_length=10000)

    @validator("body")
    def body_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Comment body cannot be empty")
        return v.strip()


class CommentModerationUpdate(BaseModel):
    """Schema for moderator actions on comments"""
    status: ContentStatus


# Response schemas
class CommentAuthorResponse(BaseModel):
    """Minimal user info for comment author"""
    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    level: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: int
    post_id: int
    parent_id: Optional[int]
    body: str
    body_html: str
    author: CommentAuthorResponse
    like_count: int
    status: ContentStatus
    created_at: datetime
    updated_at: datetime
    replies_count: int = 0  # Number of direct replies
    user_has_liked: Optional[bool] = False  # Whether current user liked this comment

    class Config:
        from_attributes = True


class CommentWithRepliesResponse(CommentResponse):
    """Schema for comment with nested replies"""
    replies: List["CommentWithRepliesResponse"] = []

    class Config:
        from_attributes = True


# Enable forward references for recursive model
CommentWithRepliesResponse.model_rebuild()


class CommentListResponse(BaseModel):
    """Schema for paginated comment list"""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CommentTreeResponse(BaseModel):
    """Schema for comment tree (with nested replies)"""
    comments: List[CommentWithRepliesResponse]
    total_root_comments: int
