"""Point economy database models"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class TransactionType(str, enum.Enum):
    """Point transaction types"""

    REGISTRATION_BONUS = "registration_bonus"  # +100 points
    CREATE_POST = "create_post"  # -5 points
    CREATE_COMMENT = "create_comment"  # -2 points
    LIKE_CONTENT = "like_content"  # -1 point
    RECEIVE_LIKE = "receive_like"  # +3, +30, +350 based on milestones
    CRYPTO_REWARD = "crypto_reward"  # -10,000 points for 0.01 BNB
    ADMIN_ADJUSTMENT = "admin_adjustment"  # Manual adjustment
    REFUND = "refund"  # Refund (unlike, delete)


class Transaction(Base):
    """Point transaction history"""

    __tablename__ = "transactions"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Transaction Details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Can be negative
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Reference (polymorphic)
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'post', 'comment', 'like'
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Balance after transaction
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # Blockchain (for crypto rewards)
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bnb_amount: Mapped[Optional[str]] = mapped_column(
        Numeric(20, 18), nullable=True
    )  # BNB amount sent

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index("idx_transactions_user_id_created_at", user_id, created_at.desc()),
        Index("idx_transactions_type_created_at", transaction_type, created_at),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"


class PointEconomy(Base):
    """Point economy configuration (singleton table)"""

    __tablename__ = "point_economy"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Costs (negative values)
    create_post_cost: Mapped[int] = mapped_column(Integer, default=-5)
    create_comment_cost: Mapped[int] = mapped_column(Integer, default=-2)
    like_cost: Mapped[int] = mapped_column(Integer, default=-1)

    # Rewards (positive values)
    registration_bonus: Mapped[int] = mapped_column(Integer, default=100)
    receive_like_tier1: Mapped[int] = mapped_column(Integer, default=3)  # 1st like
    receive_like_tier2: Mapped[int] = mapped_column(Integer, default=30)  # 10th like
    receive_like_tier3: Mapped[int] = mapped_column(Integer, default=350)  # 100th like

    # Crypto Rewards
    crypto_reward_cost: Mapped[int] = mapped_column(Integer, default=10000)
    crypto_reward_bnb_amount: Mapped[str] = mapped_column(
        Numeric(20, 18), default="0.01"
    )  # 0.01 BNB

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<PointEconomy(create_post_cost={self.create_post_cost}, crypto_reward_cost={self.crypto_reward_cost})>"


# Import to avoid circular dependencies
from src.models.user import User  # noqa: E402
