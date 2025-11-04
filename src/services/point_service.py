"""Point service - Business logic for point operations"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.points import Transaction, PointEconomy, TransactionType
from src.models.user import User
from src.schemas.points import AdminAdjustment, LeaderboardEntry
from src.core.exceptions import (
    UserNotFoundError,
    InsufficientBalanceError,
    InvalidWalletAddressError,
)


class PointService:
    """Service for point-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_economy_config(self) -> PointEconomy:
        """Get point economy configuration"""
        result = await self.db.execute(select(PointEconomy).where(PointEconomy.id == 1))
        config = result.scalar_one_or_none()

        # Create default config if doesn't exist
        if not config:
            config = PointEconomy(
                id=1,
                create_post_cost=-5,
                create_comment_cost=-2,
                like_cost=-1,
                registration_bonus=100,
                receive_like_tier1=3,
                receive_like_tier2=30,
                receive_like_tier3=350,
                crypto_reward_cost=10000,
                crypto_reward_bnb_amount="0.01",
                updated_at=datetime.utcnow(),
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

        return config

    async def create_transaction(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        blockchain_tx_hash: Optional[str] = None,
        bnb_amount: Optional[str] = None,
    ) -> Transaction:
        """Create a point transaction and update user balance"""
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Check if user has sufficient balance for negative transactions
        if amount < 0 and user.points + amount < 0:
            raise InsufficientBalanceError(
                f"Insufficient points. Current: {user.points}, Required: {abs(amount)}"
            )

        # Update user points
        user.points += amount
        balance_after = user.points

        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_after=balance_after,
            blockchain_tx_hash=blockchain_tx_hash,
            bnb_amount=bnb_amount,
            created_at=datetime.utcnow(),
        )

        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def get_user_transactions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
        transaction_type: Optional[TransactionType] = None,
    ) -> Tuple[List[Transaction], int]:
        """Get user's transaction history"""
        query = select(Transaction).where(Transaction.user_id == user_id)

        # Filter by type if provided
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)

        # Get total count
        count_query = (
            select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        )
        if transaction_type:
            count_query = count_query.where(Transaction.transaction_type == transaction_type)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Sort by created_at desc (most recent first)
        query = query.order_by(desc(Transaction.created_at))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total

    async def get_user_points_summary(self, user_id: int) -> dict:
        """Get user's points summary with statistics"""
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Get total earned (sum of positive transactions)
        earned_result = await self.db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id)
            .where(Transaction.amount > 0)
        )
        total_earned = earned_result.scalar() or 0

        # Get total spent (sum of negative transactions)
        spent_result = await self.db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id)
            .where(Transaction.amount < 0)
        )
        total_spent = abs(spent_result.scalar() or 0)

        # Get transaction count
        count_result = await self.db.execute(
            select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        )
        transactions_count = count_result.scalar()

        # Get crypto reward cost
        config = await self.get_economy_config()
        can_claim_crypto = user.points >= config.crypto_reward_cost

        return {
            "user_id": user.id,
            "username": user.username,
            "current_points": user.points,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "transactions_count": transactions_count,
            "can_claim_crypto": can_claim_crypto,
            "crypto_reward_cost": config.crypto_reward_cost,
        }

    async def admin_adjust_points(self, adjustment: AdminAdjustment, admin_id: int) -> Transaction:
        """Admin-only: Adjust user points"""
        transaction = await self.create_transaction(
            user_id=adjustment.user_id,
            amount=adjustment.amount,
            transaction_type=TransactionType.ADMIN_ADJUSTMENT,
            description=f"Admin adjustment by user {admin_id}: {adjustment.description}",
        )
        return transaction

    async def get_leaderboard(
        self, page: int = 1, page_size: int = 50
    ) -> Tuple[List[LeaderboardEntry], int]:
        """Get points leaderboard"""
        # Get total user count
        count_result = await self.db.execute(
            select(func.count()).select_from(User).where(User.is_active)
        )
        total = count_result.scalar()

        # Get top users by points
        query = select(User).where(User.is_active)
        query = query.order_by(desc(User.points))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = result.scalars().all()

        # Create leaderboard entries with ranks
        leaderboard = []
        for idx, user in enumerate(users, start=offset + 1):
            entry = LeaderboardEntry(
                rank=idx,
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                points=user.points,
                level=user.level.value,
            )
            leaderboard.append(entry)

        return leaderboard, total

    async def claim_crypto_reward(self, user_id: int, wallet_address: str) -> Transaction:
        """Claim crypto reward (placeholder - needs blockchain integration)"""
        # Validate wallet address
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            raise InvalidWalletAddressError("Invalid BNB wallet address format")

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Get config
        config = await self.get_economy_config()

        # Check if user has enough points
        if user.points < config.crypto_reward_cost:
            raise InsufficientBalanceError(
                f"Insufficient points. Required: {config.crypto_reward_cost}, Current: {user.points}"
            )

        # TODO: Integrate with BNB Chain to send actual crypto
        # For now, create a placeholder transaction
        blockchain_tx_hash = f"0x{'0' * 64}"  # Placeholder hash
        bnb_amount = str(config.crypto_reward_bnb_amount)

        # Create transaction
        transaction = await self.create_transaction(
            user_id=user_id,
            amount=-config.crypto_reward_cost,
            transaction_type=TransactionType.CRYPTO_REWARD,
            description=f"Crypto reward claim: {bnb_amount} BNB sent to {wallet_address}",
            blockchain_tx_hash=blockchain_tx_hash,
            bnb_amount=bnb_amount,
        )

        # Update user wallet address if not set
        if not user.bnb_wallet_address:
            user.bnb_wallet_address = wallet_address
            await self.db.commit()

        return transaction

    async def award_registration_bonus(self, user_id: int) -> Transaction:
        """Award registration bonus to new user"""
        config = await self.get_economy_config()

        transaction = await self.create_transaction(
            user_id=user_id,
            amount=config.registration_bonus,
            transaction_type=TransactionType.REGISTRATION_BONUS,
            description=f"Registration bonus: {config.registration_bonus} points",
        )

        return transaction
