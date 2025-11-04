"""Unit tests for oauth_service

Tests OAuth2 authentication flow for all 5 providers with mocked HTTP calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import OAuthError, OAuthProviderError
from src.models.user import OAuthAccount, User
from src.services.oauth_service import OAuth2Service


@pytest.fixture
def oauth_service():
    """Create OAuth2 service instance"""
    return OAuth2Service()


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_oauth_config():
    """Mock OAuth configuration"""
    with patch("src.services.oauth_service.config") as mock_config:
        # Mock Meta config
        mock_config.oauth_meta.client_id = "meta_client_id"
        mock_config.oauth_meta.client_secret = "meta_secret"
        mock_config.oauth_meta.redirect_uri = "http://localhost/oauth/meta/callback"
        mock_config.oauth_meta.scope = "email,public_profile"

        # Mock Reddit config
        mock_config.oauth_reddit.client_id = "reddit_client_id"
        mock_config.oauth_reddit.client_secret = "reddit_secret"
        mock_config.oauth_reddit.redirect_uri = "http://localhost/oauth/reddit/callback"
        mock_config.oauth_reddit.scope = "identity"

        # Mock Discord config
        mock_config.oauth_discord.client_id = "discord_client_id"
        mock_config.oauth_discord.client_secret = "discord_secret"
        mock_config.oauth_discord.redirect_uri = "http://localhost/oauth/discord/callback"
        mock_config.oauth_discord.scope = "identify email"

        # Mock X (Twitter) config
        mock_config.oauth_twitter.client_id = "x_client_id"
        mock_config.oauth_twitter.client_secret = "x_secret"
        mock_config.oauth_twitter.redirect_uri = "http://localhost/oauth/x/callback"
        mock_config.oauth_twitter.scope = "tweet.read users.read"

        # Mock Telegram config
        mock_config.oauth_telegram.client_id = "telegram_bot_token"
        mock_config.oauth_telegram.client_secret = "telegram_secret"
        mock_config.oauth_telegram.redirect_uri = "http://localhost/oauth/telegram/callback"
        mock_config.oauth_telegram.scope = ""

        # Mock point economy
        mock_config.point_economy.registration_bonus = 100

        yield mock_config


class TestProviderConfiguration:
    """Test OAuth provider configuration"""

    def test_get_provider_config_meta(self, oauth_service):
        """Test getting Meta provider configuration"""
        config = oauth_service.get_provider_config("meta")

        assert config["name"] == "Meta (Facebook)"
        assert "facebook.com" in config["auth_url"]
        assert "graph.facebook.com" in config["token_url"]
        assert config["scope"] == "email,public_profile"

    def test_get_provider_config_reddit(self, oauth_service):
        """Test getting Reddit provider configuration"""
        config = oauth_service.get_provider_config("reddit")

        assert config["name"] == "Reddit"
        assert "reddit.com" in config["auth_url"]
        assert config["scope"] == "identity"

    def test_get_provider_config_discord(self, oauth_service):
        """Test getting Discord provider configuration"""
        config = oauth_service.get_provider_config("discord")

        assert config["name"] == "Discord"
        assert "discord.com" in config["auth_url"]
        assert config["scope"] == "identify email"

    def test_get_provider_config_invalid(self, oauth_service):
        """Test getting configuration for invalid provider"""
        with pytest.raises(OAuthError) as exc_info:
            oauth_service.get_provider_config("invalid_provider")

        assert "Unsupported OAuth provider" in str(exc_info.value)


class TestAuthorizationURL:
    """Test authorization URL generation"""

    def test_get_authorization_url_meta(self, oauth_service, mock_oauth_config):
        """Test generating authorization URL for Meta"""
        state = "test_state_123"

        url = oauth_service.get_authorization_url("meta", state)

        # Parse URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "facebook.com" in url
        assert params["client_id"][0] == "meta_client_id"
        assert params["state"][0] == state
        assert params["response_type"][0] == "code"
        assert "email" in params["scope"][0]

    def test_get_authorization_url_reddit(self, oauth_service, mock_oauth_config):
        """Test generating authorization URL for Reddit"""
        state = "test_state_456"

        url = oauth_service.get_authorization_url("reddit", state)

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "reddit.com" in url
        assert params["client_id"][0] == "reddit_client_id"
        assert params["state"][0] == state
        assert params["scope"][0] == "identity"


class TestTokenExchange:
    """Test authorization code to access token exchange"""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, oauth_service, mock_oauth_config):
        """Test successful token exchange"""
        code = "auth_code_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "access_token_abc",
            "refresh_token": "refresh_token_xyz",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            access_token, refresh_token = await oauth_service.exchange_code_for_token("meta", code)

            assert access_token == "access_token_abc"
            assert refresh_token == "refresh_token_xyz"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_error(self, oauth_service, mock_oauth_config):
        """Test token exchange with API error"""
        code = "auth_code_123"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(OAuthProviderError) as exc_info:
                await oauth_service.exchange_code_for_token("meta", code)

            assert "Failed to exchange code for token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_no_access_token(self, oauth_service, mock_oauth_config):
        """Test token exchange when no access token in response"""
        code = "auth_code_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No access_token

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(OAuthProviderError) as exc_info:
                await oauth_service.exchange_code_for_token("meta", code)

            assert "No access token in response" in str(exc_info.value)


class TestUserInfoRetrieval:
    """Test user info fetching from OAuth providers"""

    @pytest.mark.asyncio
    async def test_get_user_info_meta(self, oauth_service):
        """Test fetching user info from Meta"""
        access_token = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456789",
            "name": "John Doe",
            "email": "john@example.com",
            "picture": {"data": {"url": "https://example.com/avatar.jpg"}},
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            user_info = await oauth_service.get_user_info("meta", access_token)

            assert user_info["provider_id"] == "123456789"
            assert user_info["email"] == "john@example.com"
            assert user_info["username"] == "John Doe"
            assert "avatar.jpg" in user_info["avatar_url"]

    @pytest.mark.asyncio
    async def test_get_user_info_reddit(self, oauth_service):
        """Test fetching user info from Reddit"""
        access_token = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "reddit_user_123",
            "name": "reddit_username",
            "icon_img": "https://reddit.com/avatar.png",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            user_info = await oauth_service.get_user_info("reddit", access_token)

            assert user_info["provider_id"] == "reddit_user_123"
            assert user_info["username"] == "reddit_username"
            assert user_info["email"] is None  # Reddit doesn't provide email

    @pytest.mark.asyncio
    async def test_get_user_info_discord(self, oauth_service):
        """Test fetching user info from Discord"""
        access_token = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "discord_123",
            "username": "discord_user",
            "email": "discord@example.com",
            "avatar": "avatar_hash_123",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            user_info = await oauth_service.get_user_info("discord", access_token)

            assert user_info["provider_id"] == "discord_123"
            assert user_info["username"] == "discord_user"
            assert user_info["email"] == "discord@example.com"
            assert "cdn.discordapp.com" in user_info["avatar_url"]

    @pytest.mark.asyncio
    async def test_get_user_info_api_error(self, oauth_service):
        """Test user info fetch with API error"""
        access_token = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(OAuthProviderError) as exc_info:
                await oauth_service.get_user_info("meta", access_token)

            assert "Failed to fetch user info" in str(exc_info.value)


class TestFindOrCreateUser:
    """Test user creation/retrieval from OAuth data"""

    @pytest.mark.asyncio
    async def test_find_existing_oauth_account(
        self, oauth_service, mock_db_session, mock_oauth_config
    ):
        """Test finding existing user by OAuth account"""
        user_info = {
            "provider_id": "123456",
            "email": "existing@example.com",
            "username": "existing_user",
            "avatar_url": None,
        }

        # Mock existing OAuth account
        mock_oauth_account = MagicMock(spec=OAuthAccount)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.username = "existing_user"
        mock_oauth_account.user = mock_user

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_oauth_account
        mock_db_session.execute.return_value = mock_result

        user = await oauth_service.find_or_create_user(mock_db_session, "meta", user_info)

        assert user == mock_user
        # Should not add new user
        assert not mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_link_oauth_to_existing_email(
        self, oauth_service, mock_db_session, mock_oauth_config
    ):
        """Test linking OAuth account to existing user by email"""
        user_info = {
            "provider_id": "new_oauth_123",
            "email": "existing@example.com",
            "username": "oauth_username",
            "avatar_url": None,
        }

        # First query: No OAuth account found
        # Second query: Existing user found by email
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.email = "existing@example.com"

        mock_results = [
            MagicMock(scalar_one_or_none=lambda: None),  # No OAuth account
            MagicMock(scalar_one_or_none=lambda: mock_user),  # Found by email
        ]
        mock_db_session.execute.side_effect = mock_results

        user = await oauth_service.find_or_create_user(mock_db_session, "meta", user_info)

        assert user == mock_user
        # Should create OAuth account for existing user
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_create_new_user_with_oauth(
        self, oauth_service, mock_db_session, mock_oauth_config
    ):
        """Test creating new user from OAuth data"""
        user_info = {
            "provider_id": "new_user_789",
            "email": "newuser@example.com",
            "username": "new_oauth_user",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        # No existing OAuth account, no existing email, username available
        mock_results = [
            MagicMock(scalar_one_or_none=lambda: None),  # No OAuth account
            MagicMock(scalar_one_or_none=lambda: None),  # No user by email
            MagicMock(scalar_one_or_none=lambda: None),  # Username available
        ]
        mock_db_session.execute.side_effect = mock_results

        _ = await oauth_service.find_or_create_user(mock_db_session, "meta", user_info)

        # Should add new user and OAuth account
        assert mock_db_session.add.call_count == 2  # User + OAuthAccount
        assert mock_db_session.flush.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_username(
        self, oauth_service, mock_db_session, mock_oauth_config
    ):
        """Test creating user when username is already taken"""
        user_info = {
            "provider_id": "new_user_999",
            "email": "newuser2@example.com",
            "username": "taken_username",
            "avatar_url": None,
        }

        # Mock: username taken first time, available second time
        mock_taken_user = MagicMock(spec=User)
        mock_results = [
            MagicMock(scalar_one_or_none=lambda: None),  # No OAuth account
            MagicMock(scalar_one_or_none=lambda: None),  # No user by email
            MagicMock(scalar_one_or_none=lambda: mock_taken_user),  # Username taken
            MagicMock(scalar_one_or_none=lambda: None),  # Username_1 available
        ]
        mock_db_session.execute.side_effect = mock_results

        _ = await oauth_service.find_or_create_user(mock_db_session, "meta", user_info)

        # Should create user with incremented username
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_create_user_no_email(self, oauth_service, mock_db_session, mock_oauth_config):
        """Test creating user when OAuth provider doesn't provide email"""
        user_info = {
            "provider_id": "reddit_user_123",
            "email": None,  # Reddit doesn't provide email
            "username": "reddit_user",
            "avatar_url": None,
        }

        mock_results = [
            MagicMock(scalar_one_or_none=lambda: None),  # No OAuth account
            MagicMock(scalar_one_or_none=lambda: None),  # Username available
        ]
        mock_db_session.execute.side_effect = mock_results

        _ = await oauth_service.find_or_create_user(mock_db_session, "reddit", user_info)

        # Should create user with synthetic email
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_create_user_invalid_provider(
        self, oauth_service, mock_db_session, mock_oauth_config
    ):
        """Test creating user with invalid provider"""
        user_info = {
            "provider_id": "123",
            "email": "test@example.com",
            "username": "testuser",
            "avatar_url": None,
        }

        with pytest.raises(OAuthError) as exc_info:
            await oauth_service.find_or_create_user(mock_db_session, "invalid_provider", user_info)

        assert "Invalid OAuth provider" in str(exc_info.value)


