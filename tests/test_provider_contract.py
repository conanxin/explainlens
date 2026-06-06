"""Tests for provider contract (contract.py)."""

from __future__ import annotations

import pytest

from explainlens.providers.contract import (
    ProviderCapabilities,
    validate_provider_output,
)
from explainlens.providers.registry import (
    AVAILABLE_PROVIDERS,
    get_provider,
    get_provider_capabilities,
    is_provider_available,
    list_provider_capabilities,
)
from explainlens.schemas import ConceptMap, ImageCard, SourceChunk, Storyboard, TeachingPlan, TeachingStep


# ── ProviderCapabilities model ──────────────────────────────


class TestProviderCapabilities:
    """Test ProviderCapabilities model validation."""

    def test_rule_based_caps_status_available(self):
        caps = get_provider_capabilities("rule-based")
        assert caps is not None
        assert caps.status == "available"

    def test_mock_llm_caps_status_available(self):
        caps = get_provider_capabilities("mock-llm")
        assert caps is not None
        assert caps.status == "available"

    def test_openai_caps_status_experimental(self):
        caps = get_provider_capabilities("openai")
        assert caps is not None
        assert caps.status == "experimental"

    def test_openai_requires_api_key(self):
        caps = get_provider_capabilities("openai")
        assert caps.requires_api_key is True

    def test_openai_uses_external_api(self):
        caps = get_provider_capabilities("openai")
        assert caps.uses_external_api is True

    def test_rule_based_requires_no_api_key(self):
        caps = get_provider_capabilities("rule-based")
        assert caps.requires_api_key is False

    def test_mock_llm_requires_no_api_key(self):
        caps = get_provider_capabilities("mock-llm")
        assert caps.requires_api_key is False

    def test_rule_based_uses_external_api_false(self):
        caps = get_provider_capabilities("rule-based")
        assert caps.uses_external_api is False

    def test_mock_llm_uses_external_api_false(self):
        caps = get_provider_capabilities("mock-llm")
        assert caps.uses_external_api is False

    def test_capabilities_supports_pdf_and_text(self):
        for name in ["rule-based", "mock-llm", "openai"]:
            caps = get_provider_capabilities(name)
            assert caps.supports_pdf is True
            assert caps.supports_text is True

    def test_capabilities_preserves_source_chunk_ids(self):
        for name in ["rule-based", "mock-llm", "openai"]:
            caps = get_provider_capabilities(name)
            assert caps.preserves_source_chunk_ids is True

    def test_safety_manifest_no_uploads(self):
        caps = get_provider_capabilities("rule-based")
        safety = caps.safety_manifest()
        assert safety["uploads_documents"] is False

    def test_safety_manifest_no_secrets_written(self):
        caps = get_provider_capabilities("rule-based")
        safety = caps.safety_manifest()
        assert safety["writes_secrets"] is False


# ── validate_provider_output ────────────────────────────────


