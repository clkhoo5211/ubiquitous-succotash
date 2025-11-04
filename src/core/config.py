"""Application Configuration

Loads configuration from config.yaml and environment variables.
Follows Pydantic BaseSettings for type safety and validation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    """Application-wide settings"""

    model_config = {"env_prefix": "APP_"}

    name: str = "Decentralized Forum"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = Field(default=True)
    secret_key: str = Field(
        min_length=32, description="Must be set via APP_SECRET_KEY environment variable"
    )
    allowed_hosts: List[str] = Field(default_factory=lambda: ["*"])
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"]
    )


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    model_config = {"env_prefix": "DATABASE_"}

    url: PostgresDsn
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    echo: bool = Field(default=False)


class RedisSettings(BaseSettings):
    """Redis cache configuration"""

    model_config = {"env_prefix": "REDIS_"}

    url: RedisDsn
    max_connections: int = Field(default=50)
    decode_responses: bool = Field(default=True)


class OAuth2ProviderSettings(BaseSettings):
    """OAuth2 provider configuration"""

    client_id: str
    client_secret: Optional[str] = None  # Optional for testing
    redirect_uri: str
    scope: str


class TelegramSettings(BaseSettings):
    """Telegram Bot Login configuration"""

    bot_token: Optional[str] = None  # Optional for testing
    bot_username: str


class PaymentSettings(BaseSettings):
    """Payment and blockchain configuration"""

    method: str = "crypto"
    recipient_address: str
    supported_tokens: Dict[str, Any] = {}
    pancakeswap_router: str = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    bnb_chain_rpc: str = "https://bsc-dataseed.binance.org/"
    gas_limit: int = 200000


class IPFSSettings(BaseSettings):
    """IPFS Lighthouse configuration"""

    model_config = {"env_prefix": "IPFS_"}

    api_key: str
    upload_endpoint: str = "https://node.lighthouse.storage/api/v0/add"
    gateway_url: str = "https://gateway.lighthouse.storage/ipfs/"
    max_file_size_mb: int = 50


class PointEconomySettings(BaseSettings):
    """Point economy configuration"""

    registration_bonus: int = 100
    create_post_cost: int = 5
    create_comment_cost: int = 2
    like_cost: int = 1
    receive_like_reward_tier1: int = 3  # 1st like
    receive_like_reward_tier2: int = 30  # 10th like
    receive_like_reward_tier3: int = 350  # 100th like
    crypto_reward_cost: int = 10000  # Points to convert to 0.01 BNB


class UserLevelSettings(BaseSettings):
    """User level/tier configuration"""

    level_0_min: int = 0  # New User
    level_1_min: int = 100  # Active User
    level_2_min: int = 500  # Trusted User
    level_3_min: int = 2000  # Moderator
    level_4_min: int = 10000  # Senior Moderator
    level_5_min: int = 50000  # Admin


class SecuritySettings(BaseSettings):
    """Security configuration"""

    model_config = {"env_prefix": "SECURITY_"}

    jwt_secret_key: str = Field(
        min_length=32, description="Must be set via SECURITY_JWT_SECRET_KEY environment variable"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=30)
    session_expiration_hours: int = Field(default=720)  # 30 days
    bcrypt_rounds: int = Field(default=12)
    max_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=30)


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration"""

    anonymous_limit: int = 100  # per hour
    authenticated_limit: int = 1000  # per hour
    moderator_limit: int = 5000  # per hour


class Config:
    """Main application configuration loader"""

    def __init__(self, config_path: Optional[str] = None):
        """Load configuration from YAML file and environment variables"""
        if config_path is None:
            # Try config.local.yaml first, fall back to config.yaml
            project_root = Path(__file__).parent.parent.parent
            if (project_root / "config.local.yaml").exists():
                config_path = str(project_root / "config.local.yaml")
            else:
                config_path = str(project_root / "config.yaml")

        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)

        # Initialize all settings
        self.app = self._load_section("application", ApplicationSettings)
        self.database = self._load_section("database", DatabaseSettings)
        self.redis = self._load_section("redis", RedisSettings)
        self.security = self._load_section("security", SecuritySettings)
        self.point_economy = self._load_section("point_economy", PointEconomySettings)
        self.user_levels = self._load_section("user_levels", UserLevelSettings)
        self.rate_limit = self._load_section("rate_limit", RateLimitSettings)
        self.ipfs = self._load_section("ipfs", IPFSSettings)
        self.payments = self._load_section("payments", PaymentSettings)

        # OAuth2 providers
        self.oauth_meta = self._load_section("oauth.meta", OAuth2ProviderSettings, prefix="META")
        self.oauth_reddit = self._load_section(
            "oauth.reddit", OAuth2ProviderSettings, prefix="REDDIT"
        )
        self.oauth_twitter = self._load_section(
            "oauth.twitter", OAuth2ProviderSettings, prefix="TWITTER"
        )
        self.oauth_discord = self._load_section(
            "oauth.discord", OAuth2ProviderSettings, prefix="DISCORD"
        )
        self.oauth_telegram = self._load_section(
            "oauth.telegram", TelegramSettings, prefix="TELEGRAM"
        )

    def _load_section(
        self, path: str, settings_class: type, prefix: Optional[str] = None
    ) -> BaseSettings:
        """Load a configuration section from YAML and merge with environment variables

        Environment variables take precedence over YAML values for security.
        Secrets should NEVER be stored in YAML files.
        """
        # Navigate nested YAML structure
        parts = path.split(".")
        data = self._config
        for part in parts:
            data = data.get(part, {})

        # Remove sensitive keys from YAML data - must come from environment
        sensitive_keys = {"secret_key", "jwt_secret_key", "client_secret", "bot_token", "api_key"}
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k not in sensitive_keys}

        # Create settings instance (Pydantic will automatically read env vars)
        # Environment variables take precedence over YAML values
        try:
            return settings_class(**data)
        except Exception as e:
            # If validation fails, provide more context
            raise ValueError(f"Failed to load config section '{path}': {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a raw configuration value by dot notation path"""
        parts = key.split(".")
        value = self._config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default
        return value


# Global configuration instance
config = Config()
