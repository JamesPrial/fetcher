"""Anthropic provider for fetching models."""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities
from .data_loader import get_pricing_map, get_capabilities_map


class AnthropicProvider(BaseProvider):
    """Anthropic provider - Claude models."""

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    # Pricing and capabilities loaded from JSON config files
    # Source: src/fetcher/data/provider_configs/anthropic.json
    # Based on official pricing: https://www.anthropic.com/pricing
    PRICING_MAP: Dict[str, Dict[str, float]] = {}
    CAPABILITIES_MAP: Dict[str, Dict[str, Any]] = {}

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Required API key for authentication
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, base_url=self.DEFAULT_BASE_URL, timeout=timeout)

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "anthropic"

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get or create the HTTP client with Anthropic-specific headers.

        Overrides base class to use x-api-key header instead of Bearer auth.
        """
        if self._client is None:
            headers = {
                "anthropic-version": self.API_VERSION,
            }

            if self.api_key:
                headers["x-api-key"] = self.api_key

            client_kwargs = {
                "headers": headers,
                "timeout": self.timeout,
                "follow_redirects": True,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self._client = httpx.AsyncClient(**client_kwargs)
        return self._client

    def validate_credentials(self) -> bool:
        """API key is required for Anthropic."""
        return self.api_key is not None

    async def fetch_models(self) -> List[ModelInfo]:
        """
        Fetch all available models from Anthropic.

        Returns:
            List of ModelInfo objects

        Raises:
            httpx.HTTPError: If the API request fails
        """
        if not self.validate_credentials():
            raise ValueError("API key is required for Anthropic provider")

        try:
            models = []
            after_id = None
            limit = 100  # Max allowed per page

            # Paginate through all models
            while True:
                params = {"limit": limit}
                if after_id:
                    params["after_id"] = after_id

                response = await self.client.get("/models", params=params)
                response.raise_for_status()
                data = response.json()

                # Parse models from this page
                page_models = data.get("data", [])
                for model_data in page_models:
                    model = self._parse_model(model_data)
                    if model:
                        models.append(model)

                # Check if there are more pages
                has_more = data.get("has_more", False)
                if not has_more or not page_models:
                    break

                # Get the last model ID for pagination
                after_id = page_models[-1].get("id")

            return models

        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch models from Anthropic: {e}")

    def _parse_model(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        Parse a model from Anthropic API response.

        Args:
            data: Raw model data from API

        Returns:
            ModelInfo object or None if parsing fails
        """
        try:
            model_id = data.get("id", "")
            if not model_id:
                return None

            # Get pricing from static map (Anthropic API doesn't provide this)
            pricing = None
            if model_id in self.PRICING_MAP:
                pricing_data = self.PRICING_MAP[model_id]
                pricing = PricingInfo(
                    prompt=pricing_data.get("prompt"),
                    completion=pricing_data.get("completion"),
                    currency="USD",
                )

            # Get capabilities from static map
            caps_data = self.CAPABILITIES_MAP.get(model_id, {})
            capabilities = ModelCapabilities(
                supports_vision=caps_data.get("vision", False),
                supports_function_calling=caps_data.get("function_calling", True),
                supports_streaming=caps_data.get("streaming", True),
                modalities=caps_data.get("modalities", ["text"]),
            )

            # Get context length from static map
            context_length = caps_data.get("context_length")

            # Build metadata
            metadata = {
                "type": data.get("type"),
                "created_at": data.get("created_at"),
            }

            return ModelInfo(
                model_id=model_id,
                name=data.get("display_name", model_id),
                provider=self.name,
                description=f"Anthropic Claude model: {data.get('display_name', model_id)}",
                context_length=context_length,
                pricing=pricing,
                capabilities=capabilities,
                metadata={k: v for k, v in metadata.items() if v is not None},
                updated_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            # Log the error but don't fail the entire fetch
            print(f"Warning: Failed to parse model {data.get('id', 'unknown')}: {e}")
            return None


# Load pricing and capabilities at module level to support class-level access
AnthropicProvider.PRICING_MAP = get_pricing_map("anthropic")
AnthropicProvider.CAPABILITIES_MAP = get_capabilities_map("anthropic")
