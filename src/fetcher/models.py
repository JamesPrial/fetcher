"""Pydantic models for structured model data."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class PricingInfo(BaseModel):
    """Pricing information for a model."""

    prompt: Optional[float] = Field(None, description="Cost per prompt token")
    completion: Optional[float] = Field(None, description="Cost per completion token")
    image: Optional[float] = Field(None, description="Cost per image")
    request: Optional[float] = Field(None, description="Cost per request")
    currency: str = Field("USD", description="Currency code")


class ModelCapabilities(BaseModel):
    """Capabilities and features of a model."""

    supports_vision: bool = Field(False, description="Supports image inputs")
    supports_function_calling: bool = Field(False, description="Supports function calling")
    supports_streaming: bool = Field(False, description="Supports streaming responses")
    modalities: List[str] = Field(default_factory=list, description="Supported modalities")


class ModelInfo(BaseModel):
    """Information about a single model."""

    model_id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="Provider name (e.g., openrouter, openai)")
    description: Optional[str] = Field(None, description="Model description")
    context_length: Optional[int] = Field(None, description="Maximum context window size")
    pricing: Optional[PricingInfo] = Field(None, description="Pricing information")
    capabilities: ModelCapabilities = Field(
        default_factory=lambda: ModelCapabilities(supports_function_calling=False, supports_vision=False, supports_streaming=False), description="Model capabilities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific metadata"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProviderInfo(BaseModel):
    """Information about a provider."""

    name: str = Field(..., description="Provider name")
    model_count: int = Field(0, description="Number of models from this provider")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last fetch timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ModelCatalog(BaseModel):
    """Complete catalog of fetched models."""

    models: List[ModelInfo] = Field(default_factory=list, description="List of all models")
    providers: Dict[str, ProviderInfo] = Field(
        default_factory=dict, description="Provider information"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Catalog last update timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def add_model(self, model: ModelInfo) -> None:
        """Add a model to the catalog and update provider info."""
        self.models.append(model)

        # Update provider info
        if model.provider not in self.providers:
            self.providers[model.provider] = ProviderInfo(name=model.provider, model_count=0)

        self.providers[model.provider].model_count += 1
        self.providers[model.provider].last_updated = datetime.now()
        self.last_updated = datetime.now()

    def get_models_by_provider(self, provider: str) -> List[ModelInfo]:
        """Get all models from a specific provider."""
        return [m for m in self.models if m.provider == provider]
