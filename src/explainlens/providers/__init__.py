"""Provider adapters for ExplainLens — swappable analysis backends."""

from explainlens.providers.base import ExplainProvider
from explainlens.providers.contract import (
    ProviderCapabilities,
    validate_provider_output,
)
from explainlens.providers.openai_draft import OpenAIDraftProvider
from explainlens.providers.local_fixture import LocalFixtureProvider
from explainlens.providers.local_http import LocalHttpProvider
from explainlens.providers.prompt_contract import (
    ProviderPromptChunk,
    ProviderPromptPack,
    build_prompt_pack,
)
from explainlens.providers.response_contract import (
    ProviderCardResponse,
    ProviderConceptMapResponse,
    ProviderStructuredResponse,
    parse_provider_response,
)
from explainlens.providers.fixture_transport import run_fixture_transport
from explainlens.providers.local_http_transport import (
    ProtocolType,
    is_local_endpoint,
    build_local_http_payload,
    call_local_http_provider,
    extract_structured_response_from_chat_json,
)
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
    "LocalFixtureProvider",
    "LocalHttpProvider",
    "ProviderPromptChunk",
    "ProviderPromptPack",
    "build_prompt_pack",
    "ProviderCardResponse",
    "ProviderConceptMapResponse",
    "ProviderStructuredResponse",
    "parse_provider_response",
    "run_fixture_transport",
    "ProtocolType",
    "is_local_endpoint",
    "build_local_http_payload",
    "call_local_http_provider",
    "extract_structured_response_from_chat_json",
    "AVAILABLE_PROVIDERS",
    "DISABLED_PROVIDERS",
    "get_provider",
    "get_provider_capabilities",
    "is_provider_available",
    "list_provider_capabilities",
    "list_providers",
]
