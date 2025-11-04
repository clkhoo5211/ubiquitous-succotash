"""User API schemas for request/response validation"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserLevelEnum(str, Enum):
    """User level enumeration"""

    NEW_USER = "NEW_USER"
    ACTIVE_USER = "ACTIVE_USER"
    TRUSTED_USER = "TRUSTED_USER"
    MODERATOR = "MODERATOR"
    SENIOR_MODERATOR = "SENIOR_MODERATOR"


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bnb_wallet_address: Optional[str] = Field(None, max_length=42)

    @validator("username")
    def username_alphanumeric(cls, v):
        if v and not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (can include _ and -)")
        return v

    @validator("bnb_wallet_address")
    def validate_bnb_address(cls, v):
        # Allow None/empty for disconnect, but validate if value provided
        if v and v != "" and (not v.startswith("0x") or len(v) != 42):
            raise ValueError("Invalid BNB wallet address format")
        # Return None for empty string to normalize
        return v if v and v != "" else None


# Request schemas
class UserCreate(UserBase):
    """Schema for user registration"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bnb_wallet_address: Optional[str] = Field(default=None, max_length=42)

    @validator("bnb_wallet_address")
    def validate_bnb_address(cls, v):
        # Allow None/empty for disconnect, but validate if value provided
        if v and v != "" and (not v.startswith("0x") or len(v) != 42):
            raise ValueError("Invalid BNB wallet address format")
        # Return None for empty string to normalize
        return v if v and v != "" else None

    class Config:
        # Allow setting fields to None explicitly (for disconnect)
        validate_assignment = False


class UserPasswordChange(BaseModel):
    """Schema for password change"""

    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserEmailChange(BaseModel):
    """Schema for email change"""

    new_email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


# Response schemas
class UserResponse(BaseModel):
    """Schema for user response (public profile)"""

    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    points: int
    level: UserLevelEnum
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Schema for detailed user response (private profile)"""

    email: Optional[EmailStr]
    bnb_wallet_address: Optional[str]
    email_verified: bool
    last_login_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list"""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Statistics schema
class UserStatsResponse(BaseModel):
    """Schema for user statistics"""

    user_id: int
    username: str
    total_posts: int
    total_comments: int
    total_likes_received: int
    total_likes_given: int
    points: int
    level: UserLevelEnum
    account_age_days: int
    posts_this_month: int
    comments_this_month: int

    class Config:
        from_attributes = True
