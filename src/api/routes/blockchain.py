"""Blockchain API routes (BNB Chain integration)

Handles:
- Wallet connection and verification
- Points-to-BNB redemption
- Transaction status tracking
- Wallet balance queries
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import require_auth
from src.core.database import get_db
from src.core.exceptions import BlockchainError, InsufficientPointsError
from src.models.user import User
from src.schemas.blockchain import (
    RewardRedemptionRequest,
    RewardRedemptionResponse,
    TransactionStatusRequest,
    TransactionStatusResponse,
    WalletBalanceResponse,
    WalletConnectRequest,
    WalletConnectResponse,
)
from src.services.blockchain_service import blockchain_service

router = APIRouter()


@router.post("/wallet/connect", response_model=WalletConnectResponse)
async def connect_wallet(
    wallet_request: WalletConnectRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Connect and verify user's BNB Chain wallet

    Requires signature verification to prove wallet ownership.

    **Process:**
    1. User signs a message with their private key
    2. Backend verifies signature matches wallet address
    3. Wallet address is saved to user profile

    **Example message to sign:**
    "Connect wallet to Decentralized Forum - Nonce: {user_id}_{timestamp}"
    """
    try:
        result = await blockchain_service.connect_wallet(db, current_user, wallet_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect wallet: {str(e)}",
        )


@router.delete("/wallet/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_wallet(
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the user's BNB Chain wallet"""
    from datetime import datetime
    from sqlalchemy import select
    
    try:
        # Get fresh user object in current session
        result = await db.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one()
        
        user.bnb_wallet_address = None
        user.updated_at = datetime.utcnow()
        await db.commit()
        
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect wallet: {str(e)}"
        )


@router.get("/wallet/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get user's wallet balance and platform points

    Returns:
    - On-chain BNB balance
    - Platform points balance
    - Current conversion rate (points per BNB)
    """
    try:
        balance_info = await blockchain_service.get_user_wallet_info(db, current_user)
        return balance_info
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch wallet balance: {str(e)}",
        )


@router.post("/rewards/redeem", response_model=RewardRedemptionResponse)
async def redeem_rewards(
    redemption_request: RewardRedemptionRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Redeem platform points for BNB rewards

    **Requirements:**
    - Minimum 10,000 points for redemption
    - Connected wallet address
    - Sufficient points balance

    **Process:**
    1. Validates point balance
    2. Calculates BNB amount (conversion rate: 1000 points = 1 BNB)
    3. Sends BNB to user's wallet
    4. Deducts points from user's account

    **Note:** Transactions are processed asynchronously. Use `/transaction/status`
    to check transaction confirmation.
    """
    try:
        transaction_hash, bnb_amount = await blockchain_service.redeem_points_for_bnb(
            db=db,
            user=current_user,
            points_to_redeem=redemption_request.points_to_redeem,
            wallet_address=redemption_request.wallet_address,
        )

        return RewardRedemptionResponse(
            success=True,
            transaction_hash=transaction_hash,
            bnb_amount=bnb_amount,
            points_redeemed=redemption_request.points_to_redeem,
            message=f"Successfully redeemed {redemption_request.points_to_redeem} points "
            f"for {bnb_amount} BNB. Transaction: {transaction_hash}",
        )

    except InsufficientPointsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redemption failed: {str(e)}",
        )


@router.post("/transaction/status", response_model=TransactionStatusResponse)
async def get_transaction_status(
    tx_request: TransactionStatusRequest,
    current_user: User = Depends(require_auth),
):
    """Get status of a blockchain transaction

    **Statuses:**
    - `pending`: Transaction submitted but not yet mined
    - `confirmed`: Transaction confirmed on blockchain
    - `failed`: Transaction failed (reverted)
    - `unknown`: Transaction not found

    **Confirmations:**
    Number of blocks mined after transaction. Generally:
    - 12+ confirmations: Safe to consider final on BNB Chain
    - 1-11 confirmations: Transaction confirmed but still confirming
    - 0 confirmations: Transaction pending
    """
    try:
        status_info = await blockchain_service.get_transaction_status(tx_request.transaction_hash)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction status: {str(e)}",
        )


@router.get("/conversion-rate")
async def get_conversion_rate():
    """Get current points-to-BNB conversion rate

    Returns the exchange rate for converting platform points to BNB.

    **Current Rate:** 1000 points = 1 BNB
    """
    return {
        "points_per_bnb": int(blockchain_service.conversion_rate),
        "bnb_per_point": float(1 / blockchain_service.conversion_rate),
        "minimum_redemption_points": blockchain_service.min_redemption_points,
    }
