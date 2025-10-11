"""Utility for loading provider configuration data from JSON files."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


def get_data_dir() -> Path:
    """
    Get the directory containing provider configuration files.

    Returns:
        Path to the provider_configs directory
    """
    # Get the directory where this file is located
    providers_dir = Path(__file__).parent
    # Go up to src/fetcher, then into data/provider_configs
    data_dir = providers_dir.parent / "data" / "provider_configs"
    return data_dir


@lru_cache(maxsize=None)
def load_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Load configuration data for a provider from JSON file.

    Uses LRU cache to avoid repeated file reads. The cache persists for the
    lifetime of the process.

    Args:
        provider_name: Name of the provider (e.g., "anthropic", "openai", "google")

    Returns:
        Dictionary containing "pricing" and "capabilities" mappings.
        Returns empty dicts if file doesn't exist or is invalid.

    Example:
        >>> config = load_provider_config("anthropic")
        >>> pricing = config.get("pricing", {})
        >>> capabilities = config.get("capabilities", {})
    """
    try:
        data_dir = get_data_dir()
        config_file = data_dir / f"{provider_name}.json"

        if not config_file.exists():
            print(f"Warning: Config file not found: {config_file}")
            return {"pricing": {}, "capabilities": {}}

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Validate structure
        if not isinstance(config, dict):
            print(f"Warning: Invalid config format in {config_file}: expected dict")
            return {"pricing": {}, "capabilities": {}}

        # Ensure required keys exist
        if "pricing" not in config:
            config["pricing"] = {}
        if "capabilities" not in config:
            config["capabilities"] = {}

        return config

    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON in {config_file}: {e}")
        return {"pricing": {}, "capabilities": {}}
    except Exception as e:
        print(f"Warning: Failed to load provider config for {provider_name}: {e}")
        return {"pricing": {}, "capabilities": {}}


def get_pricing_map(provider_name: str) -> Dict[str, Dict[str, float]]:
    """
    Get pricing mapping for a provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Dictionary mapping model IDs to pricing info
    """
    config = load_provider_config(provider_name)
    return config.get("pricing", {})


def get_capabilities_map(provider_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get capabilities mapping for a provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Dictionary mapping model IDs to capabilities info
    """
    config = load_provider_config(provider_name)
    return config.get("capabilities", {})


def clear_cache():
    """
    Clear the configuration cache.

    Useful for testing or when config files are updated at runtime.
    """
    load_provider_config.cache_clear()
