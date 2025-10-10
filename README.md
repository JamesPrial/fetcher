# Model Fetcher

A Python tool for fetching available AI models from various providers and storing them in structured format.

## Features

- Fetch model catalogs from multiple AI providers
- **OpenRouter support** - access to the largest catalog of models
- Store models in structured JSON format
- Export to CSV and YAML formats
- Merge capabilities for incremental updates
- Command-line interface for easy usage

## Installation

```bash
# Clone the repository
cd fetcher

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Usage

### Fetch Models

Fetch models from OpenRouter (default provider):

```bash
fetcher fetch
```

Fetch from a specific provider:

```bash
fetcher fetch --provider openrouter
```

### List Models

List all fetched models:

```bash
fetcher list
```

Filter by provider:

```bash
fetcher list --provider openrouter
```

Limit the number of results:

```bash
fetcher list --limit 10
```

### Export Data

Export to different formats:

```bash
# Export to CSV
fetcher export --format csv

# Export to YAML
fetcher export --format yaml

# Specify custom output path
fetcher export --format csv --output /path/to/models.csv
```

## Configuration

Create a `.env` file in the project root to configure API keys and settings:

```bash
cp .env.example .env
```

Available configuration options:

- `OPENROUTER_API_KEY` - OpenRouter API key (optional for listing models)
- `FETCHER_DATA_DIR` - Data directory path (default: `data`)
- `FETCHER_TIMEOUT` - HTTP request timeout in seconds (default: `30.0`)
- `FETCHER_DEBUG` - Enable debug mode (default: `false`)

## Project Structure

```
fetcher/
├── src/fetcher/
│   ├── __init__.py
│   ├── models.py          # Pydantic data models
│   ├── config.py          # Configuration management
│   ├── storage.py         # Data persistence
│   ├── cli.py             # Command-line interface
│   └── providers/         # Provider implementations
│       ├── __init__.py
│       ├── base.py        # Abstract base class
│       └── openrouter.py  # OpenRouter provider
├── data/                  # Output directory
│   └── models.json
├── tests/
├── pyproject.toml
└── README.md
```

## Data Model

Each model in the catalog includes:

- **model_id** - Unique identifier
- **name** - Human-readable name
- **provider** - Provider name (e.g., openrouter)
- **description** - Model description
- **context_length** - Maximum context window size
- **pricing** - Cost per token (prompt, completion, image)
- **capabilities** - Supported features (vision, function calling, streaming)
- **modalities** - Supported input types (text, image, etc.)
- **metadata** - Provider-specific additional information
- **updated_at** - Last update timestamp

## Development

Run tests:

```bash
pytest
```

Format code:

```bash
black src/
```

Lint code:

```bash
ruff check src/
```

## Adding New Providers

To add a new provider:

1. Create a new file in `src/fetcher/providers/`
2. Subclass `BaseProvider`
3. Implement `fetch_models()` method
4. Add provider to CLI in `cli.py`

Example:

```python
from .base import BaseProvider
from ..models import ModelInfo

class MyProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "myprovider"

    async def fetch_models(self) -> List[ModelInfo]:
        # Implementation here
        pass
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
