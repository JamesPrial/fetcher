"""Google provider for fetching models."""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities
from .data_loader import get_pricing_map, get_capabilities_map


class GoogleProvider(BaseProvider):
    """Google Gemini provider - multimodal AI models."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    # Pricing and capabilities loaded from JSON config files
    # Source: src/fetcher/data/provider_configs/google.json
    # Based on official pricing: https://ai.google.dev/gemini-api/docs/pricing
    PRICING_MAP: Dict[str, Dict[str, float]] = {}
    CAPABILITIES_MAP: Dict[str, Dict[str, Any]] = {}

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize Google provider.

        Args:
            api_key: Required API key for authentication
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, base_url=self.DEFAULT_BASE_URL, timeout=timeout)

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "google"

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get or create the HTTP client with Google-specific headers.

        Overrides base class to use x-goog-api-key header instead of Bearer auth.
        """
        if self._client is None:
            headers = {}

            if self.api_key:
                headers["x-goog-api-key"] = self.api_key

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
        """API key is required for Google."""
        return self.api_key is not None

    async def fetch_models(self) -> List[ModelInfo]:
        """
        Fetch all available models from Google.

        Returns:
            List of ModelInfo objects

        Raises:
            httpx.HTTPError: If the API request fails
        """
        if not self.validate_credentials():
            raise ValueError("API key is required for Google provider")

        try:
            models = []
            page_token = None
            page_size = 50  # Default page size, max 1000

            # Paginate through all models
            while True:
                params = {"pageSize": page_size}
                if page_token:
                    params["pageToken"] = page_token

                response = await self.client.get("/models", params=params)
                response.raise_for_status()
                data = response.json()

                # Parse models from this page
                page_models = data.get("models", [])
                for model_data in page_models:
                    model = self._parse_model(model_data)
                    if model:
                        models.append(model)

                # Check if there are more pages
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            return models

        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch models from Google: {e}")

    def _parse_model(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        Parse a model from Google API response.

        Args:
            data: Raw model data from API

        Returns:
            ModelInfo object or None if parsing fails
        """
        try:
            # Get full model name (e.g., "models/gemini-2.5-flash")
            full_name = data.get("name", "")
            if not full_name:
                return None

            # Normalize model ID by stripping "models/" prefix
            model_id = full_name.replace("models/", "")

            # Get display name
            display_name = data.get("displayName", model_id)

            # Get description
            description = data.get("description", f"Google Gemini model: {display_name}")

            # Get context length from inputTokenLimit
            context_length = data.get("inputTokenLimit")

            # Get pricing from static map (Google API doesn't provide this)
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

            # Build metadata
            metadata = {
                "full_name": full_name,
                "output_token_limit": data.get("outputTokenLimit"),
                "supported_methods": data.get("supportedGenerationMethods", []),
                "base_model_id": data.get("baseModelId"),
                "version": data.get("version"),
            }

            return ModelInfo(
                model_id=model_id,
                name=display_name,
                provider=self.name,
                description=description,
                context_length=context_length,
                pricing=pricing,
                capabilities=capabilities,
                metadata={k: v for k, v in metadata.items() if v is not None},
                updated_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            # Log the error but don't fail the entire fetch
            print(f"Warning: Failed to parse model {data.get('name', 'unknown')}: {e}")
            return None


# Load pricing and capabilities at module level to support class-level access
GoogleProvider.PRICING_MAP = get_pricing_map("google")
GoogleProvider.CAPABILITIES_MAP = get_capabilities_map("google")
