"""Tests for mock-llm provider output quality and constraints."""

import json
from pathlib import Path

import pytest

from explainlens.providers.mock_llm import MockLLMProvider, _mock_concept_map
from explainlens.schemas import SourceChunk


# ── Sample chunks for testing ─────────────────────────────────────

def _make_chunks(texts: list[str]) -> list[SourceChunk]:
    """Create SourceChunk objects from a list of texts."""
    chunks = []
    offset = 0
    for i, text in enumerate(texts):
        end = offset + len(text)
        chunks.append(SourceChunk(
            chunk_id=f"chunk_{i + 1:03d}",
            text=text,
            start_char=offset,
            end_char=end,
        ))
        offset = end + 1
    return chunks


SAMPLE_CHUNKS = _make_chunks([
    "Machine learning models often face the challenge of overfitting. "
    "This is a critical problem that limits generalization to unseen data.",

    "We propose a novel regularization technique called DropConnect. "
    "This method randomly drops connections between neurons during training.",

    "Our experiments on CIFAR-10 and ImageNet demonstrate that DropConnect "
    "outperforms standard dropout by 2.3% on average across all benchmarks.",

    "The key insight is that dropping connections rather than activations "
    "preserves more information flow while still preventing co-adaptation.",

    "However, our approach has limitations. The computational cost increases "
    "by approximately 15%, and the method has not been tested on NLP tasks.",

    "Why this matters: improving generalization remains one of the most "
    "important open problems in deep learning research.",

    "The core mechanism involves randomly sampling a binary mask at each "
    "training step. This mask determines which connections are active.",

    "Future work should explore adaptive drop rates and applications "
    "to transformer architectures. We also note that the theoretical "
    "underpinnings of why DropConnect works are not yet fully understood.",
])


class TestMockConceptMap:
    """Tests for _mock_concept_map function."""

    def test_returns_concept_map(self):
        """Should return a valid ConceptMap."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        assert cm.core_problem, "core_problem should not be empty"
        assert len(cm.key_concepts) >= 1, "should have at least 1 key concept"

    def test_core_problem_is_narrative(self):
        """Core problem should use more conversational language."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        # The mock-llm should use narrative language like "The core tension here is"
        narrative = cm.core_problem.lower()
        assert ("challenge" in narrative or "problem" in narrative or
                "tension" in narrative or "question" in narrative or
                "explores" in narrative)

    def test_key_claims_not_empty(self):
        """Should extract some key claims."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        assert len(cm.key_claims) >= 1

    def test_methods_not_empty(self):
        """Should extract methods or mechanisms."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        assert len(cm.methods_or_mechanisms) >= 1

    def test_limitations_not_empty(self):
        """Should identify limitations."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        assert len(cm.limitations) >= 1

    def test_why_it_matters_not_empty(self):
        """Why it matters should not be empty."""
        cm = _mock_concept_map(SAMPLE_CHUNKS)
        assert cm.why_it_matters


class TestMockLLMProvider:
    """Tests for MockLLMProvider class."""

    def test_name_and_version(self):
        """Provider should have correct name and version."""
        provider = MockLLMProvider()
        assert provider.name == "mock-llm"
        assert provider.version == "mock-llm-v0.1"

    def test_no_external_api(self):
        """Should not call external APIs."""
        provider = MockLLMProvider()
        assert provider.uses_external_api is False

    def test_build_concept_map(self):
        """build_concept_map should return a valid ConceptMap."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        assert cm.core_problem
        assert len(cm.key_concepts) >= 1

    def test_build_teaching_plan_has_8_steps(self):
        """build_teaching_plan should produce exactly 8 steps."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        tp = provider.build_teaching_plan(SAMPLE_CHUNKS, cm)
        assert len(tp.steps) == 8
        for step in tp.steps:
            assert step.step_id, f"Step should have step_id"
            assert step.title, f"Step should have title"
            assert step.simple_explanation, f"Step should have explanation"

    def test_build_storyboard_has_8_panels(self):
        """build_storyboard should produce exactly 8 panels."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        tp = provider.build_teaching_plan(SAMPLE_CHUNKS, cm)
        sb = provider.build_storyboard(SAMPLE_CHUNKS, cm, tp)
        assert len(sb.panels) == 8
        for panel in sb.panels:
            assert panel.panel_id, f"Panel should have panel_id"
            assert panel.title, f"Panel should have title"
            assert len(panel.source_chunk_ids) >= 1, (
                f"Panel {panel.panel_id} should have at least 1 source chunk"
            )

    def test_build_cards_has_8_cards(self):
        """build_cards should produce exactly 8 cards."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        tp = provider.build_teaching_plan(SAMPLE_CHUNKS, cm)
        sb = provider.build_storyboard(SAMPLE_CHUNKS, cm, tp)
        cards = provider.build_cards(sb)
        assert len(cards) == 8

    def test_all_cards_have_source_chunk_ids(self):
        """Every card must have non-empty source_chunk_ids."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        tp = provider.build_teaching_plan(SAMPLE_CHUNKS, cm)
        sb = provider.build_storyboard(SAMPLE_CHUNKS, cm, tp)
        cards = provider.build_cards(sb)
        for card in cards:
            assert len(card.source_chunk_ids) >= 1, (
                f"Card {card.card_id} should reference at least one source chunk"
            )

    def test_teaching_plan_has_mock_llm_language(self):
        """Teaching plan should contain narrative/conversational language."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        tp = provider.build_teaching_plan(SAMPLE_CHUNKS, cm)
        # At least one step should contain narrative markers
        narrative_markers = [
            "Let me", "you might", "here's the thing", "imagine",
            "picture this", "let's be", "stepping back",
            "Teaching metaphor", "⚠",
        ]
        found = False
        for step in tp.steps:
            for marker in narrative_markers:
                if marker.lower() in step.simple_explanation.lower():
                    found = True
                    break
            if found:
                break
        assert found, (
            "Teaching plan should contain narrative language markers. "
            "Got steps: " + json.dumps([s.simple_explanation[:80] for s in tp.steps])
        )

    def test_mock_output_not_set_uses_external_api_true(self):
        """Mock provider output must NOT set uses_external_api=true."""
        provider = MockLLMProvider()
        assert provider.uses_external_api is False

    def test_concept_map_fields_are_strings_or_lists(self):
        """Concept map fields should have correct types."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map(SAMPLE_CHUNKS)
        assert isinstance(cm.core_problem, str)
        assert isinstance(cm.key_concepts, list)
        assert isinstance(cm.key_claims, list)
        assert isinstance(cm.methods_or_mechanisms, list)
        assert isinstance(cm.evidence_or_examples, list)
        assert isinstance(cm.limitations, list)
        assert isinstance(cm.why_it_matters, str)


class TestEmptyInput:
    """Tests for mock-llm with empty input."""

    def test_empty_chunks_produces_valid_output(self):
        """Should handle empty chunks gracefully."""
        provider = MockLLMProvider()
        cm = provider.build_concept_map([])
        assert cm is not None
        assert cm.core_problem == ""

        tp = provider.build_teaching_plan([], cm)
        assert len(tp.steps) == 8

        sb = provider.build_storyboard([], cm, tp)
        assert len(sb.panels) == 8

        cards = provider.build_cards(sb)
        assert len(cards) == 8
