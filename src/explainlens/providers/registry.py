"""Provider registry — maps provider names to provider classes.

Supports both available and disabled providers. Disabled providers
are listed for documentation but cannot be instantiated.
"""

from __future__ import annotations

from typing import List

from explainlens.providers.base import ExplainProvider
from explainlens.providers.contract import (
    ProviderCapabilities,
    capabilities_for_rule_based,
    capabilities_for_mock_llm,
    capabilities_for_openai,
    capabilities_for_local_fixture,
    capabilities_for_local_http,
)
from explainlens.providers.rule_based import RuleBasedProvider
from explainlens.providers.mock_llm import MockLLMProvider
from explainlens.providers.local_fixture import LocalFixtureProvider
from explainlens.providers.local_http import LocalHttpProvider


# ── Registry ──────────────────────────────────────────────────────

AVAILABLE_PROVIDERS: dict[str, type[ExplainProvider]] = {
    "rule-based": RuleBasedProvider,
    "mock-llm": MockLLMProvider,
    "local-fixture": LocalFixtureProvider,
    "local-http": LocalHttpProvider,
}

DISABLED_PROVIDERS: dict[str, type[ExplainProvider]] = {}

# Lazy import: OpenAI provider is experimental (not disabled)
try:
    from explainlens.providers.openai_draft import OpenAIProvider
    AVAILABLE_PROVIDERS["openai"] = OpenAIProvider
except ImportError:
    pass  # Graceful if the file is somehow missing

# All known providers (available + disabled)
_ALL_PROVIDERS = {**AVAILABLE_PROVIDERS, **DISABLED_PROVIDERS}

# Capability presets for known providers
_CAPABILITIES: dict[str, ProviderCapabilities] = {
    "rule-based": capabilities_for_rule_based(),
    "mock-llm": capabilities_for_mock_llm(),
    "openai": capabilities_for_openai(),
    "local-fixture": capabilities_for_local_fixture(),
    "local-http": capabilities_for_local_http(),
}


def get_provider(name: str) -> ExplainProvider:
    """Get a provider instance by name.

    Args:
        name: Provider name, e.g. 'rule-based' or 'mock-llm'.

    Returns:
        An initialized ExplainProvider instance.

    Raises:
        ValueError: If the provider name is not recognized.
        RuntimeError: If the provider is disabled.
    """
    if name not in _ALL_PROVIDERS:
        available = ", ".join(sorted(AVAILABLE_PROVIDERS.keys()))
        disabled = ", ".join(sorted(DISABLED_PROVIDERS.keys()))
        msg = f"Unknown provider: '{name}'."
        if available:
            msg += f"\nAvailable providers: {available}"
        if disabled:
            msg += f"\nDisabled providers: {disabled}"
        raise ValueError(msg)

    if name in DISABLED_PROVIDERS:
        caps = get_provider_capabilities(name)
        api_note = (
            "\nThis provider requires an external API and is not available "
            "in the current version."
            if caps and caps.uses_external_api
            else ""
        )
        # Instantiate to use the provider's own _DISABLED_MSG
        instance = DISABLED_PROVIDERS[name]()
        raise RuntimeError(str(instance._DISABLED_MSG))

    return AVAILABLE_PROVIDERS[name]()


def get_provider_capabilities(name: str) -> ProviderCapabilities | None:
    """Get the capability description for a provider.

    Args:
        name: Provider name.

    Returns:
        ProviderCapabilities if known, None otherwise.
    """
    return _CAPABILITIES.get(name)


def list_provider_capabilities() -> List[ProviderCapabilities]:
    """List capabilities for all known providers (available + disabled).

    Returns:
        A list of ProviderCapability objects.
    """
    result = []
    for name in sorted(_ALL_PROVIDERS.keys()):
        caps = _CAPABILITIES.get(name)
        if caps:
            result.append(caps)
    return result


def is_provider_available(name: str) -> bool:
    """Check whether a provider is available for use.

    Args:
        name: Provider name.

    Returns:
        True if the provider is available, False otherwise.
    """
    return name in AVAILABLE_PROVIDERS


def list_providers() -> List[dict[str, str]]:
    """List all available providers with metadata.

    Returns:
        A list of dicts with keys: name, version, uses_external_api.
    """
    result = []
    for name, cls in AVAILABLE_PROVIDERS.items():
        instance = cls()
        result.append({
            "name": name,
            "version": instance.version,
            "uses_external_api": instance.uses_external_api,
        })
    return result
