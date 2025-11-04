"""OAuth2 Service - Social Login Integration

Supports 5 providers:
- Meta (Facebook)
- Reddit
- X (Twitter)
- Discord
- Telegram

Each provider follows OAuth2 authorization code flow.
"""

import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import config
from src.core.exceptions import OAuthError, OAuthProviderError
from src.models.user import User, UserLevelEnum

logger = logging.getLogger(__name__)


class OAuth2Service:
    """Service for OAuth2 social login"""

    def __init__(self):
        """Initialize OAuth2 providers configuration"""
        self.providers = {
            "meta": {
                "name": "Meta (Facebook)",
                "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
                "user_info_url": "https://graph.facebook.com/me",
                "scope": "email,public_profile",
            },
            "reddit": {
                "name": "Reddit",
                "auth_url": "https://www.reddit.com/api/v1/authorize",
                "token_url": "https://www.reddit.com/api/v1/access_token",
                "user_info_url": "https://oauth.reddit.com/api/v1/me",
                "scope": "identity",
            },
            "x": {
                "name": "X (Twitter)",
                "auth_url": "https://twitter.com/i/oauth2/authorize",
                "token_url": "https://api.twitter.com/2/oauth2/token",
                "user_info_url": "https://api.twitter.com/2/users/me",
                "scope": "tweet.read users.read",
            },
            "discord": {
                "name": "Discord",
                "auth_url": "https://discord.com/api/oauth2/authorize",
                "token_url": "https://discord.com/api/oauth2/token",
                "user_info_url": "https://discord.com/api/users/@me",
                "scope": "identify email",
            },
            "telegram": {
                "name": "Telegram",
                # Telegram uses widget-based auth, not OAuth2
                # We'll handle it differently
                "auth_method": "widget",
            },
        }

    def get_provider_config(self, provider: str) -> Dict:
        """Get OAuth2 configuration for provider

        Args:
            provider: Provider name (meta, reddit, x, discord, telegram)

        Returns:
            Provider configuration dict

        Raises:
            OAuthError: If provider not supported
        """
        if provider not in self.providers:
            raise OAuthError(
                f"Unsupported OAuth provider: {provider}. "
                f"Supported: {', '.join(self.providers.keys())}"
            )
        return self.providers[provider]

    def get_authorization_url(self, provider: str, state: str) -> str:
        """Generate OAuth2 authorization URL

        Args:
            provider: Provider name
            state: CSRF protection state token

        Returns:
            Authorization URL to redirect user to

        Raises:
            OAuthError: If provider not supported
        """
        provider_config = self.get_provider_config(provider)

        # Get OAuth2 settings from config
        oauth_settings = self.get_oauth_settings(provider)

        # Build authorization URL
        params = {
            "client_id": oauth_settings["client_id"],
            "redirect_uri": oauth_settings["redirect_uri"],
            "scope": provider_config["scope"],
            "state": state,
            "response_type": "code",
        }

        auth_url = f"{provider_config['auth_url']}?{urlencode(params)}"
        return auth_url

    def get_oauth_settings(self, provider: str) -> Dict:
        """Get OAuth2 client settings from config

        Args:
            provider: Provider name

        Returns:
            Dict with client_id, client_secret, redirect_uri, scope
        """
        # Map provider names to config attributes
        provider_map = {
            "meta": config.oauth_meta,
            "reddit": config.oauth_reddit,
            "x": config.oauth_twitter,
            "discord": config.oauth_discord,
            "telegram": config.oauth_telegram,
        }

        if provider not in provider_map:
            raise OAuthError(f"No OAuth configuration for provider: {provider}")

        oauth_config = provider_map[provider]

        return {
            "client_id": oauth_config.client_id,
            "client_secret": oauth_config.client_secret,
            "redirect_uri": oauth_config.redirect_uri,
            "scope": oauth_config.scope,
        }

    async def exchange_code_for_token(self, provider: str, code: str) -> Tuple[str, Optional[str]]:
        """Exchange authorization code for access token

        Args:
            provider: Provider name
            code: Authorization code from OAuth callback

        Returns:
            Tuple of (access_token, refresh_token)

        Raises:
            OAuthProviderError: If token exchange fails
        """
        provider_config = self.get_provider_config(provider)
        oauth_settings = self.get_oauth_settings(provider)

        # Prepare token request
        token_data = {
            "client_id": oauth_settings["client_id"],
            "client_secret": oauth_settings["client_secret"],
            "code": code,
            "redirect_uri": oauth_settings["redirect_uri"],
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    provider_config["token_url"],
                    data=token_data,
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    logger.error(
                        f"Token exchange failed for {provider}: {response.status_code} - {response.text}"
                    )
                    raise OAuthProviderError(f"Failed to exchange code for token: {response.text}")

                token_response = response.json()
                access_token = token_response.get("access_token")
                refresh_token = token_response.get("refresh_token")

                if not access_token:
                    raise OAuthProviderError("No access token in response")

                return access_token, refresh_token

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise OAuthProviderError(f"Network error: {str(e)}")

    async def get_user_info(self, provider: str, access_token: str) -> Dict:
        """Fetch user information from OAuth provider

        Args:
            provider: Provider name
            access_token: OAuth access token

        Returns:
            User info dict with standardized fields

        Raises:
            OAuthProviderError: If user info fetch fails
        """
        provider_config = self.get_provider_config(provider)

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}"}

                # Provider-specific adjustments
                if provider == "meta":
                    # Request specific fields from Facebook
                    params = {"fields": "id,name,email,picture"}
                    response = await client.get(
                        provider_config["user_info_url"], headers=headers, params=params
                    )
                else:
                    response = await client.get(provider_config["user_info_url"], headers=headers)

                if response.status_code != 200:
                    logger.error(
                        f"User info fetch failed for {provider}: {response.status_code} - {response.text}"
                    )
                    raise OAuthProviderError(f"Failed to fetch user info: {response.text}")

                user_data = response.json()

                # Standardize user info across providers
                standardized_info = self.standardize_user_info(provider, user_data)
                return standardized_info

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during user info fetch: {e}")
            raise OAuthProviderError(f"Network error: {str(e)}")

    def standardize_user_info(self, provider: str, raw_data: Dict) -> Dict:
        """Standardize user info from different OAuth providers

        Args:
            provider: Provider name
            raw_data: Raw user data from provider

        Returns:
            Standardized user info dict with: id, email, username, avatar_url
        """
        if provider == "meta":
            return {
                "provider_id": raw_data.get("id"),
                "email": raw_data.get("email"),
                "username": raw_data.get("name"),
                "avatar_url": raw_data.get("picture", {}).get("data", {}).get("url"),
            }

        elif provider == "reddit":
            return {
                "provider_id": raw_data.get("id"),
                "email": None,  # Reddit doesn't provide email by default
                "username": raw_data.get("name"),
                "avatar_url": raw_data.get("icon_img"),
            }

        elif provider == "x":
            return {
                "provider_id": raw_data.get("data", {}).get("id"),
                "email": None,  # Twitter/X requires additional permissions
                "username": raw_data.get("data", {}).get("username"),
                "avatar_url": raw_data.get("data", {}).get("profile_image_url"),
            }

        elif provider == "discord":
            return {
                "provider_id": raw_data.get("id"),
                "email": raw_data.get("email"),
                "username": raw_data.get("username"),
                "avatar_url": (
                    f"https://cdn.discordapp.com/avatars/{raw_data.get('id')}/{raw_data.get('avatar')}.png"
                    if raw_data.get("avatar")
                    else None
                ),
            }

        else:
            # Generic fallback
            return {
                "provider_id": raw_data.get("id"),
                "email": raw_data.get("email"),
                "username": raw_data.get("username") or raw_data.get("name"),
                "avatar_url": raw_data.get("avatar_url"),
            }

    async def find_or_create_user(self, db: AsyncSession, provider: str, user_info: Dict) -> User:
        """Find existing user or create new one from OAuth data

        Args:
            db: Database session
            provider: OAuth provider name
            user_info: Standardized user info

        Returns:
            User object

        Raises:
            OAuthError: If user creation fails
        """
        from sqlalchemy import select
        from src.models.user import OAuthAccount, OAuth2Provider

        provider_id = user_info["provider_id"]

        # Convert provider string to OAuth2Provider enum
        try:
            provider_enum = OAuth2Provider(provider)
        except ValueError:
            raise OAuthError(f"Invalid OAuth provider: {provider}")

        # Try to find existing OAuth account
        result = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider_enum, OAuthAccount.oauth_id == provider_id
            )
        )
        oauth_account = result.scalar_one_or_none()

        if oauth_account:
            # Found existing OAuth account, return associated user
            await db.refresh(oauth_account, ["user"])
            logger.info(f"Found existing OAuth account for {provider}:{provider_id}")
            return oauth_account.user

        # Check if user exists by email (to link accounts)
        user = None
        if user_info.get("email"):
            result = await db.execute(select(User).where(User.email == user_info["email"]))
            user = result.scalar_one_or_none()

            if user:
                # Create OAuth account for existing user
                new_oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider_enum,
                    oauth_id=provider_id,
                    oauth_username=user_info.get("username"),
                    oauth_email=user_info.get("email"),
                    oauth_avatar_url=user_info.get("avatar_url"),
                    access_token=None,  # Not storing tokens for security
                )
                db.add(new_oauth_account)
                await db.commit()
                logger.info(f"Linked OAuth account {provider} to existing user: {user.email}")
                return user

        # Create new user with OAuth account
        username = user_info["username"] or f"{provider}_user_{provider_id[:8]}"

        # Ensure unique username
        base_username = username
        counter = 1
        while True:
            result = await db.execute(select(User).where(User.username == username))
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}_{counter}"
            counter += 1

        # Create user
        new_user = User(
            username=username,
            email=user_info.get("email") or f"{provider}_{provider_id}@oauth.local",
            password_hash=None,  # OAuth users don't have passwords
            level=UserLevelEnum.NEW_USER,
            points=config.point_economy.registration_bonus,
            is_active=True,
        )

        db.add(new_user)
        await db.flush()  # Get user.id before creating OAuth account

        # Create OAuth account
        new_oauth_account = OAuthAccount(
            user_id=new_user.id,
            provider=provider_enum,
            oauth_id=provider_id,
            oauth_username=user_info.get("username"),
            oauth_email=user_info.get("email"),
            oauth_avatar_url=user_info.get("avatar_url"),
            access_token=None,  # Not storing tokens for security
        )
        db.add(new_oauth_account)

        await db.commit()
        await db.refresh(new_user)

        logger.info(f"Created new OAuth user: {new_user.username} (provider: {provider})")

        return new_user


# Global service instance
oauth_service = OAuth2Service()
