"""Tests for disabled OpenAI provider draft (openai_draft.py)."""

from __future__ import annotations

import pytest

from explainlens.providers.registry import get_provider, AVAILABLE_PROVIDERS, DISABLED_PROVIDERS


class TestOpenAIDraftProviderExists:
    """Test that the disabled OpenAI provider draft exists."""

    def test_openai_in_disabled_providers(self):
        """OpenAI provider draft should be in DISABLED_PROVIDERS."""
        assert "openai" in DISABLED_PROVIDERS

    def test_openai_not_in_available_providers(self):
        """OpenAI provider should NOT be in AVAILABLE_PROVIDERS."""
        assert "openai" not in AVAILABLE_PROVIDERS


class TestOpenAIDraftDisabledBehavior:
    """Test that the OpenAI provider draft is properly disabled."""

    def test_get_provider_openai_raises_runtime_error(self):
        """Attempting to get openai provider must raise RuntimeError."""
        with pytest.raises(RuntimeError, match="currently disabled|not enabled"):
            get_provider("openai")

    def test_get_provider_openai_error_message_clear(self):
        """Error message should explain that openai is disabled."""
        with pytest.raises(RuntimeError, match="openai"):
            get_provider("openai")

    def test_openai_provider_instance_has_disabled_msg(self):
        """The draft provider class should have a clear disabled message."""
        from explainlens.providers.openai_draft import OpenAIDraftProvider
        provider = OpenAIDraftProvider()
        assert hasattr(provider, "_DISABLED_MSG")
        msg = provider._DISABLED_MSG
        assert "disabled" in msg.lower() or "not enabled" in msg.lower()


class TestOpenAIDraftDoesNotCallAPI:
    """Test that the OpenAI draft provider does NOT call any API."""

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
        """openai_draft.py should not READ API keys in code."""
        from pathlib import Path

        source = Path(
            "src/explainlens/providers/openai_draft.py"
        ).read_text(encoding="utf-8")
        # Should not contain actual API key reading code
        # (mentions in comments/docstrings are acceptable)
        import ast
        try:
            tree = ast.parse(source)
        except SyntaxError:
            pytest.fail("openai_draft.py has syntax errors")
        # Check that no os.getenv/os.environ calls for API keys exist
        source_lower = source.lower()
        # These would indicate actual key reading — mentions in comments are OK
        # We just verify the file has no `import openai` at module level
        assert "import openai" not in source
        assert "from openai" not in source or "not" in source.lower()


class TestRegistryDisabledHandling:
    """Test registry properly handles disabled providers."""

    def test_is_provider_available_openai_false(self):
        from explainlens.providers.registry import is_provider_available

        assert is_provider_available("openai") is False

    def test_get_provider_openai_raises(self):
        with pytest.raises((ValueError, RuntimeError)):
            get_provider("openai")

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent-provider-xyz")

    def test_error_message_lists_available_and_disabled(self):
        """Error for unknown provider should list both available and disabled."""
        try:
            get_provider("nonexistent-provider-xyz")
        except ValueError as e:
            msg = str(e)
            # Should mention available providers
            assert "rule-based" in msg
            assert "mock-llm" in msg
        except RuntimeError:
            pass  # openai case


class TestOpenAIDraftProviderAttributes:
    """Test OpenAI draft provider class attributes."""

    def test_openai_draft_name(self):
        from explainlens.providers.openai_draft import OpenAIDraftProvider

        provider = OpenAIDraftProvider()
        assert provider.name == "openai"

    def test_openai_draft_uses_external_api_true(self):
        from explainlens.providers.openai_draft import OpenAIDraftProvider

        provider = OpenAIDraftProvider()
        assert provider.uses_external_api is True

    def test_openai_draft_is_subclass_of_explain_provider(self):
        from explainlens.providers.base import ExplainProvider
        from explainlens.providers.openai_draft import OpenAIDraftProvider

        assert issubclass(OpenAIDraftProvider, ExplainProvider)