class TestUserInfoStandardization:
    """Test standardization of user info across providers"""

    def test_standardize_meta_user_info(self, oauth_service):
        """Test standardizing Meta user data"""
        raw_data = {
            "id": "123456789",
            "name": "John Doe",
            "email": "john@example.com",
            "picture": {"data": {"url": "https://graph.facebook.com/avatar.jpg"}},
        }

        standardized = oauth_service.standardize_user_info("meta", raw_data)

        assert standardized["provider_id"] == "123456789"
        assert standardized["email"] == "john@example.com"
        assert standardized["username"] == "John Doe"
        assert "avatar.jpg" in standardized["avatar_url"]

    def test_standardize_reddit_user_info(self, oauth_service):
        """Test standardizing Reddit user data"""
        raw_data = {"id": "reddit123", "name": "reddit_user", "icon_img": "avatar.png"}

        standardized = oauth_service.standardize_user_info("reddit", raw_data)

        assert standardized["provider_id"] == "reddit123"
        assert standardized["username"] == "reddit_user"
        assert standardized["email"] is None

    def test_standardize_discord_user_info(self, oauth_service):
        """Test standardizing Discord user data"""
        raw_data = {
            "id": "discord123",
            "username": "discord_user",
            "email": "discord@example.com",
            "avatar": "avatar_hash",
        }

        standardized = oauth_service.standardize_user_info("discord", raw_data)

        assert standardized["provider_id"] == "discord123"
        assert standardized["username"] == "discord_user"
        assert standardized["email"] == "discord@example.com"
        assert "cdn.discordapp.com" in standardized["avatar_url"]

    def test_standardize_x_user_info(self, oauth_service):
        """Test standardizing X (Twitter) user data"""
        raw_data = {
            "data": {
                "id": "twitter123",
                "username": "twitter_user",
                "profile_image_url": "https://pbs.twimg.com/avatar.jpg",
            }
        }

        standardized = oauth_service.standardize_user_info("x", raw_data)

        assert standardized["provider_id"] == "twitter123"
        assert standardized["username"] == "twitter_user"
        assert standardized["email"] is None
