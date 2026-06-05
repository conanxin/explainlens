"""Tests for provider response contract (response_contract.py)."""

import pytest
from pydantic import ValidationError

from explainlens.schemas import SourceChunk
from explainlens.providers.response_contract import (
    parse_provider_response,
    ProviderStructuredResponse,
    ProviderCardResponse,
    ProviderConceptMapResponse,
)


def _make_chunks(n: int = 4) -> list[SourceChunk]:
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{i+1:03d}",
                text=f"Chunk {i+1} content.",
                start_char=i * 100,
                end_char=(i + 1) * 100,
            )
        )
    return chunks


def _make_valid_response(n_cards: int = 8) -> dict:
    """Make a valid provider response dict."""
    cards = []
    for i in range(n_cards):
        cards.append({
            "title": f"Card {i+1}",
            "explanation": f"Explanation for card {i+1}.",
            "visual_metaphor": f"Metaphor {i+1}",
            "visual_scene": f"Scene {i+1}",
            "takeaway": f"Takeaway {i+1}",
            "source_chunk_ids": [f"chunk_00{(i % 4) + 1}"],
        })

    return {
        "concept_map": {
            "core_problem": "Understanding the content.",
            "key_concepts": ["Concept A", "Concept B"],
            "key_claims": ["Claim 1", "Claim 2"],
            "methods_or_mechanisms": ["Method 1"],
            "evidence_or_examples": ["Example 1"],
            "limitations": ["Limitation 1"],
            "why_it_matters": "It matters.",
        },
        "cards": cards,
        "provider_notes": ["Test note."],
    }


class TestParseProviderResponse:
    """Tests for parse_provider_response()."""

    def test_parses_valid_response(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        resp = parse_provider_response(raw, chunks)
        assert len(resp.cards) == 8
        assert resp.concept_map.core_problem == "Understanding the content."

    def test_rejects_unknown_source_chunk_id(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        # Introduce an unknown chunk_id
        raw["cards"][0]["source_chunk_ids"] = ["chunk_999"]
        with pytest.raises(ValueError, match="unknown source_chunk_ids"):
            parse_provider_response(raw, chunks)

    def test_rejects_less_than_8_cards(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(7)
        with pytest.raises(ValidationError, match=r"8 cards"):
            parse_provider_response(raw, chunks)

    def test_rejects_more_than_8_cards(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(9)
        with pytest.raises(ValidationError, match=r"8 cards"):
            parse_provider_response(raw, chunks)

    def test_rejects_empty_source_chunk_ids(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        raw["cards"][0]["source_chunk_ids"] = []
        with pytest.raises(ValidationError, match="at least one source_chunk_id"):
            parse_provider_response(raw, chunks)

    def test_all_cards_have_source_chunk_ids(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        resp = parse_provider_response(raw, chunks)
        for card in resp.cards:
            assert len(card.source_chunk_ids) > 0

    def test_all_source_chunk_ids_valid(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        resp = parse_provider_response(raw, chunks)
        known = {c.chunk_id for c in chunks}
        for card in resp.cards:
            for cid in card.source_chunk_ids:
                assert cid in known

    def test_provider_notes_preserved(self):
        chunks = _make_chunks(4)
        raw = _make_valid_response(8)
        raw["provider_notes"] = ["custom note"]
        resp = parse_provider_response(raw, chunks)
        assert resp.provider_notes == ["custom note"]


class TestProviderStructuredResponse:
    """Tests for ProviderStructuredResponse model."""

    def test_minimal_valid(self):
        resp = ProviderStructuredResponse(
            concept_map=ProviderConceptMapResponse(),
            cards=[
                ProviderCardResponse(
                    title="Test",
                    explanation="Test explanation",
                    source_chunk_ids=["chunk_001"],
                )
            ]
            * 8,
        )
        assert len(resp.cards) == 8

    def test_cards_count_validation(self):
        with pytest.raises(ValidationError, match=r"8 cards"):
            ProviderStructuredResponse(
                concept_map=ProviderConceptMapResponse(),
                cards=[
                    ProviderCardResponse(
                        title="Test",
                        explanation="Test",
                        source_chunk_ids=["chunk_001"],
                    )
                ]
                * 3,
            )
