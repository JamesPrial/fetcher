"""OpenAI provider for fetching models."""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities


class OpenAIProvider(BaseProvider):
    """OpenAI provider - GPT models and more."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    # Static pricing mapping (per million tokens) based on official pricing
    # Source: https://openai.com/api/pricing/
    PRICING_MAP = {
        # GPT-5 series
        "gpt-5": {"prompt": 1.25, "completion": 10.00},
        "gpt-5-mini": {"prompt": 0.25, "completion": 2.00},
        "gpt-5-nano": {"prompt": 0.10, "completion": 0.50},
        # GPT-4o series
        "gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-2024-11-20": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-2024-08-06": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-2024-05-13": {"prompt": 5.00, "completion": 15.00},
        "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "gpt-4o-mini-2024-07-18": {"prompt": 0.15, "completion": 0.60},
        "chatgpt-4o-latest": {"prompt": 5.00, "completion": 15.00},
        # o1 series (reasoning models)
        "o1": {"prompt": 15.00, "completion": 60.00},
        "o1-2024-12-17": {"prompt": 15.00, "completion": 60.00},
        "o1-mini": {"prompt": 3.00, "completion": 12.00},
        "o1-mini-2024-09-12": {"prompt": 3.00, "completion": 12.00},
        "o1-preview": {"prompt": 15.00, "completion": 60.00},
        "o1-preview-2024-09-12": {"prompt": 15.00, "completion": 60.00},
        # GPT-4 Turbo
        "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-turbo-2024-04-09": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-turbo-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-0125-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-1106-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-1106-vision-preview": {"prompt": 10.00, "completion": 30.00},
        # GPT-4
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-4-0613": {"prompt": 30.00, "completion": 60.00},
        "gpt-4-32k": {"prompt": 60.00, "completion": 120.00},
        "gpt-4-32k-0613": {"prompt": 60.00, "completion": 120.00},
        # GPT-3.5 Turbo
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        "gpt-3.5-turbo-0125": {"prompt": 0.50, "completion": 1.50},
        "gpt-3.5-turbo-1106": {"prompt": 1.00, "completion": 2.00},
        "gpt-3.5-turbo-16k": {"prompt": 3.00, "completion": 4.00},
        # Embedding models (per million tokens)
        "text-embedding-3-small": {"prompt": 0.02, "completion": 0.0},
        "text-embedding-3-large": {"prompt": 0.13, "completion": 0.0},
        "text-embedding-ada-002": {"prompt": 0.10, "completion": 0.0},
    }

    # Capabilities mapping
    CAPABILITIES_MAP = {
        # GPT-5 series
        "gpt-5": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 272000,
            "modalities": ["text", "image"],
        },
        "gpt-5-mini": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 272000,
            "modalities": ["text", "image"],
        },
        "gpt-5-nano": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 272000,
            "modalities": ["text", "image"],
        },
        # GPT-4o series
        "gpt-4o": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4o-2024-11-20": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4o-2024-08-06": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4o-2024-05-13": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4o-mini": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4o-mini-2024-07-18": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "chatgpt-4o-latest": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        # o1 series (reasoning models - no streaming or vision)
        "o1": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 200000,
            "modalities": ["text"],
        },
        "o1-2024-12-17": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 200000,
            "modalities": ["text"],
        },
        "o1-mini": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "o1-mini-2024-09-12": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "o1-preview": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "o1-preview-2024-09-12": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 128000,
            "modalities": ["text"],
        },
        # GPT-4 Turbo
        "gpt-4-turbo": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4-turbo-2024-04-09": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        "gpt-4-turbo-preview": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "gpt-4-0125-preview": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "gpt-4-1106-preview": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text"],
        },
        "gpt-4-1106-vision-preview": {
            "vision": True,
            "function_calling": True,
            "streaming": True,
            "context_length": 128000,
            "modalities": ["text", "image"],
        },
        # GPT-4
        "gpt-4": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 8192,
            "modalities": ["text"],
        },
        "gpt-4-0613": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 8192,
            "modalities": ["text"],
        },
        "gpt-4-32k": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 32768,
            "modalities": ["text"],
        },
        "gpt-4-32k-0613": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 32768,
            "modalities": ["text"],
        },
        # GPT-3.5 Turbo
        "gpt-3.5-turbo": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 16385,
            "modalities": ["text"],
        },
        "gpt-3.5-turbo-0125": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 16385,
            "modalities": ["text"],
        },
        "gpt-3.5-turbo-1106": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 16385,
            "modalities": ["text"],
        },
        "gpt-3.5-turbo-16k": {
            "vision": False,
            "function_calling": True,
            "streaming": True,
            "context_length": 16385,
            "modalities": ["text"],
        },
        # Embedding models
        "text-embedding-3-small": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 8191,
            "modalities": ["text"],
        },
        "text-embedding-3-large": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 8191,
            "modalities": ["text"],
        },
        "text-embedding-ada-002": {
            "vision": False,
            "function_calling": False,
            "streaming": False,
            "context_length": 8191,
            "modalities": ["text"],
        },
    }

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize OpenAI provider.

        Args:
            api_key: Optional API key (recommended for production use)
            timeout: Request timeout in seconds
        """
        super().__init__(
            api_key=api_key, base_url=self.DEFAULT_BASE_URL, timeout=timeout
        )

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openai"

    def validate_credentials(self) -> bool:
        """API key is optional but recommended for OpenAI."""
        return True

    async def fetch_models(self) -> List[ModelInfo]:
        """
        Fetch all available models from OpenAI.

        Returns:
            List of ModelInfo objects

        Raises:
            httpx.HTTPError: If the API request fails
        """
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model = self._parse_model(model_data)
                if model:
                    models.append(model)

            return models

        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch models from OpenAI: {e}")

    def _parse_model(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        Parse a model from OpenAI API response.

        Args:
            data: Raw model data from API

        Returns:
            ModelInfo object or None if parsing fails
        """
        try:
            model_id = data.get("id", "")
            if not model_id:
                return None

            # Get pricing from static map (OpenAI API doesn't provide this)
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
                supports_function_calling=caps_data.get("function_calling", False),
                supports_streaming=caps_data.get("streaming", False),
                modalities=caps_data.get("modalities", ["text"]),
            )

            # Get context length from static map
            context_length = caps_data.get("context_length")

            # Build metadata
            metadata = {
                "object": data.get("object"),
                "created": data.get("created"),
                "owned_by": data.get("owned_by"),
            }

            # Determine if this is a fine-tuned model
            is_fine_tuned = model_id.startswith("ft:")

            # Generate description
            if is_fine_tuned:
                description = f"Fine-tuned OpenAI model: {model_id}"
            elif model_id.startswith("gpt-5"):
                description = "OpenAI GPT-5 - next-generation model with advanced reasoning and multimodal capabilities"
            elif model_id.startswith("gpt-4o"):
                description = "OpenAI GPT-4o - flagship model with vision and function calling"
            elif model_id.startswith("o1"):
                description = "OpenAI o1 - advanced reasoning model"
            elif model_id.startswith("gpt-4-turbo"):
                description = "OpenAI GPT-4 Turbo - fast and capable with large context"
            elif model_id.startswith("gpt-4"):
                description = "OpenAI GPT-4 - advanced language model"
            elif model_id.startswith("gpt-3.5"):
                description = "OpenAI GPT-3.5 Turbo - fast and cost-effective"
            elif "embedding" in model_id:
                description = f"OpenAI embedding model: {model_id}"
            else:
                description = f"OpenAI model: {model_id}"

            return ModelInfo(
                model_id=model_id,
                name=model_id,  # OpenAI uses ID as name
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
            print(f"Warning: Failed to parse model {data.get('id', 'unknown')}: {e}")
            return None
