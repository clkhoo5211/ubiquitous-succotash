"""Like API schemas for request/response validation"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Request schemas
class LikeCreate(BaseModel):
    """Schema for creating a like"""

    pass  # No fields needed, user_id comes from auth, target from URL


# Response schemas
class LikeUserResponse(BaseModel):
    """Minimal user info for like author"""

    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]

    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    """Schema for like response"""

    id: int
    user_id: int
    post_id: Optional[int]
    comment_id: Optional[int]
    created_at: datetime
    user: LikeUserResponse

    class Config:
        from_attributes = True


class LikeListResponse(BaseModel):
    """Schema for paginated like list"""

    likes: list[LikeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LikeStatsResponse(BaseModel):
    """Schema for like statistics"""

    content_id: int
    content_type: str  # "post" or "comment"
    total_likes: int
    user_has_liked: bool = False
