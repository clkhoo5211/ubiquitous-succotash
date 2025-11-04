"""Points API schemas for request/response validation"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    """Point transaction types"""

    REGISTRATION_BONUS = "registration_bonus"
    CREATE_POST = "create_post"
    CREATE_COMMENT = "create_comment"
    LIKE_CONTENT = "like_content"
    RECEIVE_LIKE = "receive_like"
    CRYPTO_REWARD = "crypto_reward"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    REFUND = "refund"


# Request schemas
class AdminAdjustment(BaseModel):
    """Schema for admin point adjustment"""

    user_id: int = Field(..., description="User ID to adjust points for")
    amount: int = Field(..., description="Point amount (positive or negative)")
    description: str = Field(
        ..., min_length=10, max_length=500, description="Reason for adjustment"
    )


class CryptoRewardRequest(BaseModel):
    """Schema for requesting crypto reward"""

    bnb_wallet_address: str = Field(
        ..., min_length=42, max_length=42, description="BNB wallet address (must start with 0x)"
    )


# Response schemas
class TransactionResponse(BaseModel):
    """Schema for transaction response"""

    id: int
    user_id: int
    amount: int
    transaction_type: TransactionType
    description: str
    reference_type: Optional[str]
    reference_id: Optional[int]
    balance_after: int
    blockchain_tx_hash: Optional[str]
    bnb_amount: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list"""

    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserPointsResponse(BaseModel):
    """Schema for user points summary"""

    user_id: int
    username: str
    current_points: int
    total_earned: int
    total_spent: int
    transactions_count: int
    can_claim_crypto: bool
    crypto_reward_cost: int


class PointEconomyResponse(BaseModel):
    """Schema for point economy configuration"""

    create_post_cost: int
    create_comment_cost: int
    like_cost: int
    registration_bonus: int
    receive_like_tier1: int
    receive_like_tier2: int
    receive_like_tier3: int
    crypto_reward_cost: int
    crypto_reward_bnb_amount: str
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry"""

    rank: int
    user_id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    points: int
    level: str


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard"""

    leaderboard: list[LeaderboardEntry]
    total_users: int
    page: int
    page_size: int
