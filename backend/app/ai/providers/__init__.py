"""AI Providers factory and registry."""

from typing import Optional
from backend.app.ai.providers.base import AIProvider
from backend.app.ai.providers.gemini_provider import GeminiProvider
from backend.app.ai.providers.mock_provider import MockAIProvider
from backend.app.ai.providers.openai_provider import OpenAIProvider
from backend.app.core.config import settings

_cached_provider: Optional[AIProvider] = None


def get_ai_provider(override_driver: Optional[str] = None) -> AIProvider:
    """Retrieves or instantiates the configured AI provider.
    
    Guarantees that test environments can run deterministically using the MockAIProvider
    without requiring third-party API keys or internet access.
    """
    global _cached_provider

    provider_name = override_driver or settings.AI_PROVIDER
    if settings.ENVIRONMENT == "test" and override_driver is None:
        provider_name = "mock"

    if provider_name == "openai":
        if _cached_provider is None or not isinstance(_cached_provider, OpenAIProvider):
            _cached_provider = OpenAIProvider()
        return _cached_provider

    if provider_name == "gemini":
        if _cached_provider is None or not isinstance(_cached_provider, GeminiProvider):
            _cached_provider = GeminiProvider()
        return _cached_provider

    # Default to deterministic mock provider
    if _cached_provider is None or not isinstance(_cached_provider, MockAIProvider):
        _cached_provider = MockAIProvider(model_name=settings.AI_MODEL)

    return _cached_provider


def set_ai_provider_instance(provider: Optional[AIProvider]) -> None:
    """Allows setting an explicit provider instance (e.g. for unit and integration test fixtures)."""
    global _cached_provider
    _cached_provider = provider


__all__ = [
    "AIProvider",
    "GeminiProvider",
    "MockAIProvider",
    "OpenAIProvider",
    "get_ai_provider",
    "set_ai_provider_instance",
]
