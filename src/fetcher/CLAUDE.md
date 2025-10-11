# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this package (./src/fetcher/providers).

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

### GoogleProvider

The Google provider fetches models from the Google Gemini API. Key characteristics:

- **Authentication**: Requires API key (set via `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable or passed programmatically)
- **Headers**: Uses custom `x-goog-api-key` header instead of Bearer auth
- **Pagination**: Supports full pagination using `pageToken` and `pageSize` parameters
- **API Endpoint**: `GET /v1beta/models` returns model information including context limits and capabilities
- **Static Mappings**: Pricing and detailed capabilities are maintained via static mappings, as the Google API doesn't provide pricing information
- **Model Coverage**: Includes Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash, Gemini 1.5 Pro/Flash, and Gemini 1.0 Pro models
- **Multimodal Support**: Modern Gemini models support text, image, video, and audio inputs
- **Model ID Normalization**: API returns model IDs in format `models/gemini-xxx`, which are normalized by stripping the `models/` prefix

**CLI Usage:**
```bash
# Set API key (either variable works)
export GOOGLE_API_KEY="AIza..."
# or
export GEMINI_API_KEY="AIza..."

# Fetch Google models
fetcher fetch --provider google

# Fetch from all providers
fetcher fetch --provider all

# List Google models
fetcher list --provider google

# Search for specific Google models
fetcher search --provider google --supports-vision --min-context 1000000
```

**Programmatic Usage:**
```python
from pathlib import Path
from fetcher import Fetcher

# Initialize with Google API key
fetcher = Fetcher(
    api_keys={"google": "AIza..."},
    timeout=60.0,
    data_dir=Path("data")
)

# Fetch Google models
catalog, summary = await fetcher.fetch(provider="google", merge=True)

# Search for Gemini 2.5 models with multimodal support
models = fetcher.search(
    provider="google",
    query="gemini-2.5",
    supports_vision=True
)

# Search for models with large context windows
models = fetcher.search(
    provider="google",
    min_context=1000000,  # 1M+ tokens
    modalities=["text", "image", "video"]
)

# Search for cost-effective models
models = fetcher.search(
    provider="google",
    max_prompt_price=0.10,  # Per 1M tokens
    supports_function_calling=True
)
```
