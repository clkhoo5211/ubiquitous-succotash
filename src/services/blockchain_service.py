"""Blockchain Service - BNB Chain Integration

Handles wallet connections, reward redemptions, and transaction monitoring.
"""

import logging
from decimal import Decimal
from typing import Tuple

from eth_account.messages import encode_defunct
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import AsyncWeb3
from web3.exceptions import Web3Exception

from src.core.config import config
from src.core.exceptions import BlockchainError, InsufficientPointsError
from src.models.user import User
from src.schemas.blockchain import (
    TransactionStatusResponse,
    WalletBalanceResponse,
    WalletConnectRequest,
    WalletConnectResponse,
)

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for BNB Chain blockchain operations"""

    def __init__(self):
        """Initialize Web3 connection to BNB Chain"""
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(config.payments.bnb_chain_rpc))
        self.conversion_rate = Decimal("1000")  # 1000 points = 1 BNB (configurable)
        self.min_redemption_points = 10000  # Minimum points for redemption

    async def verify_wallet_signature(
        self, wallet_request: WalletConnectRequest
    ) -> Tuple[bool, str]:
        """Verify wallet ownership through signature verification

        Args:
            wallet_request: Wallet connection request with signature

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Encode the message
            message = encode_defunct(text=wallet_request.message)

            # Recover address from signature
            recovered_address = self.w3.eth.account.recover_message(
                message, signature=wallet_request.signature
            )

            # Compare with provided address
            is_valid = recovered_address.lower() == wallet_request.wallet_address.lower()

            if is_valid:
                return True, "Wallet verified successfully"
            else:
                return False, "Signature verification failed"

        except Exception as e:
            logger.error(f"Wallet verification error: {e}")
            return False, f"Verification error: {str(e)}"

    async def connect_wallet(
        self, db: AsyncSession, user: User, wallet_request: WalletConnectRequest
    ) -> WalletConnectResponse:
        """Connect and verify user's BNB Chain wallet

        Args:
            db: Database session
            user: Current user
            wallet_request: Wallet connection request

        Returns:
            WalletConnectResponse with connection status
        """
        # Verify signature
        is_valid, message = await self.verify_wallet_signature(wallet_request)

        if not is_valid:
            return WalletConnectResponse(success=False, message=message)

        # Update user's wallet address
        user.bnb_wallet_address = wallet_request.wallet_address
        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.id} connected wallet {wallet_request.wallet_address}")

        return WalletConnectResponse(
            success=True,
            wallet_address=wallet_request.wallet_address,
            message="Wallet connected successfully",
        )

    async def get_wallet_balance(self, wallet_address: str) -> Decimal:
        """Get BNB balance for a wallet address

        Args:
            wallet_address: Wallet address to check

        Returns:
            BNB balance as Decimal
        """
        try:
            balance_wei = await self.w3.eth.get_balance(wallet_address)
            balance_bnb = Decimal(self.w3.from_wei(balance_wei, "ether"))
            return balance_bnb
        except Web3Exception as e:
            logger.error(f"Error fetching balance for {wallet_address}: {e}")
            raise BlockchainError(f"Failed to fetch wallet balance: {str(e)}")

    async def get_user_wallet_info(self, db: AsyncSession, user: User) -> WalletBalanceResponse:
        """Get comprehensive wallet information for user

        Args:
            db: Database session
            user: Current user

        Returns:
            WalletBalanceResponse with balance details
        """
        if not user.bnb_wallet_address:
            raise BlockchainError("No wallet connected. Please connect a wallet first.")

        # Get on-chain BNB balance
        bnb_balance = await self.get_wallet_balance(user.bnb_wallet_address)

        return WalletBalanceResponse(
            wallet_address=user.bnb_wallet_address,
            bnb_balance=bnb_balance,
            platform_points=user.points,
            conversion_rate=self.conversion_rate,
        )

    async def calculate_bnb_reward(self, points: int) -> Decimal:
        """Calculate BNB amount for given points

        Args:
            points: Number of points to convert

        Returns:
            BNB amount as Decimal
        """
        return Decimal(points) / self.conversion_rate

    async def send_bnb_reward(self, recipient_address: str, bnb_amount: Decimal) -> str:
        """Send BNB reward to user's wallet

        Note: This is a placeholder for production implementation.
        In production, this should:
        1. Use a secure hot wallet for automated payouts
        2. Implement transaction queueing and batching
        3. Add gas price optimization
        4. Include transaction retry logic
        5. Implement multi-signature security for large amounts

        Args:
            recipient_address: User's wallet address
            bnb_amount: Amount of BNB to send

        Returns:
            Transaction hash

        Raises:
            BlockchainError: If transaction fails
        """
        # TODO: Implement actual BNB transfer using platform's hot wallet
        # For now, return a mock transaction hash for development/testing
        logger.warning(
            f"MOCK: Would send {bnb_amount} BNB to {recipient_address}. "
            "Implement actual web3.py transaction in production."
        )

        # Mock transaction hash (in production, this would be the real tx hash)
        mock_tx_hash = f"0x{'0' * 64}"

        return mock_tx_hash

    async def redeem_points_for_bnb(
        self, db: AsyncSession, user: User, points_to_redeem: int, wallet_address: str
    ) -> Tuple[str, Decimal]:
        """Redeem platform points for BNB rewards

        Args:
            db: Database session
            user: Current user
            points_to_redeem: Number of points to convert
            wallet_address: Destination wallet address

        Returns:
            Tuple of (transaction_hash, bnb_amount)

        Raises:
            InsufficientPointsError: If user doesn't have enough points
            BlockchainError: If transaction fails
        """
        # Validate sufficient points
        if user.points < points_to_redeem:
            raise InsufficientPointsError(
                f"Insufficient points. You have {user.points}, " f"need {points_to_redeem}"
            )

        # Validate minimum redemption amount
        if points_to_redeem < self.min_redemption_points:
            raise BlockchainError(f"Minimum redemption is {self.min_redemption_points} points")

        # Calculate BNB amount
        bnb_amount = await self.calculate_bnb_reward(points_to_redeem)

        # Send BNB (in production, this would be actual blockchain transaction)
        transaction_hash = await self.send_bnb_reward(wallet_address, bnb_amount)

        # Deduct points from user (only after successful transaction)
        user.points -= points_to_redeem
        await db.commit()
        await db.refresh(user)

        logger.info(
            f"User {user.id} redeemed {points_to_redeem} points for {bnb_amount} BNB. "
            f"TX: {transaction_hash}"
        )

        return transaction_hash, bnb_amount

    async def get_transaction_status(self, transaction_hash: str) -> TransactionStatusResponse:
        """Get status of a blockchain transaction

        Args:
            transaction_hash: Transaction hash to check

        Returns:
            TransactionStatusResponse with transaction details
        """
        try:
            # Get transaction receipt
            receipt = await self.w3.eth.get_transaction_receipt(transaction_hash)

            if receipt is None:
                # Transaction is pending
                return TransactionStatusResponse(
                    transaction_hash=transaction_hash,
                    status="pending",
                    confirmations=0,
                )

            # Get current block number for confirmation count
            current_block = await self.w3.eth.block_number
            confirmations = current_block - receipt["blockNumber"]

            # Determine status based on receipt
            status = "confirmed" if receipt["status"] == 1 else "failed"

            # Get transaction details
            tx = await self.w3.eth.get_transaction(transaction_hash)
            bnb_amount = Decimal(self.w3.from_wei(tx["value"], "ether"))

            return TransactionStatusResponse(
                transaction_hash=transaction_hash,
                status=status,
                confirmations=int(confirmations),
                block_number=int(receipt["blockNumber"]),
                bnb_amount=bnb_amount,
                from_address=tx["from"],
                to_address=tx["to"],
            )

        except Exception as e:
            logger.error(f"Error fetching transaction status: {e}")
            # If transaction not found, it might be pending or invalid
            return TransactionStatusResponse(
                transaction_hash=transaction_hash, status="unknown", confirmations=0
            )


# Global service instance
blockchain_service = BlockchainService()
