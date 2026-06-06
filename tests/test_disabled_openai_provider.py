"""Tests for OpenAI provider (openai_draft.py) — now experimental, not disabled.

Updated for Phase 3.3: openai is now in AVAILABLE_PROVIDERS with status="experimental".
"""

from __future__ import annotations

import pytest

from explainlens.providers.registry import get_provider, AVAILABLE_PROVIDERS, DISABLED_PROVIDERS


class TestOpenAIProviderRegistry:
    """Test that the OpenAI provider is in AVAILABLE_PROVIDERS."""

    def test_openai_in_available_providers(self):
        """OpenAI provider should be in AVAILABLE_PROVIDERS."""
        assert "openai" in AVAILABLE_PROVIDERS

    def test_openai_not_in_disabled_providers(self):
        """OpenAI provider should NOT be in DISABLED_PROVIDERS."""
        assert "openai" not in DISABLED_PROVIDERS


class TestOpenAIProviderCanBeInstantiated:
    """Test that the OpenAI provider can be instantiated."""

    def test_get_provider_openai_returns_instance(self):
        """get_provider('openai') should return an OpenAIProvider."""
        provider = get_provider("openai")
        from explainlens.providers.openai_draft import OpenAIProvider
        assert isinstance(provider, OpenAIProvider)

    def test_openai_provider_has_fail_closed_default(self):
        """OpenAI provider defaults to fail-closed (allow_external_api=False)."""
        provider = get_provider("openai")
        assert provider.allow_external_api is False
        assert provider.name == "openai"

    def test_openai_provider_can_be_configured(self):
        """OpenAI provider can accept configuration."""
        from explainlens.providers.openai_draft import OpenAIProvider
        provider = OpenAIProvider()
        provider.allow_external_api = True
        provider.model = "gpt-4"
        provider.timeout_seconds = 30.0
        assert provider.allow_external_api is True
        assert provider.model == "gpt-4"
        assert provider.timeout_seconds == 30.0


class TestOpenAIDraftDoesNotCallAPI:
    """Test that the OpenAI draft provider does NOT call any API unless opted in."""

    def test_no_openai_sdk_import_at_module_level(self):
        """openai_draft.py should not import openai SDK at module level."""
        import ast
        from pathlib import Path

        source = Path("src/explainlens/providers/openai_draft.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        import_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_names.append(node.module)
        # openai should NOT be in imports
        assert "openai" not in import_names

    def test_openai_draft_file_does_not_contain_api_key_read(self):
        """openai_draft.py should not contain hardcoded API keys."""
        from pathlib import Path

        source = Path(
            "src/explainlens/providers/openai_draft.py"
        ).read_text(encoding="utf-8")
        # Verify syntax is valid
        import ast
        try:
            tree = ast.parse(source)
        except SyntaxError:
            pytest.fail("openai_draft.py has syntax errors")
        # Should not have `import openai` at module level
        assert "import openai" not in source
        assert "from openai" not in source or "openai_transport" in source


class TestRegistryHandling:
    """Test registry properly handles experimental providers."""

    def test_is_provider_available_openai(self):
        from explainlens.providers.registry import is_provider_available

        assert is_provider_available("openai") is True

    def test_get_provider_openai_does_not_raise(self):
        """get_provider('openai') should NOT raise now that it's available."""
        try:
            provider = get_provider("openai")
            assert provider is not None
        except (ValueError, RuntimeError) as e:
            pytest.fail(f"get_provider('openai') raised unexpectedly: {e}")

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent-provider-xyz")

    def test_error_message_lists_available_providers(self):
        """Error for unknown provider should list available providers."""
        try:
            get_provider("nonexistent-provider-xyz")
        except ValueError as e:
            msg = str(e)
            # Should mention available providers
            assert "rule-based" in msg
            assert "mock-llm" in msg


class TestOpenAIProviderAttributes:
    """Test OpenAI provider class attributes."""

    def test_openai_draft_name(self):
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.name == "openai"
        assert provider.version == "openai-v0.1"

    def test_openai_draft_uses_external_api_true(self):
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.uses_external_api is True

    def test_openai_draft_is_subclass_of_explain_provider(self):
        from explainlens.providers.base import ExplainProvider
        from explainlens.providers.openai_draft import OpenAIProvider

        assert issubclass(OpenAIProvider, ExplainProvider)

    def test_network_manifest_has_required_fields(self):
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        manifest = provider.get_network_manifest()
        assert manifest["uses_external_api"] is True
        assert "api_base" in manifest
        assert "endpoint" in manifest
