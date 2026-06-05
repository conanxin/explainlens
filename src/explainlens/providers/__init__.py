"""Provider adapters for ExplainLens — swappable analysis backends."""

from explainlens.providers.base import ExplainProvider
from explainlens.providers.contract import (
    ProviderCapabilities,
    validate_provider_output,
)
from explainlens.providers.openai_draft import OpenAIDraftProvider
from explainlens.providers.registry import (
    AVAILABLE_PROVIDERS,
    DISABLED_PROVIDERS,
    get_provider,
    get_provider_capabilities,
    is_provider_available,
    list_provider_capabilities,
    list_providers,
)

__all__ = [
    "ExplainProvider",
    "ProviderCapabilities",
    "validate_provider_output",
    "OpenAIDraftProvider",
    "AVAILABLE_PROVIDERS",
    "DISABLED_PROVIDERS",
    "get_provider",
    "get_provider_capabilities",
    "is_provider_available",
    "list_provider_capabilities",
    "list_providers",
]
