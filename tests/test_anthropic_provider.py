"""Tests for AnthropicProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fetcher.providers.anthropic import AnthropicProvider
from fetcher.models import ModelInfo, PricingInfo, ModelCapabilities


class TestAnthropicProvider:
    """Test suite for AnthropicProvider."""

    def test_provider_name(self):
        """Test that provider name is correct."""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.name == "anthropic"

    def test_validate_credentials_with_key(self):
        """Test credential validation with API key."""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.validate_credentials() is True

    def test_validate_credentials_without_key(self):
        """Test credential validation without API key."""
        provider = AnthropicProvider()
        assert provider.validate_credentials() is False

    def test_client_headers(self):
        """Test that client has correct Anthropic headers."""
        provider = AnthropicProvider(api_key="test-key")
        client = provider.client

        assert "x-api-key" in client.headers
        assert client.headers["x-api-key"] == "test-key"
        assert "anthropic-version" in client.headers
        assert client.headers["anthropic-version"] == "2023-06-01"

    def test_client_without_api_key(self):
        """Test that client can be created without API key."""
        provider = AnthropicProvider()
        client = provider.client

        assert "x-api-key" not in client.headers
        assert "anthropic-version" in client.headers

    @pytest.mark.asyncio
    async def test_fetch_models_without_api_key(self):
        """Test that fetch_models raises error without API key."""
        provider = AnthropicProvider()

        with pytest.raises(ValueError, match="API key is required"):
            await provider.fetch_models()

    @pytest.mark.asyncio
    async def test_fetch_models_single_page(self):
        """Test fetching models with single page response."""
        provider = AnthropicProvider(api_key="test-key")

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "display_name": "Claude 3.5 Sonnet",
                    "type": "model",
                    "created_at": "2024-10-22T00:00:00Z",
                }
            ],
            "has_more": False,
        }
        mock_response.raise_for_status = MagicMock()

        # Create a mock client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # Set the internal _client to bypass the property
        provider._client = mock_client

        models = await provider.fetch_models()

        # Verify request
        mock_client.get.assert_called_once_with("/models", params={"limit": 100})

        # Verify results
        assert len(models) == 1
        assert models[0].model_id == "claude-3-5-sonnet-20241022"
        assert models[0].name == "Claude 3.5 Sonnet"
        assert models[0].provider == "anthropic"

    @pytest.mark.asyncio
    async def test_fetch_models_pagination(self):
        """Test fetching models with pagination."""
        provider = AnthropicProvider(api_key="test-key")

        # Mock responses for pagination
        page1_response = MagicMock()
        page1_response.json.return_value = {
            "data": [
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "display_name": "Claude 3.5 Sonnet",
                    "type": "model",
                    "created_at": "2024-10-22T00:00:00Z",
                }
            ],
            "has_more": True,
        }
        page1_response.raise_for_status = MagicMock()

        page2_response = MagicMock()
        page2_response.json.return_value = {
            "data": [
                {
                    "id": "claude-3-opus-20240229",
                    "display_name": "Claude 3 Opus",
                    "type": "model",
                    "created_at": "2024-02-29T00:00:00Z",
                }
            ],
            "has_more": False,
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
        mock_client.get.assert_any_call("/models", params={"limit": 100})
        mock_client.get.assert_any_call(
            "/models", params={"limit": 100, "after_id": "claude-3-5-sonnet-20241022"}
        )

        # Verify results
        assert len(models) == 2
        assert models[0].model_id == "claude-3-5-sonnet-20241022"
        assert models[1].model_id == "claude-3-opus-20240229"

    def test_parse_model_with_pricing(self):
        """Test parsing model with pricing information."""
        provider = AnthropicProvider(api_key="test-key")

        model_data = {
            "id": "claude-3-5-sonnet-20241022",
            "display_name": "Claude 3.5 Sonnet",
            "type": "model",
            "created_at": "2024-10-22T00:00:00Z",
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.model_id == "claude-3-5-sonnet-20241022"
        assert model.name == "Claude 3.5 Sonnet"
        assert model.provider == "anthropic"

        # Check pricing (from static mapping)
        assert model.pricing is not None
        assert model.pricing.prompt == 0.000003
        assert model.pricing.completion == 0.000015
        assert model.pricing.currency == "USD"

    def test_parse_model_with_capabilities(self):
        """Test parsing model with capabilities."""
        provider = AnthropicProvider(api_key="test-key")

        model_data = {
            "id": "claude-3-5-sonnet-20241022",
            "display_name": "Claude 3.5 Sonnet",
            "type": "model",
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.capabilities.supports_vision is True
        assert model.capabilities.supports_function_calling is True
        assert model.capabilities.supports_streaming is True
        assert "text" in model.capabilities.modalities
        assert "image" in model.capabilities.modalities
        assert model.context_length == 200000

    def test_parse_model_without_pricing(self):
        """Test parsing model without pricing in static map."""
        provider = AnthropicProvider(api_key="test-key")

        model_data = {
            "id": "unknown-model",
            "display_name": "Unknown Model",
            "type": "model",
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert model.model_id == "unknown-model"
        assert model.pricing is None
        assert model.context_length is None

    def test_parse_model_with_metadata(self):
        """Test parsing model with metadata."""
        provider = AnthropicProvider(api_key="test-key")

        model_data = {
            "id": "claude-3-5-sonnet-20241022",
            "display_name": "Claude 3.5 Sonnet",
            "type": "model",
            "created_at": "2024-10-22T00:00:00Z",
        }

        model = provider._parse_model(model_data)

        assert model is not None
        assert "type" in model.metadata
        assert model.metadata["type"] == "model"
        assert "created_at" in model.metadata
        assert model.metadata["created_at"] == "2024-10-22T00:00:00Z"

    def test_parse_model_invalid_data(self):
        """Test parsing model with invalid data."""
        provider = AnthropicProvider(api_key="test-key")

        # Model without ID
        model = provider._parse_model({})
        assert model is None

        # Model with empty ID
        model = provider._parse_model({"id": ""})
        assert model is None

    def test_pricing_map_completeness(self):
        """Test that all models in pricing map have expected fields."""
        for model_id, pricing in AnthropicProvider.PRICING_MAP.items():
            assert "prompt" in pricing
            assert "completion" in pricing
            assert pricing["prompt"] > 0
            assert pricing["completion"] > 0

    def test_capabilities_map_completeness(self):
        """Test that all models in capabilities map have expected fields."""
        for model_id, caps in AnthropicProvider.CAPABILITIES_MAP.items():
            assert "vision" in caps
            assert "function_calling" in caps
            assert "streaming" in caps
            assert "context_length" in caps
            assert "modalities" in caps
            assert isinstance(caps["modalities"], list)
            assert len(caps["modalities"]) > 0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        provider = AnthropicProvider(api_key="test-key")

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
        provider = AnthropicProvider(api_key="test-key")

        # Access client to create it
        _ = provider.client
        assert provider._client is not None

        # Close should clear the client
        await provider.close()
        assert provider._client is None
