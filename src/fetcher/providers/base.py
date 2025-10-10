"""Base provider class for fetching models."""

from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

from ..models import ModelInfo


class BaseProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the provider.

        Args:
            api_key: Optional API key for authentication
            base_url: Optional base URL for the API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    @abstractmethod
    async def fetch_models(self) -> List[ModelInfo]:
        """
        Fetch all available models from the provider.

        Returns:
            List of ModelInfo objects

        Raises:
            httpx.HTTPError: If the API request fails
        """
        pass

    def validate_credentials(self) -> bool:
        """
        Validate that the provider has the necessary credentials.

        Returns:
            True if credentials are valid (or not required), False otherwise
        """
        # Default implementation - override if credentials are required
        return True
