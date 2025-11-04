"""Channel API schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ChannelBase(BaseModel):
    """Base channel schema"""

    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: str = Field("#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class ChannelCreate(ChannelBase):
    """Schema for creating a channel"""

    @validator("name")
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError("Channel name cannot be empty")
        return v.strip()


class ChannelUpdate(BaseModel):
    """Schema for updating a channel"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sort_order: Optional[int] = None


class ChannelResponse(BaseModel):
    """Schema for channel response"""

    id: int
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    color: str
    post_count: int
    subscriber_count: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelListResponse(BaseModel):
    """Schema for channel list"""

    channels: list[ChannelResponse]
    total: int
