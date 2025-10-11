"""Main Fetcher class for programmatic access to model fetching."""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .storage import Storage
from .models import ModelInfo, ModelCatalog
from .providers.openrouter import OpenRouterProvider


class Fetcher:
    """Main class for fetching and managing AI model catalogs."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        api_keys: Optional[Dict[str, str]] = None,
        base_urls: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        debug: bool = False,
    ):
        """
        Initialize the Fetcher.

        Args:
            data_dir: Data directory path. Defaults to 'data'.
            api_keys: Dict mapping provider names to API keys (e.g., {"openrouter": "key"}).
            base_urls: Dict mapping provider names to custom base URLs.
            timeout: HTTP request timeout in seconds. Defaults to 30.0.
            debug: Enable debug mode. Defaults to False.
        """
        # Store configuration values
        self._data_dir = data_dir or Path("data")
        self._api_keys = api_keys or {}
        self._base_urls = base_urls or {}
        self._timeout = timeout
        self._debug = debug

        self.storage = Storage(data_dir=self._data_dir)

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider."""
        return self._api_keys.get(provider)

    def _get_base_url(self, provider: str) -> Optional[str]:
        """Get base URL for a provider."""
        return self._base_urls.get(provider)

    async def fetch(
        self, provider: str = "openrouter", merge: bool = True
    ) -> Tuple[ModelCatalog, Dict[str, Any]]:
        """
        Fetch models from a provider.

        Args:
            provider: Provider to fetch from ("openrouter" or "all")
            merge: Whether to merge with existing data or overwrite

        Returns:
            Tuple of (ModelCatalog, summary_dict) where summary_dict contains:
                - total_models: Total number of models in catalog
                - providers: Dict of provider names to model counts
                - fetched_count: Number of models just fetched

        Raises:
            ValueError: If no models are fetched
            Exception: If fetching or saving fails
        """
        providers_to_fetch = []

        if provider == "openrouter" or provider == "all":
            api_key = self._get_api_key("openrouter")
            providers_to_fetch.append(
                OpenRouterProvider(api_key=api_key, timeout=self._timeout)
            )

        # Fetch from all specified providers
        all_models = []
        for prov in providers_to_fetch:
            async with prov:
                models = await prov.fetch_models()
                all_models.extend(models)

        if not all_models:
            raise ValueError("No models fetched")

        # Save or merge the data
        if merge:
            catalog = self.storage.merge_models(all_models)
        else:
            catalog = ModelCatalog()
            for model in all_models:
                catalog.add_model(model)

        self.storage.save_catalog(catalog)

        # Build summary
        summary = {
            "total_models": len(catalog.models),
            "providers": {
                prov_name: prov_info.model_count
                for prov_name, prov_info in catalog.providers.items()
            },
            "fetched_count": len(all_models),
        }

        return catalog, summary

    def list(
        self, provider: Optional[str] = None, limit: Optional[int] = None
    ) -> List[ModelInfo]:
        """
        List fetched models.

        Args:
            provider: Optional provider name to filter by
            limit: Optional limit on number of models to return

        Returns:
            List of ModelInfo objects (filtered and limited as specified)

        Raises:
            Exception: If catalog cannot be loaded
        """
        catalog = self.storage.load_catalog()

        # Filter by provider if specified
        models = catalog.models
        if provider:
            models = [m for m in models if m.provider.lower() == provider.lower()]

        # Apply limit
        if limit:
            models = models[:limit]

        return models

    def export(
        self, format: str = "json", output_path: Optional[Path] = None
    ) -> Path:
        """
        Export catalog to different formats.

        Args:
            format: Export format ("json", "csv", or "yaml")
            output_path: Optional custom output path

        Returns:
            Path to the exported file

        Raises:
            ValueError: If format is not supported
            Exception: If export fails
        """
        if format == "csv":
            return self.storage.export_to_csv(output_path)
        elif format == "yaml":
            return self.storage.export_to_yaml(output_path)
        elif format == "json":
            # JSON is the default storage format
            catalog = self.storage.load_catalog()
            return self.storage.catalog_path
        else:
            raise ValueError(f"Unsupported format: {format}")
