"""Configuration management for the fetcher."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Configuration manager for API keys and settings."""

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            env_file: Optional path to .env file
        """
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            # Try to load from default locations
            load_dotenv()

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: Provider name (e.g., 'openrouter', 'openai')

        Returns:
            API key or None if not found
        """
        # Convert provider name to environment variable format
        # e.g., 'openrouter' -> 'OPENROUTER_API_KEY'
        env_var = f"{provider.upper()}_API_KEY"
        return os.getenv(env_var)

    def get_base_url(self, provider: str) -> Optional[str]:
        """
        Get custom base URL for a provider.

        Args:
            provider: Provider name

        Returns:
            Base URL or None if not configured
        """
        env_var = f"{provider.upper()}_BASE_URL"
        return os.getenv(env_var)

    @staticmethod
    def get_data_dir() -> Path:
        """
        Get the data directory path.

        Returns:
            Path to data directory
        """
        data_dir = os.getenv("FETCHER_DATA_DIR", "data")
        return Path(data_dir)

    @staticmethod
    def get_timeout() -> float:
        """
        Get the HTTP request timeout.

        Returns:
            Timeout in seconds
        """
        timeout = os.getenv("FETCHER_TIMEOUT", "30.0")
        try:
            return float(timeout)
        except ValueError:
            return 30.0

    @staticmethod
    def is_debug_enabled() -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled
        """
        return os.getenv("FETCHER_DEBUG", "false").lower() in ("true", "1", "yes")
