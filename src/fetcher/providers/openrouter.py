"""OpenRouter provider for fetching models."""

from typing import List, Optional, Any, Dict
import httpx

from .base import BaseProvider
from ..models import ModelInfo, PricingInfo, ModelCapabilities


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider - supports the largest catalog of models."""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: Optional API key (not required for listing models)
            timeout: Request timeout in seconds
        """
        super().__init__(
            api_key=api_key, base_url=self.DEFAULT_BASE_URL, timeout=timeout
        )

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openrouter"

    def validate_credentials(self) -> bool:
        """API key not required for listing models."""
        return True

    async def fetch_models(self) -> List[ModelInfo]:
        """
        Fetch all available models from OpenRouter.

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
            raise Exception(f"Failed to fetch models from OpenRouter: {e}")

    def _parse_model(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        Parse a model from OpenRouter API response.

        Args:
            data: Raw model data from API

        Returns:
            ModelInfo object or None if parsing fails
        """
        try:
            model_id = data.get("id", "")
            if not model_id:
                return None

            # Parse pricing information
            pricing = None
            pricing_data = data.get("pricing", {})
            if pricing_data:
                pricing = PricingInfo(
                    prompt=self._parse_price(pricing_data.get("prompt")),
                    completion=self._parse_price(pricing_data.get("completion")),
                    image=self._parse_price(pricing_data.get("image")),
                    request=self._parse_price(pricing_data.get("request")),
                )

            # Parse capabilities
            capabilities = ModelCapabilities(
                supports_vision=self._supports_vision(data),
                supports_function_calling=self._supports_function_calling(data),
                supports_streaming=True,  # OpenRouter supports streaming by default
                modalities=self._extract_modalities(data),
            )

            # Extract context length
            context_length = data.get("context_length") or data.get("max_context_length")

            # Build metadata
            metadata = {
                "architecture": data.get("architecture", {}).get("tokenizer"),
                "top_provider": data.get("top_provider", {}).get("name"),
                "per_request_limits": data.get("per_request_limits"),
            }

            return ModelInfo(
                model_id=model_id,
                name=data.get("name", model_id),
                provider=self.name,
                description=data.get("description"),
                context_length=context_length,
                pricing=pricing,
                capabilities=capabilities,
                metadata={k: v for k, v in metadata.items() if v is not None},
            )

        except Exception as e:
            # Log the error but don't fail the entire fetch
            print(f"Warning: Failed to parse model {data.get('id', 'unknown')}: {e}")
            return None

    @staticmethod
    def _parse_price(price_str: Optional[str]) -> Optional[float]:
        """
        Parse price string to float.

        Args:
            price_str: Price as string (e.g., "0.000001")

        Returns:
            Price as float or None
        """
        if price_str is None:
            return None
        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _supports_vision(data: Dict[str, Any]) -> bool:
        """Check if model supports vision/image inputs."""
        modalities = data.get("architecture", {}).get("modality", "")
        return "image" in modalities.lower() if modalities else False

    @staticmethod
    def _supports_function_calling(data: Dict[str, Any]) -> bool:
        """Check if model supports function calling."""
        # OpenRouter doesn't always explicitly mark this, but we can infer
        # from supported parameters or model capabilities
        supported_params = data.get("supported_parameters", [])
        return "tools" in supported_params or "functions" in supported_params

    @staticmethod
    def _extract_modalities(data: Dict[str, Any]) -> List[str]:
        """Extract supported modalities from model data."""
        modalities = []
        modality_str = data.get("architecture", {}).get("modality", "")

        if modality_str:
            # Split on common delimiters
            for mod in modality_str.replace(",", "+").split("+"):
                mod = mod.strip().lower()
                if mod:
                    modalities.append(mod)

        # Always include text as a fallback
        if not modalities or "text" not in modalities:
            modalities.insert(0, "text")

        return modalities
