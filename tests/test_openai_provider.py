"""Tests for OpenAIProvider (openai_draft.py).

All tests use mock fixtures — NO real API calls are made.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest

from explainlens.providers.openai_draft import OpenAIProvider
from explainlens.providers.registry import (
    AVAILABLE_PROVIDERS,
    get_provider,
    get_provider_capabilities,
)


# ── Helpers ──────────────────────────────────────────────────

def _make_chunks():
    """Create minimal source chunks for testing."""
    from explainlens.schemas import SourceChunk

    return [
        SourceChunk(
            chunk_id="c0",
            text="Sample text for testing OpenAI provider.",
            start_char=0,
            end_char=42,
            source_type="txt",
        ),
    ]


def _make_mock_api_result():
    """Create a mock API result matching the expected structure."""
    return {
        "concept_map": {
            "core_problem": "Testing OpenAI provider",
            "key_concepts": ["concept A", "concept B"],
            "key_claims": ["claim 1"],
        },
        "cards": [
            {
                "title": "Test Card 1",
                "explanation": "Explanation 1",
                "visual_metaphor": "A test",
                "visual_scene": "Test scene",
                "takeaway": "Test well",
                "source_chunk_ids": ["c0"],
            },
            {
                "title": "Test Card 2",
                "explanation": "Explanation 2",
                "source_chunk_ids": ["c0"],
            },
        ],
        "provider_notes": ["note 1"],
    }


# ── Provider Status Tests ─────────────────────────────────────

class TestOpenAIProviderExperimentalStatus:
    """Test that the OpenAI provider has experimental status."""

    def test_provider_is_experimental(self):
        provider = OpenAIProvider()
        assert provider.name == "openai"
        assert provider.version == "openai-v0.1"
        assert provider.uses_external_api is True

    def test_provider_in_available_providers(self):
        """OpenAI provider should now be in AVAILABLE_PROVIDERS (not disabled)."""
        assert "openai" in AVAILABLE_PROVIDERS

    def test_get_provider_returns_instance(self):
        """get_provider('openai') should return an OpenAIProvider instance."""
        provider = get_provider("openai")
        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"


class TestOpenAIProviderCapabilities:
    """Test OpenAI provider capabilities."""

    def test_capabilities_exist(self):
        caps = get_provider_capabilities("openai")
        assert caps is not None
        assert caps.name == "openai"
        assert caps.status == "experimental"
        assert caps.uses_external_api is True
        assert caps.requires_api_key is True
        assert caps.supports_pdf is True
        assert caps.supports_text is True
        assert caps.preserves_source_chunk_ids is True


# ── Fail-Closed Tests ────────────────────────────────────────

class TestOpenAIProviderFailClosed:
    """Test that OpenAIProvider is fail-closed by default."""

    def test_allow_external_api_defaults_to_false(self):
        provider = OpenAIProvider()
        assert provider.allow_external_api is False

    def test_build_concept_map_raises_without_enabling(self):
        provider = OpenAIProvider()
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            provider.build_concept_map(_make_chunks())

    def test_build_concept_map_raises_without_api_key(self):
        provider = OpenAIProvider()
        provider.allow_external_api = True
        # Ensure OPENAI_API_KEY is not set (use monkeypatch-style)
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
                provider.build_concept_map(_make_chunks())
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved

    def test_rejects_missing_api_key(self):
        provider = OpenAIProvider()
        provider.allow_external_api = True
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            provider._check_fail_closed()


class TestOpenAIProviderApiKeyHandling:
    """Test API key handling in OpenAIProvider."""

    def test_get_api_key_reads_from_env(self):
        provider = OpenAIProvider()
        saved = os.environ.get("OPENAI_API_KEY", None)
        try:
            os.environ["OPENAI_API_KEY"] = "sk-test123"
            key = provider._get_api_key()
            assert key == "sk-test123"
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_get_api_key_returns_empty_when_not_set(self):
        provider = OpenAIProvider()
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            key = provider._get_api_key()
            assert key == ""
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved


# ── Provider Manifest Tests ──────────────────────────────────

class TestOpenAIProviderManifest:
    """Test provider manifest generation."""

    def test_manifest_includes_external_api(self):
        provider = OpenAIProvider()
        manifest = provider.get_network_manifest()
        assert manifest["uses_external_api"] is True
        assert manifest["api_base"] == "https://api.openai.com/v1"
        assert manifest["endpoint"] == "/responses"
        assert "allow_external_api" in manifest
        assert "timeout_seconds" in manifest

    def test_manifest_reflects_allow_external_api_state(self):
        provider = OpenAIProvider()
        manifest = provider.get_network_manifest()
        assert manifest["allow_external_api"] is False

        provider.allow_external_api = True
        manifest = provider.get_network_manifest()
        assert manifest["allow_external_api"] is True


# ── build_concept_map with mock transport ────────────────────

class TestOpenAIProviderBuildConceptMap:
    """Test build_concept_map with mocked transport (no real API)."""

    def test_build_concept_map_with_mock_api(self):
        """Verify build_concept_map works with mocked API response."""
        provider = OpenAIProvider()
        provider.allow_external_api = True

        mock_result = _make_mock_api_result()

        with patch(
            "explainlens.providers.openai_draft.call_openai_responses_api",
            return_value=mock_result,
        ), patch(
            "explainlens.providers.openai_draft.OpenAIProvider._get_api_key",
            return_value="sk-mock",
        ):
            concept_map = provider.build_concept_map(_make_chunks())
            assert concept_map.core_problem == "Testing OpenAI provider"
            assert len(concept_map.key_concepts) == 2
            assert len(concept_map.key_claims) == 1

    def test_build_cards_preserves_source_chunk_ids(self):
        """Verify source_chunk_ids are preserved from API response."""
        provider = OpenAIProvider()
        provider.allow_external_api = True
        provider._last_result = _make_mock_api_result()

        from explainlens.schemas import Storyboard, StoryboardPanel
        storyboard = Storyboard(panels=[
            StoryboardPanel(
                panel_id="panel_000",
                title="Panel 1",
                key_concept="Testing",
                visual_metaphor="A test",
                image_prompt="Test image",
            ),
            StoryboardPanel(
                panel_id="panel_001",
                title="Panel 2",
                key_concept="Testing 2",
                visual_metaphor="Another test",
                image_prompt="Test image 2",
            ),
        ])

        cards = provider.build_cards(storyboard)
        assert len(cards) == 2
        assert cards[0].source_chunk_ids == ["c0"]
        assert cards[1].source_chunk_ids == ["c0"]

    def test_build_cards_without_prior_call_raises(self):
        """Calling build_cards before build_concept_map should raise."""
        provider = OpenAIProvider()
        provider.allow_external_api = True

        from explainlens.schemas import Storyboard, StoryboardPanel
        storyboard = Storyboard(panels=[
            StoryboardPanel(
                panel_id="panel_000",
                title="P1",
                key_concept="K",
                visual_metaphor="V",
                image_prompt="I",
            ),
        ])

        with pytest.raises(RuntimeError, match="no stored result"):
            provider.build_cards(storyboard)
