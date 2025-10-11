"""Google provider for fetching models."""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities


class GoogleProvider(BaseProvider):
    """Google Gemini provider - multimodal AI models."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    # Static pricing mapping (per million tokens) based on official pricing
    # Source: https://ai.google.dev/gemini-api/docs/pricing
    PRICING_MAP = {
        # Gemini 2.5 Pro
        "gemini-2.5-pro": {"prompt": 1.25, "completion": 5.00},
        "gemini-2.5-pro-preview": {"prompt": 1.25, "completion": 5.00},
        "gemini-2.5-pro-latest": {"prompt": 1.25, "completion": 5.00},
        # Gemini 2.5 Flash
        "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
        "gemini-2.5-flash-preview": {"prompt": 0.075, "completion": 0.30},
        "gemini-2.5-flash-latest": {"prompt": 0.075, "completion": 0.30},
        # Gemini 2.0 Flash
        "gemini-2.0-flash": {"prompt": 0.10, "completion": 0.40},
        "gemini-2.0-flash-exp": {"prompt": 0.10, "completion": 0.40},
        "gemini-2.0-flash-preview": {"prompt": 0.10, "completion": 0.40},
        # Gemini 1.5 Pro
        "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
        "gemini-1.5-pro-latest": {"prompt": 1.25, "completion": 5.00},
        # Gemini 1.5 Flash
        "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
        "gemini-1.5-flash-latest": {"prompt": 0.075, "completion": 0.30},
        "gemini-1.5-flash-8b": {"prompt": 0.0375, "completion": 0.15},
        "gemini-1.5-flash-8b-latest": {"prompt": 0.0375, "completion": 0.15},
        # Gemini 1.0 Pro
        "gemini-1.0-pro": {"prompt": 0.50, "completion": 1.50},
        "gemini-1.0-pro-latest": {"prompt": 0.50, "completion": 1.50},
    }

    # Capabilities mapping
    CAPABILITIES_MAP = {
        # Gemini 2.5 models - Full multimodal
        "gemini-2.5-pro": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.5-pro-preview": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.5-pro-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.5-flash": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.5-flash-preview": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.5-flash-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        # Gemini 2.0 models
        "gemini-2.0-flash": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.0-flash-exp": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-2.0-flash-preview": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        # Gemini 1.5 models
        "gemini-1.5-pro": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-1.5-pro-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-1.5-flash": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-1.5-flash-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-1.5-flash-8b": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        "gemini-1.5-flash-8b-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image", "video", "audio"],
        },
        # Gemini 1.0 models - Text and image only
        "gemini-1.0-pro": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image"],
        },
        "gemini-1.0-pro-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "modalities": ["text", "image"],
        },
    }

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize Google provider.

        Args:
            api_key: Required API key for authentication
            timeout: Request timeout in seconds
        """
        super().__init__(
            api_key=api_key, base_url=self.DEFAULT_BASE_URL, timeout=timeout
        )

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
