"""Points economy API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.points import (
    TransactionResponse,
    TransactionListResponse,
    UserPointsResponse,
    PointEconomyResponse,
    LeaderboardResponse,
    AdminAdjustment,
    CryptoRewardRequest,
    TransactionType
)
from src.core.dependencies import (
    get_db,
    get_current_user,
    require_senior_moderator
)
from src.models.user import User
from src.services.point_service import PointService

router = APIRouter()


@router.get("/me/points", response_model=UserPointsResponse, summary="Get my points summary")
async def get_my_points(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the authenticated user's points summary.

    **Returns:**
    - Current points balance
    - Total points earned
    - Total points spent
    - Transaction count
    - Whether user can claim crypto reward
    """
    point_service = PointService(db)
    summary = await point_service.get_user_points_summary(current_user.id)
    return summary


@router.get("/users/{user_id}/points", response_model=UserPointsResponse, summary="Get user points summary")
async def get_user_points(
    user_id: int = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user's points summary (public view).

    **Returns:**
    - Current points balance
    - Total points earned
    - Total points spent
    - Transaction count
    """
    point_service = PointService(db)
    summary = await point_service.get_user_points_summary(user_id)
    return summary


@router.get("/me/transactions", response_model=TransactionListResponse, summary="Get my transaction history")
async def get_my_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Transactions per page"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the authenticated user's transaction history.

    **Filters:**
    - `transaction_type`: Filter by type (REGISTRATION_BONUS, CREATE_POST, etc.)

    **Returns:**
    - Paginated list of transactions
    - Sorted by most recent first
    """
    point_service = PointService(db)
    transactions, total = await point_service.get_user_transactions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type
    )

    total_pages = (total + page_size - 1) // page_size

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}/transactions", response_model=TransactionListResponse, summary="Get user transaction history")
async def get_user_transactions(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Transactions per page"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user's transaction history (public view).

    **Filters:**
    - `transaction_type`: Filter by type

    **Returns:**
    - Paginated list of transactions
    - Sorted by most recent first
    """
    point_service = PointService(db)
    transactions, total = await point_service.get_user_transactions(
        user_id=user_id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type
    )

    total_pages = (total + page_size - 1) // page_size

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/economy", response_model=PointEconomyResponse, summary="Get point economy configuration")
async def get_economy_config(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the point economy configuration.

    **Returns:**
    - Point costs for actions (create post, comment, like)
    - Point rewards (registration bonus, receiving likes)
    - Crypto reward costs and amounts
    """
    point_service = PointService(db)
    config = await point_service.get_economy_config()
    return config


@router.get("/leaderboard", response_model=LeaderboardResponse, summary="Get points leaderboard")
async def get_leaderboard(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Users per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the points leaderboard.

    **Returns:**
    - Top users ranked by points
    - User details (username, avatar, level)
    - Current rank and points
    """
    point_service = PointService(db)
    leaderboard, total = await point_service.get_leaderboard(
        page=page,
        page_size=page_size
    )

    return LeaderboardResponse(
        leaderboard=leaderboard,
        total_users=total,
        page=page,
        page_size=page_size
    )


@router.post("/claim-crypto", response_model=TransactionResponse, summary="Claim crypto reward")
async def claim_crypto_reward(
    reward_request: CryptoRewardRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Claim crypto reward by exchanging points for BNB.

    **Requirements:**
    - Must have enough points (default: 10,000 points)
    - Must provide valid BNB wallet address

    **Effects:**
    - Deducts points from user account
    - Sends BNB to wallet address (requires blockchain integration)
    - Creates transaction record with blockchain hash

    **Note:** This is a placeholder - requires BNB Chain integration to send actual crypto.
    """
    point_service = PointService(db)
    transaction = await point_service.claim_crypto_reward(
        user_id=current_user.id,
        wallet_address=reward_request.bnb_wallet_address
    )
    return transaction


@router.post("/admin/adjust", response_model=TransactionResponse, summary="Admin: Adjust user points")
async def admin_adjust_points(
    adjustment: AdminAdjustment,
    current_user: User = Depends(require_senior_moderator),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually adjust a user's points (senior moderator only).

    **Required fields:**
    - `user_id`: Target user ID
    - `amount`: Points to add (positive) or subtract (negative)
    - `description`: Reason for adjustment

    **Use cases:**
    - Compensate users for bugs
    - Penalize users for violations
    - Grant special rewards
    """
    point_service = PointService(db)
    transaction = await point_service.admin_adjust_points(adjustment, current_user.id)
    return transaction
