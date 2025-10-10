"""Command-line interface for the model fetcher."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from .config import Config
from .storage import Storage
from .providers.openrouter import OpenRouterProvider


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Model Fetcher - Fetch available models from AI providers."""
    pass


@cli.command()
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["openrouter", "all"], case_sensitive=False),
    default="openrouter",
    help="Provider to fetch from",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Custom output directory",
)
@click.option(
    "--merge/--no-merge",
    default=True,
    help="Merge with existing data or overwrite",
)
def fetch(provider: str, output: Optional[Path], merge: bool):
    """Fetch models from a provider."""
    asyncio.run(fetch_async(provider, output, merge))


async def fetch_async(provider: str, output: Optional[Path], merge: bool):
    """Async implementation of fetch command."""
    config = Config()
    data_dir = output or config.get_data_dir()
    storage = Storage(data_dir=data_dir)

    click.echo(f"Fetching models from {provider}...")

    try:
        providers_to_fetch = []

        if provider == "openrouter" or provider == "all":
            api_key = config.get_api_key("openrouter")
            providers_to_fetch.append(
                OpenRouterProvider(api_key=api_key, timeout=config.get_timeout())
            )

        # Fetch from all specified providers
        all_models = []
        for prov in providers_to_fetch:
            async with prov:
                click.echo(f"\n→ Fetching from {prov.name}...")
                models = await prov.fetch_models()
                all_models.extend(models)
                click.echo(f"  Found {len(models)} models from {prov.name}")

        if not all_models:
            click.echo("No models fetched.", err=True)
            sys.exit(1)

        # Save or merge the data
        if merge:
            catalog = storage.merge_models(all_models)
            click.echo(f"\n✓ Merged {len(all_models)} models into catalog")
        else:
            from .models import ModelCatalog

            catalog = ModelCatalog()
            for model in all_models:
                catalog.add_model(model)
            click.echo(f"\n✓ Created new catalog with {len(all_models)} models")

        storage.save_catalog(catalog)

        # Show summary
        click.echo("\nSummary:")
        click.echo(f"  Total models: {len(catalog.models)}")
        click.echo(f"  Providers: {len(catalog.providers)}")
        for prov_name, prov_info in catalog.providers.items():
            click.echo(f"    - {prov_name}: {prov_info.model_count} models")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if config.is_debug_enabled():
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    "-p",
    help="Filter by provider name",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    help="Custom data directory",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of models to display",
)
def list(provider: Optional[str], data_dir: Optional[Path], limit: Optional[int]):
    """List fetched models."""
    config = Config()
    storage = Storage(data_dir=data_dir or config.get_data_dir())

    try:
        catalog = storage.load_catalog()

        if not catalog.models:
            click.echo("No models in catalog. Run 'fetcher fetch' first.")
            return

        # Filter by provider if specified
        models = catalog.models
        if provider:
            models = [m for m in models if m.provider.lower() == provider.lower()]

        if not models:
            click.echo(f"No models found for provider '{provider}'")
            return

        # Apply limit
        if limit:
            models = models[:limit]

        click.echo(f"\nFound {len(models)} models:\n")
        for model in models:
            context = f"{model.context_length}k" if model.context_length else "N/A"
            pricing = ""
            if model.pricing and model.pricing.prompt:
                pricing = f" (${model.pricing.prompt:.6f}/tok)"

            click.echo(f"  {model.model_id}")
            click.echo(f"    Provider: {model.provider}")
            click.echo(f"    Name: {model.name}")
            click.echo(f"    Context: {context}{pricing}")
            if model.capabilities.modalities:
                click.echo(f"    Modalities: {', '.join(model.capabilities.modalities)}")
            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "yaml"], case_sensitive=False),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    help="Custom data directory",
)
def export(format: str, output: Optional[Path], data_dir: Optional[Path]):
    """Export catalog to different formats."""
    config = Config()
    storage = Storage(data_dir=data_dir or config.get_data_dir())

    try:
        if format == "csv":
            path = storage.export_to_csv(output)
        elif format == "yaml":
            path = storage.export_to_yaml(output)
        else:
            # JSON is the default storage format
            catalog = storage.load_catalog()
            click.echo(f"Catalog already available at: {storage.catalog_path}")
            return

        click.echo(f"Exported to: {path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
