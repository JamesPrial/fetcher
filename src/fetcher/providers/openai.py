"""OpenAI provider for fetching models."""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities
from .data_loader import get_pricing_map, get_capabilities_map


class OpenAIProvider(BaseProvider):
    """OpenAI provider - GPT models and more."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    # Pricing and capabilities loaded from JSON config files
    # Source: src/fetcher/data/provider_configs/openai.json
    # Based on official pricing: https://openai.com/api/pricing/
    PRICING_MAP: Dict[str, Dict[str, float]] = {}
    CAPABILITIES_MAP: Dict[str, Dict[str, Any]] = {}

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
            elif model_id == "gpt-5-codex":
                description = "OpenAI GPT-5 Codex - specialized coding model with multimodal capabilities"
            elif model_id.startswith("gpt-5"):
                description = "OpenAI GPT-5 - next-generation model with advanced reasoning and multimodal capabilities"
            elif model_id.startswith("gpt-4.1"):
                description = "OpenAI GPT-4.1 - advanced model with 1M token context window"
            elif model_id.startswith("gpt-4o"):
                description = "OpenAI GPT-4o - flagship model with vision and function calling"
            elif model_id.startswith("o3") or model_id.startswith("o4"):
                description = "OpenAI o3/o4 - next-generation reasoning model with vision and multimodal capabilities"
            elif model_id.startswith("o1"):
                description = "OpenAI o1 - advanced reasoning model"
            elif model_id.startswith("gpt-4-turbo"):
                description = "OpenAI GPT-4 Turbo - fast and capable with large context"
            elif model_id.startswith("gpt-4"):
                description = "OpenAI GPT-4 - advanced language model"
            elif model_id.startswith("gpt-3.5"):
                description = "OpenAI GPT-3.5 Turbo - fast and cost-effective"
            elif "codex" in model_id:
                description = f"OpenAI Codex model - specialized for code generation: {model_id}"
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


# Load pricing and capabilities at module level to support class-level access
OpenAIProvider.PRICING_MAP = get_pricing_map("openai")
OpenAIProvider.CAPABILITIES_MAP = get_capabilities_map("openai")