class TestValidateProviderOutput:
    """Test output validation function."""

    def _make_chunks(self, n=3):
        return [
            SourceChunk(chunk_id=f"chunk_{i:03d}", text=f"Text {i}",
                        start_char=i*100, end_char=(i+1)*100)
            for i in range(n)
        ]

    def _make_concept_map(self):
        return ConceptMap(
            core_problem="Test problem",
            key_concepts=["Concept A"],
            key_claims=["Claim 1"],
            methods_or_mechanisms=["Method X"],
            evidence_or_examples=["Evidence Y"],
            limitations=["Limitation Z"],
            why_it_matters="It matters.",
        )

    def _make_teaching_plan(self):
        return TeachingPlan(
            steps=[
                TeachingStep(
                    step_id=f"step_{i+1:02d}",
                    title=f"Step {i+1}",
                    teaching_goal="Learn",
                    source_chunk_ids=[f"chunk_{i:03d}"],
                    simple_explanation="Explain",
                    visual_metaphor="",
                    audience_level="beginner",
                    risk_note="",
                )
                for i in range(8)
            ]
        )

    def _make_storyboard(self, teaching_plan=None):
        from explainlens.schemas import StoryboardPanel
        if teaching_plan is None:
            teaching_plan = self._make_teaching_plan()
        panels = [
            StoryboardPanel(
                panel_id=f"panel_{i+1:02d}",
                title=step.title,
                source_chunk_ids=step.source_chunk_ids[:],
                plain_explanation=step.simple_explanation,
                visual_scene="Scene",
                characters=[],
                composition="",
                caption=step.title,
                takeaway="Takeaway",
                must_include=[],
                must_avoid=[],
                image_prompt="prompt",
                verification_status="pending",
            )
            for i, step in enumerate(teaching_plan.steps)
        ]
        return Storyboard(panels=panels)

    def _make_cards(self, n=8, chunk_ids=None):
        if chunk_ids is None:
            chunk_ids = ["chunk_000"]
        return [
            ImageCard(
                card_id=f"card_{i:02d}",
                title=f"Card {i}",
                explanation="Explanation text",
                source_chunk_ids=chunk_ids,
                image_prompt="prompt",
                teaching_note="Note",
                panel_id=f"panel_{i+1:02d}",
            )
            for i in range(n)
        ]

    def test_valid_output_no_errors(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards(chunk_ids=["chunk_000"])

        errors = validate_provider_output(
            provider_name="rule-based",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
            uses_external_api=False,
        )
        assert errors == []

    def test_empty_provider_name(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards()

        errors = validate_provider_output(
            provider_name="",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
        )
        assert any("Provider name is empty" in e for e in errors)

    def test_wrong_card_count(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards(n=5)  # 5 != 8

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
        )
        assert any("Expected 8 cards" in e for e in errors)

    def test_card_with_empty_source_chunk_ids(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards()
        cards[0].source_chunk_ids = []

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
        )
        assert any("empty source_chunk_ids" in e for e in errors)

    def test_invalid_chunk_id_in_card(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards()
        cards[0].source_chunk_ids = ["chunk_999"]  # Not in chunks

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
        )
        assert any("unknown chunk_id" in e for e in errors)

    def test_empty_cards(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=[],
        )
        assert any("No cards were generated" in e for e in errors)

    def test_empty_storyboard(self):
        chunks = self._make_chunks()
        concept_map = self._make_concept_map()
        teaching_plan = self._make_teaching_plan()
        empty_sb = Storyboard(panels=[])
        cards = self._make_cards()

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=concept_map,
            teaching_plan=teaching_plan,
            storyboard=empty_sb,
            cards=cards,
        )
        assert any("Storyboard has no panels" in e for e in errors)

    def test_empty_concept_map(self):
        chunks = self._make_chunks()
        empty_cm = ConceptMap()
        teaching_plan = self._make_teaching_plan()
        storyboard = self._make_storyboard(teaching_plan)
        cards = self._make_cards()

        errors = validate_provider_output(
            provider_name="test",
            chunks=chunks,
            concept_map=empty_cm,
            teaching_plan=teaching_plan,
            storyboard=storyboard,
            cards=cards,
        )
        assert any("Concept map is empty" in e for e in errors)


# ── Registry integration ───────────────────────────────────


class TestRegistryIntegration:
    """Test registry functions with contract."""

    def test_get_provider_capabilities_rule_based(self):
        caps = get_provider_capabilities("rule-based")
        assert caps is not None
        assert caps.name == "rule-based"

    def test_get_provider_capabilities_mock_llm(self):
        caps = get_provider_capabilities("mock-llm")
        assert caps is not None
        assert caps.name == "mock-llm"

    def test_get_provider_capabilities_openai(self):
        caps = get_provider_capabilities("openai")
        assert caps is not None
        assert caps.name == "openai"
        assert caps.status == "experimental"

    def test_list_provider_capabilities_count(self):
        caps_list = list_provider_capabilities()
        names = [c.name for c in caps_list]
        assert "rule-based" in names
        assert "mock-llm" in names
        assert "openai" in names

    def test_is_provider_available_rule_based(self):
        assert is_provider_available("rule-based") is True

    def test_is_provider_available_mock_llm(self):
        assert is_provider_available("mock-llm") is True

    def test_is_provider_available_openai(self):
        assert is_provider_available("openai") is True

    def test_get_provider_does_not_raise_for_openai(self):
        """get_provider('openai') should succeed now that it's available (experimental)."""
        provider = get_provider("openai")
        assert provider is not None

    def test_get_provider_raises_for_unknown(self):
        with pytest.raises(ValueError):
            get_provider("nonexistent-provider-xyz")
