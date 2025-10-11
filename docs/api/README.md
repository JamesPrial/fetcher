# AI Model Catalog API

Static JSON API for querying AI model information from multiple providers (OpenRouter, Anthropic, OpenAI, Google).

**Base URL:** `https://jamesprial.github.io/fetcher`

## Table of Contents

- [Quick Start](#quick-start)
- [Endpoints](#endpoints)
  - [All Models](#all-models)
  - [By Provider](#by-provider)
  - [By Capability](#by-capability)
  - [Statistics](#statistics)
  - [API Metadata](#api-metadata)
- [Response Format](#response-format)
- [Examples](#examples)
- [Data Freshness](#data-freshness)

## Quick Start

### Get All Models

```bash
curl https://jamesprial.github.io/fetcher/models.json
```

### Get OpenAI Models

```bash
curl https://jamesprial.github.io/fetcher/api/providers/openai.json
```

### Get Models with Vision Support

```bash
curl https://jamesprial.github.io/fetcher/api/capabilities/vision.json
```

### Get API Statistics

```bash
curl https://jamesprial.github.io/fetcher/api/stats.json
```

## Endpoints

All endpoints return pre-generated JSON files that are updated automatically via GitHub Actions.

### All Models

**Endpoint:** `/models.json`

Complete model catalog with all providers (479 models total).

```bash
curl https://jamesprial.github.io/fetcher/models.json
```

### By Provider

**Endpoint:** `/api/providers/{provider}.json`

**Available Providers:** `openrouter`, `anthropic`, `openai`, `google`

```bash
# Get all OpenAI models
curl https://jamesprial.github.io/fetcher/api/providers/openai.json

# Get all Anthropic models
curl https://jamesprial.github.io/fetcher/api/providers/anthropic.json

# Get all Google models
curl https://jamesprial.github.io/fetcher/api/providers/google.json

# Get all OpenRouter models
curl https://jamesprial.github.io/fetcher/api/providers/openrouter.json
```

**List all providers:**

```bash
curl https://jamesprial.github.io/fetcher/api/providers/index.json
```

### By Capability

**Endpoint:** `/api/capabilities/{capability}.json`

**Available Capabilities:** `vision`, `function-calling`, `streaming`

```bash
# Get all models with vision support
curl https://jamesprial.github.io/fetcher/api/capabilities/vision.json

# Get all models with function calling
curl https://jamesprial.github.io/fetcher/api/capabilities/function-calling.json

# Get all models with streaming support
curl https://jamesprial.github.io/fetcher/api/capabilities/streaming.json
```

**List all capabilities:**

```bash
curl https://jamesprial.github.io/fetcher/api/capabilities/index.json
```

### Statistics

**Endpoint:** `/api/stats.json`

Summary statistics for all models and providers including counts, averages, and per-provider breakdowns.

```bash
curl https://jamesprial.github.io/fetcher/api/stats.json
```

**Response:**
```json
{
  "api_version": "1.0.0",
  "overall": {
    "total_models": 479,
    "total_providers": 4,
    "models_with_vision": 87,
    "models_with_function_calling": 245,
    "models_with_streaming": 456,
    "avg_context_length": 98234.5,
    "avg_prompt_price": 0.000002145,
    "avg_prompt_price_per_1m_tokens": 2.145
  },
  "by_provider": {
    "openai": {
      "model_count": 42,
      "models_with_vision": 8,
      "models_with_function_calling": 38,
      "avg_context_length": 128000,
      "avg_prompt_price": 0.0000015
    }
  }
}
```

### API Metadata

**Endpoint:** `/api/api.json`

API documentation and available endpoint information.

```bash
curl https://jamesprial.github.io/fetcher/api/api.json
```

## Response Format

All endpoints return JSON with a consistent structure:

```json
{
  "api_version": "1.0.0",
  "models": [
    {
      "model_id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "openai",
      "description": "...",
      "context_length": 128000,
      "pricing": {
        "prompt": 0.0000025,
        "completion": 0.00001,
        "currency": "USD"
      },
      "capabilities": {
        "supports_vision": true,
        "supports_function_calling": true,
        "supports_streaming": true,
        "modalities": ["text", "image"]
      },
      "metadata": {},
      "updated_at": "2025-10-11T16:13:40+00:00"
    }
  ],
  "providers": {
    "openai": {
      "model_count": 73,
      "updated_at": "2025-10-11T16:13:40+00:00"
    }
  }
}
```

## Examples

### JavaScript/Fetch Example

```javascript
// Fetch all models with vision support
fetch('https://jamesprial.github.io/fetcher/api/capabilities/vision.json')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.models.length} models with vision support`);
    data.models.slice(0, 10).forEach(model => {
      console.log(`${model.name}: $${model.pricing.prompt * 1000000}/1M tokens`);
    });
  });
```

### Python Example

```python
import requests

# Get all OpenAI models
response = requests.get('https://jamesprial.github.io/fetcher/api/providers/openai.json')
data = response.json()

print(f"OpenAI has {len(data['models'])} models")

for model in data['models'][:10]:
    print(f"{model['name']}")
    print(f"  Context: {model['context_length']:,} tokens")
    print(f"  Price: ${model['pricing']['prompt'] * 1000000:.4f}/1M tokens")
```

### Combining Multiple Endpoints

```bash
# Get stats for all providers
for provider in openai anthropic google openrouter; do
  echo "=== $provider ==="
  curl -s "https://jamesprial.github.io/fetcher/api/providers/$provider.json" | \
    jq -r '.models | length | "Model count: \(.)"'
done
```

## Data Freshness

- Models are fetched daily via GitHub Actions (midnight UTC)
- Each model includes an `updated_at` timestamp
- Provider metadata includes `updated_at` for last update time
- Check `/api/stats.json` for generation timestamp

## Pricing Format

All prices are **per-token** in scientific notation:
- `0.000003` = $3.00 per 1 million tokens
- `0.0000015` = $1.50 per 1 million tokens

To convert to per-1M-tokens pricing: `price * 1000000`

## Support

- **Issues:** [GitHub Issues](https://github.com/JamesPrial/fetcher/issues)
- **Documentation:** [Main README](https://github.com/JamesPrial/fetcher)
- **Interactive Viewer:** [HTML Viewer](https://jamesprial.github.io/fetcher/)

## License

This API serves data collected from various AI providers. Please refer to individual provider terms of service for usage restrictions.
