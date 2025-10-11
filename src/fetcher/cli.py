"""Command-line interface for the model fetcher."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict

import click

from .fetcher import Fetcher


def get_api_keys() -> Dict[str, str]:
    """Get API keys from environment variables."""
    api_keys = {}
    # Check for common provider API keys
    for provider in ["openrouter", "openai", "anthropic"]:
        env_var = f"{provider.upper()}_API_KEY"
        key = os.getenv(env_var)
        if key:
            api_keys[provider] = key
    return api_keys


def get_base_urls() -> Dict[str, str]:
    """Get base URLs from environment variables."""
    base_urls = {}
    for provider in ["openrouter", "openai", "anthropic"]:
        env_var = f"{provider.upper()}_BASE_URL"
        url = os.getenv(env_var)
        if url:
            base_urls[provider] = url
    return base_urls


def get_data_dir() -> Path:
    """Get data directory from environment."""
    data_dir = os.getenv("FETCHER_DATA_DIR", "data")
    return Path(data_dir)


def get_timeout() -> float:
    """Get HTTP timeout from environment."""
    timeout = os.getenv("FETCHER_TIMEOUT", "30.0")
    try:
        return float(timeout)
    except ValueError:
        return 30.0


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("FETCHER_DEBUG", "false").lower() in ("true", "1", "yes")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Model Fetcher - Fetch available models from AI providers."""
    pass


@cli.command()
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["openrouter", "anthropic", "openai", "all"], case_sensitive=False),
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
    # Read configuration from environment
    data_dir = output or get_data_dir()
    api_keys = get_api_keys()
    base_urls = get_base_urls()
    timeout = get_timeout()
    debug = is_debug_enabled()

    fetcher = Fetcher(
        data_dir=data_dir,
        api_keys=api_keys,
        base_urls=base_urls,
        timeout=timeout,
        debug=debug,
    )

    click.echo(f"Fetching models from {provider}...")

    try:
        _, summary = await fetcher.fetch(provider=provider, merge=merge)

        # Show success message
        if merge:
            click.echo(f"\n✓ Merged {summary['fetched_count']} models into catalog")
        else:
            click.echo(f"\n✓ Created new catalog with {summary['fetched_count']} models")

        # Show summary
        click.echo("\nSummary:")
        click.echo(f"  Total models: {summary['total_models']}")
        click.echo(f"  Providers: {len(summary['providers'])}")
        for prov_name, model_count in summary['providers'].items():
            click.echo(f"    - {prov_name}: {model_count} models")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if debug:
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
    # Read configuration from environment
    dir_path = data_dir or get_data_dir()

    fetcher = Fetcher(data_dir=dir_path)

    try:
        models = fetcher.list(provider=provider, limit=limit)

        if not models:
            if provider:
                click.echo(f"No models found for provider '{provider}'")
            else:
                click.echo("No models in catalog. Run 'fetcher fetch' first.")
            return

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
@click.argument("query", required=False)
@click.option(
    "--provider",
    "-p",
    help="Filter by provider name",
)
@click.option(
    "--min-context",
    type=int,
    help="Minimum context length",
)
@click.option(
    "--max-context",
    type=int,
    help="Maximum context length",
)
@click.option(
    "--max-prompt-price",
    type=float,
    help="Maximum prompt token price",
)
@click.option(
    "--max-completion-price",
    type=float,
    help="Maximum completion token price",
)
@click.option(
    "--supports-vision",
    is_flag=True,
    help="Filter models with vision support",
)
@click.option(
    "--supports-function-calling",
    is_flag=True,
    help="Filter models with function calling support",
)
@click.option(
    "--supports-streaming",
    is_flag=True,
    help="Filter models with streaming support",
)
@click.option(
    "--modality",
    "-m",
    multiple=True,
    help="Filter by modality (can be specified multiple times)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of models to display",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    help="Custom data directory",
)
def search(
    query: Optional[str],
    provider: Optional[str],
    min_context: Optional[int],
    max_context: Optional[int],
    max_prompt_price: Optional[float],
    max_completion_price: Optional[float],
    supports_vision: bool,
    supports_function_calling: bool,
    supports_streaming: bool,
    modality: tuple,
    limit: Optional[int],
    data_dir: Optional[Path],
):
    """Search for models using various filters."""
    # Read configuration from environment
    dir_path = data_dir or get_data_dir()

    fetcher = Fetcher(data_dir=dir_path)

    try:
        # Convert tuple to list for modalities
        modalities = list(modality) if modality else None

        # Convert flags to Optional[bool] (None if not set, True if set)
        vision_filter = True if supports_vision else None
        function_calling_filter = True if supports_function_calling else None
        streaming_filter = True if supports_streaming else None

        models = fetcher.search(
            query=query,
            provider=provider,
            min_context=min_context,
            max_context=max_context,
            max_prompt_price=max_prompt_price,
            max_completion_price=max_completion_price,
            supports_vision=vision_filter,
            supports_function_calling=function_calling_filter,
            supports_streaming=streaming_filter,
            modalities=modalities,
            limit=limit,
        )

        if not models:
            click.echo("No models found matching the search criteria.")
            return

        click.echo(f"\nFound {len(models)} model(s):\n")
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

            # Show capabilities if any are enabled
            caps = []
            if model.capabilities.supports_vision:
                caps.append("vision")
            if model.capabilities.supports_function_calling:
                caps.append("function_calling")
            if model.capabilities.supports_streaming:
                caps.append("streaming")
            if caps:
                click.echo(f"    Capabilities: {', '.join(caps)}")
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
    # Read configuration from environment
    dir_path = data_dir or get_data_dir()

    fetcher = Fetcher(data_dir=dir_path)

    try:
        path = fetcher.export(format=format, output_path=output)

        if format == "json":
            click.echo(f"Catalog already available at: {path}")
        else:
            click.echo(f"Exported to: {path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
