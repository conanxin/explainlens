"""Provider registry — maps provider names to provider classes."""

from __future__ import annotations

from explainlens.providers.base import ExplainProvider
from explainlens.providers.rule_based import RuleBasedProvider
from explainlens.providers.mock_llm import MockLLMProvider


# ── Registry ──────────────────────────────────────────────────────

AVAILABLE_PROVIDERS: dict[str, type[ExplainProvider]] = {
    "rule-based": RuleBasedProvider,
    "mock-llm": MockLLMProvider,
}


def get_provider(name: str) -> ExplainProvider:
    """Get a provider instance by name.

    Args:
        name: Provider name, e.g. 'rule-based' or 'mock-llm'.

    Returns:
        An initialized ExplainProvider instance.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    if name not in AVAILABLE_PROVIDERS:
        available = ", ".join(sorted(AVAILABLE_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown provider: '{name}'. "
            f"Available providers: {available}"
        )
    return AVAILABLE_PROVIDERS[name]()


def list_providers() -> list[dict[str, str]]:
    """List all available providers with metadata.

    Returns:
        A list of dicts with keys: name, version, uses_external_api.
    """
    result = []
    for name, cls in AVAILABLE_PROVIDERS.items():
        # Instantiate to get instance attributes
        instance = cls()
        result.append({
            "name": name,
            "version": instance.version,
            "uses_external_api": instance.uses_external_api,
        })
    return result
