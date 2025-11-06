"""Unit tests for blockchain_service

Tests blockchain operations with mocked Web3 and database calls.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BlockchainError, InsufficientPointsError
from src.models.user import User
from src.schemas.blockchain import (
    TransactionStatusResponse,
    WalletBalanceResponse,
    WalletConnectRequest,
    WalletConnectResponse,
)
from src.services.blockchain_service import BlockchainService


@pytest.fixture
def blockchain_service():
    """Create blockchain service instance"""
    return BlockchainService()


@pytest.fixture
def mock_user():
    """Create mock user for testing - use simple object instead of MagicMock"""

    class MockUser:
        """Simple mock user object with mutable attributes"""

        def __init__(self):
            self.id = 1
            self.username = "testuser"
            self.points = 50000
            self.wallet_address = None

    return MockUser()


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def wallet_connect_request():
    """Create valid wallet connect request"""
    return WalletConnectRequest(
        wallet_address="0x742d35cc6634c0532925a3b844bc9e7595f0beb0",
        signature="0xabcd1234...",
        message="Connect wallet to Decentralized Forum - Nonce: 1_1234567890",
    )


class TestWalletVerification:
    """Test wallet signature verification"""

    @pytest.mark.asyncio
    async def test_verify_valid_signature(self, blockchain_service, wallet_connect_request):
        """Test signature verification with valid signature"""
        with patch.object(blockchain_service.w3.eth.account, "recover_message") as mock_recover:
            mock_recover.return_value = wallet_connect_request.wallet_address

            is_valid, message = await blockchain_service.verify_wallet_signature(
                wallet_connect_request
            )

            assert is_valid is True
            assert message == "Wallet verified successfully"

    @pytest.mark.asyncio
    async def test_verify_invalid_signature(self, blockchain_service, wallet_connect_request):
        """Test signature verification with invalid signature"""
        with patch.object(blockchain_service.w3.eth.account, "recover_message") as mock_recover:
            # Return different address
            mock_recover.return_value = "0xdifferentaddress"

            is_valid, message = await blockchain_service.verify_wallet_signature(
                wallet_connect_request
            )

            assert is_valid is False
            assert message == "Signature verification failed"

    @pytest.mark.asyncio
    async def test_verify_signature_exception(self, blockchain_service, wallet_connect_request):
        """Test signature verification when exception occurs"""
        with patch.object(blockchain_service.w3.eth.account, "recover_message") as mock_recover:
            mock_recover.side_effect = Exception("Invalid signature format")

            is_valid, message = await blockchain_service.verify_wallet_signature(
                wallet_connect_request
            )

            assert is_valid is False
            assert "Verification error" in message


class TestWalletConnection:
    """Test wallet connection functionality"""

    @pytest.mark.asyncio
    async def test_connect_wallet_success(
        self, blockchain_service, mock_db_session, mock_user, wallet_connect_request
    ):
        """Test successful wallet connection"""
        with patch.object(blockchain_service, "verify_wallet_signature") as mock_verify:
            mock_verify.return_value = (True, "Wallet verified successfully")

            result = await blockchain_service.connect_wallet(
                mock_db_session, mock_user, wallet_connect_request
            )

            assert isinstance(result, WalletConnectResponse)
            assert result.success is True
            assert result.wallet_address == wallet_connect_request.wallet_address
            assert mock_user.wallet_address == wallet_connect_request.wallet_address
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_wallet_verification_failed(
        self, blockchain_service, mock_db_session, mock_user, wallet_connect_request
    ):
        """Test wallet connection with failed verification"""
        with patch.object(blockchain_service, "verify_wallet_signature") as mock_verify:
            mock_verify.return_value = (False, "Signature verification failed")

            result = await blockchain_service.connect_wallet(
                mock_db_session, mock_user, wallet_connect_request
            )

            assert result.success is False
            assert result.wallet_address is None
            assert mock_user.wallet_address is None


class TestWalletBalance:
    """Test wallet balance queries"""

    @pytest.mark.asyncio
    async def test_get_wallet_balance(self, blockchain_service):
        """Test getting BNB balance from blockchain"""
        test_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
        test_balance_wei = 5000000000000000000  # 5 BNB in wei

        with patch.object(blockchain_service.w3.eth, "get_balance") as mock_get_balance:
            mock_get_balance.return_value = test_balance_wei

            balance = await blockchain_service.get_wallet_balance(test_address)

            assert balance == Decimal("5.0")
            mock_get_balance.assert_called_once_with(test_address)

    @pytest.mark.asyncio
    async def test_get_wallet_balance_network_error(self, blockchain_service):
        """Test wallet balance query with network error"""
        from web3.exceptions import Web3Exception

        test_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"

        with patch.object(blockchain_service.w3.eth, "get_balance") as mock_get_balance:
            mock_get_balance.side_effect = Web3Exception("Network timeout")

            with pytest.raises(BlockchainError) as exc_info:
                await blockchain_service.get_wallet_balance(test_address)

            assert "Failed to fetch wallet balance" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_wallet_info(self, blockchain_service, mock_db_session, mock_user):
        """Test getting comprehensive wallet info for user"""
        mock_user.wallet_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
        mock_user.points = 50000

        with patch.object(blockchain_service, "get_wallet_balance") as mock_get_balance:
            mock_get_balance.return_value = Decimal("5.0")

            result = await blockchain_service.get_user_wallet_info(mock_db_session, mock_user)

            assert isinstance(result, WalletBalanceResponse)
            assert result.wallet_address == mock_user.wallet_address
            assert result.bnb_balance == Decimal("5.0")
            assert result.platform_points == 50000
            assert result.conversion_rate == Decimal("1000")

    @pytest.mark.asyncio
    async def test_get_user_wallet_info_no_wallet(
        self, blockchain_service, mock_db_session, mock_user
    ):
        """Test getting wallet info when user has no wallet connected"""
        mock_user.wallet_address = None

        with pytest.raises(BlockchainError) as exc_info:
            await blockchain_service.get_user_wallet_info(mock_db_session, mock_user)

        assert "No wallet connected" in str(exc_info.value)


class TestBNBConversion:
    """Test points-to-BNB conversion"""

    @pytest.mark.asyncio
    async def test_calculate_bnb_reward(self, blockchain_service):
        """Test BNB amount calculation from points"""
        test_cases = [
            (1000, Decimal("1.0")),  # 1000 points = 1 BNB
            (10000, Decimal("10.0")),  # 10000 points = 10 BNB
            (500, Decimal("0.5")),  # 500 points = 0.5 BNB
        ]

        for points, expected_bnb in test_cases:
            result = await blockchain_service.calculate_bnb_reward(points)
            assert result == expected_bnb


class TestPointsRedemption:
    """Test points-to-BNB redemption"""

    @pytest.mark.asyncio
    async def test_redeem_points_success(self, blockchain_service, mock_db_session, mock_user):
        """Test successful points redemption"""
        points_to_redeem = 20000
        wallet_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
        expected_bnb = Decimal("20.0")

        with patch.object(blockchain_service, "send_bnb_reward") as mock_send_bnb:
            mock_send_bnb.return_value = "0x" + "0" * 64

            tx_hash, bnb_amount = await blockchain_service.redeem_points_for_bnb(
                mock_db_session, mock_user, points_to_redeem, wallet_address
            )

            assert tx_hash.startswith("0x")
            assert bnb_amount == expected_bnb
            assert mock_user.points == 30000  # 50000 - 20000
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_redeem_points_insufficient_balance(
        self, blockchain_service, mock_db_session, mock_user
    ):
        """Test redemption with insufficient points"""
        mock_user.points = 5000
        points_to_redeem = 10000
        wallet_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"

        with pytest.raises(InsufficientPointsError) as exc_info:
            await blockchain_service.redeem_points_for_bnb(
                mock_db_session, mock_user, points_to_redeem, wallet_address
            )

        assert "Insufficient points" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redeem_points_below_minimum(
        self, blockchain_service, mock_db_session, mock_user
    ):
        """Test redemption below minimum threshold"""
        points_to_redeem = 5000  # Below 10000 minimum
        wallet_address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"

        with pytest.raises(BlockchainError) as exc_info:
            await blockchain_service.redeem_points_for_bnb(
                mock_db_session, mock_user, points_to_redeem, wallet_address
            )

        assert "Minimum redemption" in str(exc_info.value)


class TestTransactionStatus:
    """Test transaction status tracking"""

    @pytest.mark.asyncio
    async def test_get_transaction_status_confirmed(self, blockchain_service):
        """Test getting status of confirmed transaction"""
        tx_hash = "0x" + "1" * 64
        mock_receipt = {
            "blockNumber": 1000,
            "status": 1,
        }
        mock_tx = {
            "from": "0xsender",
            "to": "0xrecipient",
            "value": 5000000000000000000,  # 5 BNB
        }

        # Create async function for block_number property
        async def mock_block_number_func():
            return 1012

        with (
            patch.object(blockchain_service.w3.eth, "get_transaction_receipt") as mock_receipt_call,
            patch.object(blockchain_service.w3.eth, "get_transaction") as mock_tx_call,
            patch.object(
                type(blockchain_service.w3.eth),
                "block_number",
                new_callable=PropertyMock,
                return_value=mock_block_number_func(),
            ),
        ):
            mock_receipt_call.return_value = mock_receipt
            mock_tx_call.return_value = mock_tx

            result = await blockchain_service.get_transaction_status(tx_hash)

            assert isinstance(result, TransactionStatusResponse)
            assert result.status == "confirmed"
            assert result.confirmations == 12  # 1012 - 1000
            assert result.block_number == 1000
            assert result.bnb_amount == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_get_transaction_status_pending(self, blockchain_service):
        """Test getting status of pending transaction"""
        tx_hash = "0x" + "1" * 64

        with patch.object(blockchain_service.w3.eth, "get_transaction_receipt") as mock_receipt:
            mock_receipt.return_value = None  # Pending

            result = await blockchain_service.get_transaction_status(tx_hash)

            assert result.status == "pending"
            assert result.confirmations == 0

    @pytest.mark.asyncio
    async def test_get_transaction_status_failed(self, blockchain_service):
        """Test getting status of failed transaction"""
        tx_hash = "0x" + "1" * 64
        mock_receipt = {
            "blockNumber": 1000,
            "status": 0,  # Failed
        }
        mock_tx = {
            "from": "0xsender",
            "to": "0xrecipient",
            "value": 0,
        }

        # Create async function for block_number property
        async def mock_block_number_func():
            return 1005

        with (
            patch.object(blockchain_service.w3.eth, "get_transaction_receipt") as mock_receipt_call,
            patch.object(blockchain_service.w3.eth, "get_transaction") as mock_tx_call,
            patch.object(
                type(blockchain_service.w3.eth),
                "block_number",
                new_callable=PropertyMock,
                return_value=mock_block_number_func(),
            ),
        ):
            mock_receipt_call.return_value = mock_receipt
            mock_tx_call.return_value = mock_tx

            result = await blockchain_service.get_transaction_status(tx_hash)

            assert result.status == "failed"
            assert result.confirmations == 5


class TestSendBNBReward:
    """Test BNB sending (mock implementation)"""

    @pytest.mark.asyncio
    async def test_send_bnb_reward_mock(self, blockchain_service):
        """Test mock BNB sending returns transaction hash"""
        recipient = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
        amount = Decimal("5.0")

        tx_hash = await blockchain_service.send_bnb_reward(recipient, amount)

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66  # 0x + 64 hex chars
