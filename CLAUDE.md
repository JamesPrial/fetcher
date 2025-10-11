# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context7 MCP Integration

ALWAYS use the context7 MCP for Inspect AI, library id = /websites/inspect_aisi_uk

## Version Control

ALWAYS checkout a new branch before beginning implementing anything, and when you finish, commit -> open pull request

## Project Overview

This package fetches available AI models from various providers (OpenRouter, Anthropic, OpenAI) and stores them in structured JSON format. It provides both a CLI and programmatic API for model catalog management.

## Development Commands

**Install dependencies:**
```bash
pip install -e ".[dev]"
```

**Run tests:**
```bash
pytest
```

**Format code:**
```bash
black src/
```

**Lint code:**
```bash
ruff check src/
```

**Run a single test:**
```bash
pytest tests/test_file.py::test_function_name
```

## Architecture

### Core Components

**Fetcher** (`src/fetcher/fetcher.py`): Main programmatic API that coordinates between providers and storage. Accepts all configuration as constructor arguments (api_keys, base_urls, timeout, debug, data_dir). Returns `(ModelCatalog, summary_dict)` tuples from fetch operations.

**Provider System** (`src/fetcher/providers/`): Abstract `BaseProvider` class with async context manager support and lazy HTTP client initialization. Providers implement `fetch_models()` to return `List[ModelInfo]`. Currently implements `OpenRouterProvider`, `AnthropicProvider`, and `OpenAIProvider`.

**Storage** (`src/fetcher/storage.py`): Handles persistence to JSON (primary format), CSV, and YAML. Implements merge logic that updates existing models by `model_id` or adds new ones. Default storage location: `data/models.json`.

**Models** (`src/fetcher/models.py`): Pydantic models with datetime handling. Key hierarchy: `ModelCatalog` contains `List[ModelInfo]` and `Dict[str, ProviderInfo]`. All models have timezone-aware datetime fields with custom JSON encoders.

**CLI** (`src/fetcher/cli.py`): Click-based CLI with three commands: `fetch`, `list`, `export`. Handles all environment variable parsing and passes values as arguments to `Fetcher`. Entry point defined in pyproject.toml as `fetcher` command.

### Key Design Patterns

1. **Async Context Managers**: Providers use `async with` to ensure HTTP clients are properly closed
2. **Merge Logic**: Storage merges by `model_id` - updates existing entries or adds new ones
3. **Provider Registry**: Adding new providers requires updating both `fetcher.py` and `cli.py`
4. **Default Factories**: Pydantic models use lambda factories for mutable defaults and timezone-aware datetimes

## Adding New Providers

1. Create `src/fetcher/providers/your_provider.py` subclassing `BaseProvider`
2. Implement `name` property and `fetch_models()` async method
3. Add provider initialization in `Fetcher.fetch()` in `src/fetcher/fetcher.py`
4. Optionally add CLI support in `src/fetcher/cli.py`

Provider implementations should:
- Use `self.client` property for HTTP requests (lazy-initialized httpx.AsyncClient)
- Return `List[ModelInfo]` with all required fields populated
- Set `provider` field to match the `name` property
- Handle API pagination if needed
- Use timezone-aware datetimes for `updated_at` fields

## Data Model Notes

- `ModelInfo.model_id` is the unique identifier used for merge operations
- `ModelCapabilities` and `PricingInfo` have default factories returning zero/false values
- All datetime fields use `datetime.now(timezone.utc)` for consistency
- `ModelCatalog.add_model()` automatically updates provider statistics and timestamps
- Pricing includes optional `currency` field (defaults to "USD")

## Configuration

The CLI reads environment variables and passes them as arguments to the `Fetcher` class. Environment variables follow these patterns:

- `{PROVIDER}_API_KEY` - API keys for authentication (e.g., `OPENROUTER_API_KEY`)
- `{PROVIDER}_BASE_URL` - Custom base URLs (e.g., `OPENROUTER_BASE_URL`)
- `FETCHER_DATA_DIR` - Data directory path (default: "data")
- `FETCHER_TIMEOUT` - HTTP timeout in seconds (default: 30.0)
- `FETCHER_DEBUG` - Enable debug mode (default: false)

For programmatic use, pass configuration directly to `Fetcher()`:

```python
fetcher = Fetcher(
    api_keys={"openrouter": "sk-..."},
    base_urls={"openrouter": "https://custom.url"},
    timeout=60.0,
    debug=True,
    data_dir=Path("custom/data")
)
```

## Provider-Specific Notes

### AnthropicProvider

The Anthropic provider fetches models from the Anthropic API. Key characteristics:

- **Authentication**: Requires API key (set via `ANTHROPIC_API_KEY` environment variable or passed programmatically)
- **Headers**: Uses custom `x-api-key` header instead of Bearer auth, plus `anthropic-version` header
- **Pagination**: Supports full pagination using `after_id` and `limit` parameters
- **Static Mappings**: Pricing and detailed capabilities are maintained via static mappings, as the Anthropic API returns minimal model info

**CLI Usage:**
```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Fetch Anthropic models
fetcher fetch --provider anthropic

# Fetch from all providers
fetcher fetch --provider all

# List Anthropic models
fetcher list --provider anthropic
```

**Programmatic Usage:**
```python
from pathlib import Path
from fetcher import Fetcher

# Initialize with Anthropic API key
fetcher = Fetcher(
    api_keys={"anthropic": "sk-ant-..."},
    timeout=60.0,
    data_dir=Path("data")
)

# Fetch Anthropic models
catalog, summary = await fetcher.fetch(provider="anthropic", merge=True)

# Search for specific Anthropic models
models = fetcher.search(
    provider="anthropic",
    supports_vision=True,
    min_context=100000
)
```

### OpenAIProvider

The OpenAI provider fetches models from the OpenAI API. Key characteristics:

- **Authentication**: Optional API key (set via `OPENAI_API_KEY` environment variable or passed programmatically)
- **Headers**: Uses standard Bearer authentication
- **API Endpoint**: `GET /v1/models` returns minimal model information
- **Static Mappings**: Pricing and detailed capabilities are maintained via static mappings, as the OpenAI API only returns id, created, owned_by
- **Model Coverage**: Includes GPT-4o, GPT-4 Turbo, GPT-4, GPT-3.5 Turbo, o1 reasoning models, and embedding models
- **Fine-tuned Models**: Automatically detects and includes fine-tuned models (starting with "ft:")

**CLI Usage:**
```bash
# Set API key (optional but recommended)
export OPENAI_API_KEY="sk-..."

# Fetch OpenAI models
fetcher fetch --provider openai

# Fetch from all providers
fetcher fetch --provider all

# List OpenAI models
fetcher list --provider openai

# Search for specific OpenAI models
fetcher search --provider openai --supports-vision --min-context 100000
```

**Programmatic Usage:**
```python
from pathlib import Path
from fetcher import Fetcher

# Initialize with OpenAI API key
fetcher = Fetcher(
    api_keys={"openai": "sk-..."},
    timeout=60.0,
    data_dir=Path("data")
)

# Fetch OpenAI models
catalog, summary = await fetcher.fetch(provider="openai", merge=True)

# Search for GPT-4o models with vision
models = fetcher.search(
    provider="openai",
    query="gpt-4o",
    supports_vision=True
)

# Search for cost-effective models
models = fetcher.search(
    provider="openai",
    max_prompt_price=1.0,  # Per 1M tokens
    supports_function_calling=True
)
```
