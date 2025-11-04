"""Blockchain-related Pydantic schemas"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WalletConnectRequest(BaseModel):
    """Request to connect a wallet"""

    wallet_address: str = Field(..., description="User's BNB Chain wallet address")
    signature: str = Field(..., description="Signature for verification")
    message: str = Field(..., description="Message that was signed")

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, v: str) -> str:
        """Validate Ethereum-compatible address format"""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid wallet address format")
        return v.lower()


class WalletConnectResponse(BaseModel):
    """Response after wallet connection"""

    success: bool
    wallet_address: Optional[str] = None
    message: str


class RewardRedemptionRequest(BaseModel):
    """Request to redeem points for BNB rewards"""

    points_to_redeem: int = Field(..., gt=0, description="Number of points to convert to BNB")
    wallet_address: str = Field(..., description="Destination wallet address")

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet_address(cls, v: str) -> str:
        """Validate Ethereum-compatible address format"""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid wallet address format")
        return v.lower()


class RewardRedemptionResponse(BaseModel):
    """Response after redemption request"""

    success: bool
    transaction_hash: Optional[str] = None
    bnb_amount: Optional[Decimal] = None
    points_redeemed: int
    message: str


class TransactionStatusRequest(BaseModel):
    """Request to check transaction status"""

    transaction_hash: str = Field(..., description="Transaction hash on BNB Chain")

    @field_validator("transaction_hash")
    @classmethod
    def validate_transaction_hash(cls, v: str) -> str:
        """Validate transaction hash format"""
        if not v.startswith("0x") or len(v) != 66:
            raise ValueError("Invalid transaction hash format")
        return v.lower()


class TransactionStatusResponse(BaseModel):
    """Transaction status response"""

    transaction_hash: str
    status: str = Field(..., description="pending, confirmed, failed")
    confirmations: int
    block_number: Optional[int] = None
    bnb_amount: Optional[Decimal] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None


class WalletBalanceResponse(BaseModel):
    """User's wallet balance"""

    wallet_address: str
    bnb_balance: Decimal
    platform_points: int
    conversion_rate: Decimal = Field(..., description="Points per BNB")
