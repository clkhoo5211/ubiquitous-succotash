"""
Configuration loader for the Decentralized Forum application.

Loads configuration from config.yaml and merges with config.local.yaml overrides.
"""

import yaml
from pathlib import Path
from typing import Any, Dict
from functools import lru_cache


class Config:
    """Configuration management class."""

    def __init__(self, base_path: Path = None):
        """
        Initialize configuration.

        Args:
            base_path: Base path for configuration files. Defaults to project root.
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = base_path
        self.config_file = base_path / "config.yaml"
        self.local_config_file = base_path / "config.local.yaml"

        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML files."""
        # Load base configuration
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Base config file not found: {self.config_file}")

        # Merge local configuration (overrides)
        if self.local_config_file.exists():
            with open(self.local_config_file, "r") as f:
                local_config = yaml.safe_load(f) or {}
                self._merge_config(self._config, local_config)

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.

        Args:
            path: Dot-separated configuration path (e.g., "database.url")
            default: Default value if path not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get("database.url")
            "postgresql://..."
            >>> config.get("points_economy.registration_bonus")
            100
        """
        keys = path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Top-level configuration section name

        Returns:
            Configuration section dictionary

        Examples:
            >>> config.get_section("database")
            {"url": "postgresql://...", "pool_size": 10, ...}
        """
        return self._config.get(section, {})

    @property
    def all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self._config

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to top-level config sections."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Check if top-level key exists in configuration."""
        return key in self._config


@lru_cache()
def get_config() -> Config:
    """
    Get cached configuration instance.

    Returns:
        Singleton Config instance

    Examples:
        >>> from src.config import get_config
        >>> config = get_config()
        >>> db_url = config.get("database.url")
    """
    return Config()


# Convenience exports
config = get_config()

# Quick access to common config sections
APP_CONFIG = config.get_section("application")
DB_CONFIG = config.get_section("database")
REDIS_CONFIG = config.get_section("redis")
OAUTH_CONFIG = config.get_section("oauth")
PAYMENT_CONFIG = config.get_section("payments")
BLOCKCHAIN_CONFIG = config.get_section("blockchain")
STORAGE_CONFIG = config.get_section("file_storage")
EMAIL_CONFIG = config.get_section("email")
SECURITY_CONFIG = config.get_section("security")
POINTS_CONFIG = config.get_section("points_economy")
LEVELS_CONFIG = config.get_section("user_progression")
FEATURES_CONFIG = config.get_section("features")


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print("✅ Configuration loaded successfully!")
    print(f"Environment: {config.get('application.environment')}")
    print(f"Debug Mode: {config.get('application.debug')}")
    print(f"Database URL: {config.get('database.url')}")
    print(f"Registration Bonus: {config.get('points_economy.registration_bonus')} points")
