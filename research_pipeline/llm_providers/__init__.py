"""LLM Provider abstraction for research pipeline."""

from .base import LLMProvider, LLMResponse, LLMError
from .claude import ClaudeProvider
from .openai_provider import OpenAIProvider
from .mock import MockProvider

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMError",
    "ClaudeProvider",
    "OpenAIProvider",
    "MockProvider",
]


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory function to get LLM provider by name.

    Args:
        provider_name: Name of the provider ("claude", "openai", "mock")
        **kwargs: Additional configuration passed to provider constructor

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    providers = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "mock": MockProvider,
    }

    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(providers.keys())}"
        )

    return providers[provider_name](**kwargs)
