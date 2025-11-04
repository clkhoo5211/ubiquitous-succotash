"""Post API schemas for request/response validation"""

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
class PostBase(BaseModel):
    """Base post schema with common fields"""

    title: str = Field(..., min_length=3, max_length=300)
    body: str = Field(..., min_length=10, max_length=50000)
    channel_id: Optional[int] = None


# Request schemas
class PostCreate(PostBase):
    """Schema for creating a new post"""

    tag_ids: Optional[List[int]] = Field(default=[], description="List of tag IDs to attach")

    @validator("title")
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @validator("body")
    def body_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Body cannot be empty")
        return v.strip()


class PostUpdate(BaseModel):
    """Schema for updating an existing post"""

    title: Optional[str] = Field(None, min_length=3, max_length=300)
    body: Optional[str] = Field(None, min_length=10, max_length=50000)
    channel_id: Optional[int] = None

    @validator("title")
    def title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else v

    @validator("body")
    def body_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Body cannot be empty")
        return v.strip() if v else v


class PostModerationUpdate(BaseModel):
    """Schema for moderator actions on posts"""

    status: Optional[ContentStatus] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None


# Response schemas
class PostAuthorResponse(BaseModel):
    """Minimal user info for post author"""

    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    level: str

    class Config:
        from_attributes = True


class PostChannelResponse(BaseModel):
    """Minimal channel info for post"""

    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class PostTagResponse(BaseModel):
    """Tag info for post"""

    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Schema for post response"""

    id: int
    title: str
    body: str
    body_html: str
    author: PostAuthorResponse
    channel: Optional[PostChannelResponse]
    like_count: int
    comment_count: int
    view_count: int
    status: ContentStatus
    is_pinned: bool
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    tags: List[PostTagResponse] = []

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Schema for paginated post list"""

    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PostDetailResponse(PostResponse):
    """Schema for detailed post response (includes additional metadata)"""

    user_has_liked: Optional[bool] = False  # Whether current user liked this post

    class Config:
        from_attributes = True


# Filter/Query schemas
class PostSortBy(str, Enum):
    """Post sorting options"""

    CREATED_DESC = "created_desc"
    CREATED_ASC = "created_asc"
    POPULAR = "popular"  # By like_count
    TRENDING = "trending"  # By recent activity
    COMMENTED = "commented"  # By comment_count
