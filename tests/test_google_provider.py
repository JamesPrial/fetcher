"""Tests for GoogleProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fetcher.providers.google import GoogleProvider
from fetcher.models import ModelInfo, PricingInfo, ModelCapabilities


class TestGoogleProvider:
    """Test suite for GoogleProvider."""

    def test_provider_name(self):
        """Test that provider name is correct."""
        provider = GoogleProvider(api_key="test-key")
        assert provider.name == "google"

    def test_validate_credentials_with_key(self):
        """Test credential validation with API key."""
        provider = GoogleProvider(api_key="test-key")
        assert provider.validate_credentials() is True

    def test_validate_credentials_without_key(self):
        """Test credential validation without API key."""
        provider = GoogleProvider()
        assert provider.validate_credentials() is False

    def test_client_headers(self):
        """Test that client has correct Google headers."""
        provider = GoogleProvider(api_key="test-key")
        client = provider.client

        assert "x-goog-api-key" in client.headers
        assert client.headers["x-goog-api-key"] == "test-key"

    def test_client_without_api_key(self):
        """Test that client can be created without API key."""
        provider = GoogleProvider()
        client = provider.client

        assert "x-goog-api-key" not in client.headers

    @pytest.mark.asyncio
    async def test_fetch_models_without_api_key(self):
        """Test that fetch_models raises error without API key."""
        provider = GoogleProvider()

        with pytest.raises(ValueError, match="API key is required"):
            await provider.fetch_models()

    @pytest.mark.asyncio
    async def test_fetch_models_single_page(self):
        """Test fetching models with single page response."""
        provider = GoogleProvider(api_key="test-key")

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "displayName": "Gemini 2.5 Flash",
                    "description": "Fast and versatile performance across a diverse variety of tasks",
                    "inputTokenLimit": 1000000,
                    "outputTokenLimit": 8192,
                    "supportedGenerationMethods": ["generateContent", "countTokens"],
                    "version": "001",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()

        # Create a mock client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Set the internal _client to bypass the property
        provider._client = mock_client

        models = await provider.fetch_models()

        # Verify request
        mock_client.get.assert_called_once_with("/models", params={"pageSize": 50})

        # Verify results
        assert len(models) == 1
        assert models[0].model_id == "gemini-2.5-flash"
        assert models[0].name == "Gemini 2.5 Flash"
        assert models[0].provider == "google"
        assert models[0].context_length == 1000000

    @pytest.mark.asyncio
    async def test_fetch_models_pagination(self):
        """Test fetching models with pagination."""
        provider = GoogleProvider(api_key="test-key")

        # Mock responses for pagination
        page1_response = MagicMock()
        page1_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "displayName": "Gemini 2.5 Flash",
                    "description": "Fast model",
                    "inputTokenLimit": 1000000,
                    "outputTokenLimit": 8192,
                }
            ],
            "nextPageToken": "next-token-123",
        }
        page1_response.raise_for_status = MagicMock()

        page2_response = MagicMock()
        page2_response.json.return_value = {
            "models": [
                {
                    "name": "models/gemini-2.5-pro",
                    "displayName": "Gemini 2.5 Pro",
                    "description": "Pro model",
                    "inputTokenLimit": 2000000,
                    "outputTokenLimit": 8192,
                }
            ],
        }
        page2_response.raise_for_status = MagicMock()

        # Create a mock client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=[page1_response, page2_response])

        # Set the internal _client to bypass the property
        provider._client = mock_client

        models = await provider.fetch_models()

        # Verify requests
        assert mock_client.get.call_count == 2
        mock_client.get.assert_any_call("/models", params={"pageSize": 50})
        mock_client.get.assert_any_call(
            "/models", params={"pageSize": 50, "pageToken": "next-token-123"}
        )

        # Verify results
        assert len(models) == 2
        assert models[0].model_id == "gemini-2.5-flash"
        assert models[1].model_id == "gemini-2.5-pro"

    def test_parse_model_with_pricing(self):
        """Test parsing model with pricing information."""
        provider = GoogleProvider(api_key="test-key")

        model_data = {
            "name": "models/gemini-2.5-flash",
            "displayName": "Gemini 2.5 Flash",
            "description": "Fast and versatile performance",
            "inputTokenLimit": 1000000,
            "outputTokenLimit": 8192,
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.model_id == "gemini-2.5-flash"
        assert model.name == "Gemini 2.5 Flash"
        assert model.provider == "google"

        # Check pricing (from static mapping)
        assert model.pricing is not None
        assert model.pricing.prompt == 0.075
        assert model.pricing.completion == 0.30
        assert model.pricing.currency == "USD"

    def test_parse_model_with_capabilities(self):
        """Test parsing model with capabilities."""
        provider = GoogleProvider(api_key="test-key")

        model_data = {
            "name": "models/gemini-2.5-pro",
            "displayName": "Gemini 2.5 Pro",
            "description": "Pro model",
            "inputTokenLimit": 2000000,
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.capabilities.supports_vision is True
        assert model.capabilities.supports_function_calling is True
        assert model.capabilities.supports_streaming is True
        assert "text" in model.capabilities.modalities
        assert "image" in model.capabilities.modalities
        assert "video" in model.capabilities.modalities
        assert "audio" in model.capabilities.modalities

    def test_parse_model_without_pricing(self):
        """Test parsing model without pricing in static map."""
        provider = GoogleProvider(api_key="test-key")

        model_data = {
            "name": "models/unknown-model",
            "displayName": "Unknown Model",
            "description": "Unknown",
            "inputTokenLimit": 10000,
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.model_id == "unknown-model"
        assert model.pricing is None

    def test_parse_model_with_metadata(self):
        """Test parsing model with metadata."""
        provider = GoogleProvider(api_key="test-key")

        model_data = {
            "name": "models/gemini-2.5-flash",
            "displayName": "Gemini 2.5 Flash",
            "description": "Fast model",
            "inputTokenLimit": 1000000,
            "outputTokenLimit": 8192,
            "supportedGenerationMethods": ["generateContent", "countTokens"],
            "baseModelId": "models/gemini-2.0",
            "version": "001",
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert "full_name" in model.metadata
        assert model.metadata["full_name"] == "models/gemini-2.5-flash"
        assert "output_token_limit" in model.metadata
        assert model.metadata["output_token_limit"] == 8192
        assert "supported_methods" in model.metadata
        assert model.metadata["supported_methods"] == ["generateContent", "countTokens"]
        assert "base_model_id" in model.metadata
        assert model.metadata["base_model_id"] == "models/gemini-2.0"
        assert "version" in model.metadata
        assert model.metadata["version"] == "001"

    def test_parse_model_invalid_data(self):
        """Test parsing model with invalid data."""
        provider = GoogleProvider(api_key="test-key")

        # Model without name
        model = provider._parse_model({})
        assert model is None

        # Model with empty name
        model = provider._parse_model({"name": ""})
        assert model is None

    def test_model_id_normalization(self):
        """Test that model IDs are normalized correctly."""
        provider = GoogleProvider(api_key="test-key")

        model_data = {
            "name": "models/gemini-2.5-flash",
            "displayName": "Gemini 2.5 Flash",
            "inputTokenLimit": 1000000,
        }

        model = provider._parse_model(model_data)

        assert model is not None
        # Model ID should have "models/" prefix stripped
        assert model.model_id == "gemini-2.5-flash"
        # Full name should be preserved in metadata
        assert model.metadata["full_name"] == "models/gemini-2.5-flash"

    def test_pricing_map_completeness(self):
        """Test that all models in pricing map have expected fields."""
        for model_id, pricing in GoogleProvider.PRICING_MAP.items():
            assert "prompt" in pricing
            assert "completion" in pricing
            assert pricing["prompt"] > 0
            assert pricing["completion"] > 0

    def test_capabilities_map_completeness(self):
        """Test that all models in capabilities map have expected fields."""
        for model_id, caps in GoogleProvider.CAPABILITIES_MAP.items():
            assert "vision" in caps
            assert "function_calling" in caps
            assert "streaming" in caps
            assert "modalities" in caps
            assert isinstance(caps["modalities"], list)
            assert len(caps["modalities"]) > 0

    def test_pricing_and_capabilities_consistency(self):
        """Test that pricing map and capabilities map have consistent model IDs."""
        # Get model IDs from both maps
        pricing_ids = set(GoogleProvider.PRICING_MAP.keys())
        capabilities_ids = set(GoogleProvider.CAPABILITIES_MAP.keys())

        # They should be the same
        assert pricing_ids == capabilities_ids, (
            f"Pricing and capabilities maps have inconsistent model IDs.\n"
            f"Only in pricing: {pricing_ids - capabilities_ids}\n"
            f"Only in capabilities: {capabilities_ids - pricing_ids}"
        )

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        provider = GoogleProvider(api_key="test-key")

        async with provider as p:
            assert p is provider
            # Access client to create it
            _ = provider.client
            assert provider._client is not None

        # Client should be closed after context manager exits
        assert provider._client is None

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the provider."""
        provider = GoogleProvider(api_key="test-key")

        # Access client to create it
        _ = provider.client
        assert provider._client is not None

        # Close should clear the client
        await provider.close()
        assert provider._client is None

    def test_default_base_url(self):
        """Test that default base URL is correct."""
        provider = GoogleProvider(api_key="test-key")
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        provider = GoogleProvider(api_key="test-key", timeout=60.0)
        assert provider.timeout == 60.0
