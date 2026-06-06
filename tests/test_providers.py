"""Tests for provider registry and base class."""

import pytest

from explainlens.providers.base import ExplainProvider
from explainlens.providers.registry import (
    AVAILABLE_PROVIDERS,
    get_provider,
    list_providers,
)
from explainlens.providers.rule_based import RuleBasedProvider
from explainlens.providers.mock_llm import MockLLMProvider


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_registry_contains_rule_based(self):
        """Provider registry should contain 'rule-based'."""
        assert "rule-based" in AVAILABLE_PROVIDERS

    def test_registry_contains_mock_llm(self):
        """Provider registry should contain 'mock-llm'."""
        assert "mock-llm" in AVAILABLE_PROVIDERS

    def test_unknown_provider_raises_clear_error(self):
        """Unknown provider should raise ValueError with available providers."""
        with pytest.raises(ValueError) as exc_info:
            get_provider("nonexistent-provider")
        error_msg = str(exc_info.value)
        assert "nonexistent-provider" in error_msg
        assert "rule-based" in error_msg
        assert "mock-llm" in error_msg

    def test_get_provider_rule_based(self):
        """get_provider('rule-based') should return RuleBasedProvider instance."""
        provider = get_provider("rule-based")
        assert isinstance(provider, RuleBasedProvider)
        assert provider.name == "rule-based"
        assert provider.uses_external_api is False

    def test_get_provider_mock_llm(self):
        """get_provider('mock-llm') should return MockLLMProvider instance."""
        provider = get_provider("mock-llm")
        assert isinstance(provider, MockLLMProvider)
        assert provider.name == "mock-llm"
        assert provider.uses_external_api is False

    def test_list_providers_returns_all(self):
        """list_providers should return metadata for all providers."""
        providers = list_providers()
        names = {p["name"] for p in providers}
        assert "rule-based" in names
        assert "mock-llm" in names
        for p in providers:
            assert "version" in p
            assert "uses_external_api" in p
            # Non-external providers should have uses_external_api=False
            if p["name"] not in ("openai", "local-http"):
                assert p["uses_external_api"] is False


class TestExplainProvider:
    """Tests for the abstract base class."""

    def test_base_class_is_abstract(self):
        """ExplainProvider should not be directly instantiable."""
        with pytest.raises(TypeError):
            ExplainProvider()  # type: ignore[abstract]

    def test_rule_based_is_explain_provider(self):
        """RuleBasedProvider should be a subclass of ExplainProvider."""
        assert issubclass(RuleBasedProvider, ExplainProvider)

    def test_mock_llm_is_explain_provider(self):
        """MockLLMProvider should be a subclass of ExplainProvider."""
        assert issubclass(MockLLMProvider, ExplainProvider)

    def test_rule_based_has_no_external_api(self):
        """Rule-based provider should not call external APIs."""
        provider = RuleBasedProvider()
        assert provider.uses_external_api is False

    def test_mock_llm_has_no_external_api(self):
        """Mock LLM provider should not call external APIs."""
        provider = MockLLMProvider()
        assert provider.uses_external_api is False

    def test_both_providers_have_name(self):
        """All providers should define a non-empty name."""
        for name, cls in AVAILABLE_PROVIDERS.items():
            instance = cls()
            assert instance.name, f"Provider {name} has empty name"
            assert instance.name == name

    def test_both_providers_have_version(self):
        """All providers should define a non-empty version."""
        for name, cls in AVAILABLE_PROVIDERS.items():
            instance = cls()
            assert instance.version, f"Provider {name} has empty version"
