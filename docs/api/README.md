# AI Model Catalog API

RESTful API for querying AI model information from multiple providers (OpenRouter, Anthropic, OpenAI, Google).

**Base URL:** `https://jamesprial.github.io/fetcher/api`

## Table of Contents

- [Quick Start](#quick-start)
- [Endpoints](#endpoints)
  - [Dynamic Query API](#dynamic-query-api)
  - [Static Endpoints](#static-endpoints)
- [Query Parameters](#query-parameters)
- [Response Format](#response-format)
- [Examples](#examples)
- [Rate Limits](#rate-limits)

## Quick Start

### Get All Models
```bash
curl https://jamesprial.github.io/fetcher/models.json
```

### Get OpenAI Models
```bash
curl https://jamesprial.github.io/fetcher/api/?provider=openai
```

### Search for GPT-4 Models
```bash
curl "https://jamesprial.github.io/fetcher/api/?search=gpt-4"
```

### Get Models with Vision Support
```bash
curl https://jamesprial.github.io/fetcher/api/?supports_vision=true
```

## Endpoints

### Dynamic Query API

**Endpoint:** `/api/`
**Method:** `GET`
**Description:** Query models with advanced filtering, sorting, and pagination

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `provider` | string | Filter by provider (comma-separated) | `openai`, `anthropic,google` |
| `capability` | string | Filter by capability (comma-separated) | `vision`, `function-calling,streaming` |
| `search` | string | Search in model name, ID, or description | `gpt-4`, `claude` |
| `min_context` | integer | Minimum context length | `100000` |
| `max_context` | integer | Maximum context length | `200000` |
| `min_prompt_price` | float | Minimum prompt price per token | `0.000001` |
| `max_prompt_price` | float | Maximum prompt price per token | `0.00001` |
| `min_completion_price` | float | Minimum completion price per token | `0.000001` |
| `max_completion_price` | float | Maximum completion price per token | `0.00001` |
| `supports_vision` | boolean | Filter by vision support | `true`, `false` |
| `supports_function_calling` | boolean | Filter by function calling support | `true`, `false` |
| `supports_streaming` | boolean | Filter by streaming support | `true`, `false` |
| `sort` | string | Sort field | `name`, `provider`, `context`, `prompt-price`, `completion-price`, `updated` |
| `order` | string | Sort order | `asc`, `desc` |
| `limit` | integer | Number of results to return | `10`, `50` |
| `offset` | integer | Number of results to skip (pagination) | `0`, `10`, `20` |
| `format` | string | Output format | `json` (default), `csv` |

#### Response Format

```json
{
  "api_version": "1.0.0",
  "total_count": 479,
  "count": 10,
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
        "modalities": ["text", "image", "text->text"]
      },
      "metadata": {},
      "updated_at": "2025-10-11T16:13:40+00:00"
    }
  ]
}
```

### Static Endpoints

Pre-generated JSON files for common queries (updated automatically).

#### All Models
**Endpoint:** `/models.json`
**Description:** Complete model catalog with all providers

```bash
curl https://jamesprial.github.io/fetcher/models.json
```

#### By Provider

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

#### By Capability

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

#### Statistics

**Endpoint:** `/api/stats.json`
**Description:** Summary statistics for all models and providers

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

#### API Metadata

**Endpoint:** `/api/api.json`
**Description:** API documentation and metadata

```bash
curl https://jamesprial.github.io/fetcher/api/api.json
```

## Examples

### Filter by Multiple Providers

Get all models from OpenAI and Anthropic:
```bash
curl "https://jamesprial.github.io/fetcher/api/?provider=openai,anthropic"
```

### Advanced Filtering

Get models with 100k+ context, vision support, sorted by price:
```bash
curl "https://jamesprial.github.io/fetcher/api/?min_context=100000&supports_vision=true&sort=prompt-price&order=asc"
```

### Search and Filter

Search for GPT models with function calling:
```bash
curl "https://jamesprial.github.io/fetcher/api/?search=gpt&supports_function_calling=true"
```

### Price Filtering

Get cheapest models (prompt price):
```bash
curl "https://jamesprial.github.io/fetcher/api/?max_prompt_price=0.000001&sort=prompt-price&order=asc&limit=10"
```

### Pagination

Get results with pagination:
```bash
# First page (10 results)
curl "https://jamesprial.github.io/fetcher/api/?limit=10&offset=0"

# Second page (10 results)
curl "https://jamesprial.github.io/fetcher/api/?limit=10&offset=10"

# Third page (10 results)
curl "https://jamesprial.github.io/fetcher/api/?limit=10&offset=20"
```

### Export as CSV

Get results in CSV format:
```bash
curl "https://jamesprial.github.io/fetcher/api/?provider=openai&format=csv"
```

### JavaScript/Fetch Example

```javascript
// Fetch all OpenAI models with vision support
fetch('https://jamesprial.github.io/fetcher/api/?provider=openai&supports_vision=true')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total_count} models`);
    data.models.forEach(model => {
      console.log(`${model.name}: $${model.pricing.prompt * 1000000}/1M tokens`);
    });
  });
```

### Python Example

```python
import requests

# Get all models with function calling support
response = requests.get(
    'https://jamesprial.github.io/fetcher/api/',
    params={
        'supports_function_calling': 'true',
        'sort': 'prompt-price',
        'order': 'asc',
        'limit': 20
    }
)

data = response.json()
print(f"Found {data['total_count']} models")

for model in data['models']:
    print(f"{model['name']} ({model['provider']})")
    print(f"  Context: {model['context_length']:,} tokens")
    print(f"  Price: ${model['pricing']['prompt'] * 1000000:.4f}/1M tokens")
```

### cURL with Complex Filters

```bash
# Get cost-effective models with large context windows
curl -G "https://jamesprial.github.io/fetcher/api/" \
  --data-urlencode "min_context=100000" \
  --data-urlencode "max_prompt_price=0.000003" \
  --data-urlencode "supports_function_calling=true" \
  --data-urlencode "sort=context" \
  --data-urlencode "order=desc" \
  --data-urlencode "limit=15"
```

## Rate Limits

GitHub Pages has no explicit rate limits, but please be considerate:
- **Recommended:** Cache responses when possible
- **Update frequency:** Data is updated daily at midnight UTC
- **Static endpoints:** Use pre-generated files for common queries (faster)

## Data Freshness

- Models are fetched daily via GitHub Actions
- Last update timestamp available in response: `last_updated` field
- Check `/api/stats.json` for latest update time

## CORS Support

All endpoints support CORS and can be accessed from any origin.

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
