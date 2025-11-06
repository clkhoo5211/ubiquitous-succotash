"""Tag API schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TagBase(BaseModel):
    """Base tag schema"""

    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    color: str = Field("#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Schema for creating a tag"""

    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip()


class TagUpdate(BaseModel):
    """Schema for updating a tag"""

    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    """Schema for tag response"""

    id: int
    name: str
    slug: str
    description: Optional[str]
    color: str
    post_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    """Schema for tag list"""

    tags: list[TagResponse]
    total: int
