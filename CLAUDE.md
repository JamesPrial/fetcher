# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context7 MCP Integration

ALWAYS use the context7 MCP for Inspect AI, library id = /websites/inspect_aisi_uk.

## Version Control

ALWAYS use agent-git-ops to checkout a new branch before beginning implementing anything, and when you finish, use agent-gh-cli to commit and merge with dev-> open pull request to main and switch back to main.

## Context Management and Parallelization

Use your Task tool to parallelize and reduce context bloat where ever appropriate.

## Project Overview

This package fetches available AI models from various providers (OpenRouter, Anthropic, OpenAI, Google) and stores them in structured JSON format. It provides both a CLI and programmatic API for model catalog management.

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

**Provider System** (`src/fetcher/providers/`): Abstract `BaseProvider` class with async context manager support and lazy HTTP client initialization. Providers implement `fetch_models()` to return `List[ModelInfo]`. Currently implements `OpenRouterProvider`, `AnthropicProvider`, `OpenAIProvider`, and `GoogleProvider`.

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
5. See `src/fetcher/providers/CLAUDE.md` if you need more info

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

### Pricing Format

**All providers use per-token pricing** stored in scientific notation (e.g., `3e-06` for $3.00 per 1M tokens):
- OpenRouter: Natively provides per-token pricing from API
- Anthropic: Static pricing map uses per-token format (e.g., `0.000003` = $3.00 per 1M tokens)
- OpenAI: Static pricing map uses per-token format (e.g., `0.0000025` = $2.50 per 1M tokens)
- Google: Static pricing map uses per-token format (e.g., `0.000000075` = $0.075 per 1M tokens)

**Display Conversion**: The HTML viewer multiplies all prices by 1,000,000 to display user-friendly "per 1M tokens" values.

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
