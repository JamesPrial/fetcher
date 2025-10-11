#!/usr/bin/env python3
"""
Generate static API endpoint JSON files for GitHub Pages.

This script reads the main models.json file and generates pre-filtered
JSON files for common queries (by provider, capability, etc.).
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any


def load_models(models_path: Path) -> Dict[str, Any]:
    """Load models from JSON file."""
    with open(models_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], output_path: Path) -> None:
    """Save data to JSON file with pretty formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Generated: {output_path}")


def generate_provider_endpoints(data: Dict[str, Any], api_dir: Path) -> None:
    """Generate JSON files for each provider."""
    models = data.get('models', [])
    providers = {}

    # Group models by provider
    for model in models:
        provider = model.get('provider', 'unknown')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)

    # Generate a file for each provider
    providers_dir = api_dir / 'providers'
    for provider, provider_models in providers.items():
        output_data = {
            'api_version': '1.0.0',
            'provider': provider,
            'total_count': len(provider_models),
            'models': provider_models,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        output_path = providers_dir / f'{provider}.json'
        save_json(output_data, output_path)

    # Generate providers list
    providers_list = {
        'api_version': '1.0.0',
        'providers': [
            {
                'name': provider,
                'model_count': len(provider_models),
                'endpoint': f'providers/{provider}.json'
            }
            for provider, provider_models in sorted(providers.items())
        ],
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
    save_json(providers_list, providers_dir / 'index.json')


def generate_capability_endpoints(data: Dict[str, Any], api_dir: Path) -> None:
    """Generate JSON files for each capability."""
    models = data.get('models', [])
    capabilities_dir = api_dir / 'capabilities'

    # Vision capability
    vision_models = [
        m for m in models
        if m.get('capabilities', {}).get('supports_vision', False)
    ]
    save_json({
        'api_version': '1.0.0',
        'capability': 'vision',
        'total_count': len(vision_models),
        'models': vision_models,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }, capabilities_dir / 'vision.json')

    # Function calling capability
    function_calling_models = [
        m for m in models
        if m.get('capabilities', {}).get('supports_function_calling', False)
    ]
    save_json({
        'api_version': '1.0.0',
        'capability': 'function_calling',
        'total_count': len(function_calling_models),
        'models': function_calling_models,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }, capabilities_dir / 'function-calling.json')

    # Streaming capability
    streaming_models = [
        m for m in models
        if m.get('capabilities', {}).get('supports_streaming', False)
    ]
    save_json({
        'api_version': '1.0.0',
        'capability': 'streaming',
        'total_count': len(streaming_models),
        'models': streaming_models,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }, capabilities_dir / 'streaming.json')

    # Generate capabilities list
    capabilities_list = {
        'api_version': '1.0.0',
        'capabilities': [
            {
                'name': 'vision',
                'model_count': len(vision_models),
                'endpoint': 'capabilities/vision.json'
            },
            {
                'name': 'function_calling',
                'model_count': len(function_calling_models),
                'endpoint': 'capabilities/function-calling.json'
            },
            {
                'name': 'streaming',
                'model_count': len(streaming_models),
                'endpoint': 'capabilities/streaming.json'
            }
        ],
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
    save_json(capabilities_list, capabilities_dir / 'index.json')


def generate_stats_endpoint(data: Dict[str, Any], api_dir: Path) -> None:
    """Generate summary statistics endpoint."""
    models = data.get('models', [])
    providers = data.get('providers', {})

    # Calculate provider statistics
    provider_stats = {}
    for model in models:
        provider = model.get('provider', 'unknown')
        if provider not in provider_stats:
            provider_stats[provider] = {
                'model_count': 0,
                'models_with_vision': 0,
                'models_with_function_calling': 0,
                'models_with_streaming': 0,
                'avg_context_length': 0,
                'avg_prompt_price': 0
            }

        stats = provider_stats[provider]
        stats['model_count'] += 1

        caps = model.get('capabilities', {})
        if caps.get('supports_vision'):
            stats['models_with_vision'] += 1
        if caps.get('supports_function_calling'):
            stats['models_with_function_calling'] += 1
        if caps.get('supports_streaming'):
            stats['models_with_streaming'] += 1

    # Calculate averages
    for provider, stats in provider_stats.items():
        provider_models = [m for m in models if m.get('provider') == provider]

        # Average context length
        context_lengths = [
            m.get('context_length')
            for m in provider_models
            if m.get('context_length') is not None and m.get('context_length') > 0
        ]
        stats['avg_context_length'] = sum(context_lengths) / len(context_lengths) if context_lengths else 0

        # Average prompt price
        prompt_prices = [
            m.get('pricing', {}).get('prompt')
            for m in provider_models
            if m.get('pricing') is not None
            and m.get('pricing', {}).get('prompt') is not None
            and m.get('pricing', {}).get('prompt') > 0
        ]
        stats['avg_prompt_price'] = sum(prompt_prices) / len(prompt_prices) if prompt_prices else 0

    # Overall statistics
    all_context_lengths = [
        m.get('context_length')
        for m in models
        if m.get('context_length') is not None and m.get('context_length') > 0
    ]
    all_prompt_prices = [
        m.get('pricing', {}).get('prompt')
        for m in models
        if m.get('pricing') is not None
        and m.get('pricing', {}).get('prompt') is not None
        and m.get('pricing', {}).get('prompt') > 0
    ]

    stats_data = {
        'api_version': '1.0.0',
        'overall': {
            'total_models': len(models),
            'total_providers': len(provider_stats),
            'models_with_vision': sum(1 for m in models if m.get('capabilities', {}).get('supports_vision')),
            'models_with_function_calling': sum(1 for m in models if m.get('capabilities', {}).get('supports_function_calling')),
            'models_with_streaming': sum(1 for m in models if m.get('capabilities', {}).get('supports_streaming')),
            'avg_context_length': sum(all_context_lengths) / len(all_context_lengths) if all_context_lengths else 0,
            'avg_prompt_price': sum(all_prompt_prices) / len(all_prompt_prices) if all_prompt_prices else 0,
            'avg_prompt_price_per_1m_tokens': (sum(all_prompt_prices) / len(all_prompt_prices) * 1000000) if all_prompt_prices else 0
        },
        'by_provider': provider_stats,
        'last_updated': data.get('last_updated'),
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    save_json(stats_data, api_dir / 'stats.json')


def generate_api_index(api_dir: Path) -> None:
    """Generate API index/documentation file."""
    api_docs = {
        'api_version': '1.0.0',
        'title': 'AI Model Catalog API',
        'description': 'RESTful API for querying AI model information from multiple providers',
        'base_url': 'https://jamesprial.github.io/fetcher/api',
        'endpoints': {
            'dynamic': {
                'url': '/api/',
                'description': 'Dynamic query endpoint with filtering, sorting, and pagination',
                'method': 'GET',
                'parameters': {
                    'provider': 'Filter by provider (comma-separated)',
                    'capability': 'Filter by capability (comma-separated)',
                    'search': 'Search in model name, ID, or description',
                    'min_context': 'Minimum context length',
                    'max_context': 'Maximum context length',
                    'min_prompt_price': 'Minimum prompt price per token',
                    'max_prompt_price': 'Maximum prompt price per token',
                    'supports_vision': 'Filter by vision support (true/false)',
                    'supports_function_calling': 'Filter by function calling (true/false)',
                    'supports_streaming': 'Filter by streaming support (true/false)',
                    'sort': 'Sort field (name, provider, context, prompt-price, etc.)',
                    'order': 'Sort order (asc, desc)',
                    'limit': 'Number of results',
                    'offset': 'Pagination offset',
                    'format': 'Output format (json, csv)'
                }
            },
            'static': {
                'providers': {
                    'url': '/api/providers/',
                    'description': 'List all providers',
                    'files': 'Individual provider files at /api/providers/{provider}.json'
                },
                'capabilities': {
                    'url': '/api/capabilities/',
                    'description': 'List all capabilities',
                    'files': 'Individual capability files at /api/capabilities/{capability}.json'
                },
                'stats': {
                    'url': '/api/stats.json',
                    'description': 'Summary statistics for all models and providers'
                },
                'all_models': {
                    'url': '/models.json',
                    'description': 'Complete model catalog (raw data)'
                }
            }
        },
        'examples': [
            {
                'description': 'Get all OpenAI models',
                'url': '/api/?provider=openai'
            },
            {
                'description': 'Get models with vision support',
                'url': '/api/?supports_vision=true'
            },
            {
                'description': 'Search for GPT-4 models',
                'url': '/api/?search=gpt-4'
            },
            {
                'description': 'Get cheapest models with 100k+ context',
                'url': '/api/?min_context=100000&sort=prompt-price&order=asc'
            }
        ],
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    save_json(api_docs, api_dir / 'api.json')


def main():
    """Main execution function."""
    # Determine paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    docs_dir = project_dir / 'docs'
    models_path = docs_dir / 'models.json'
    api_dir = docs_dir / 'api'

    print(f"Loading models from: {models_path}")

    # Load data
    data = load_models(models_path)

    print(f"Found {len(data.get('models', []))} models")
    print(f"Generating API endpoints in: {api_dir}")

    # Generate endpoints
    generate_provider_endpoints(data, api_dir)
    generate_capability_endpoints(data, api_dir)
    generate_stats_endpoint(data, api_dir)
    generate_api_index(api_dir)

    print("\nAPI endpoints generated successfully!")
    print(f"\nAccess the API at: https://jamesprial.github.io/fetcher/api/")


if __name__ == '__main__':
    main()
