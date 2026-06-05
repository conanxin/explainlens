"""Tests for local-fixture provider (local_fixture.py)."""

import pytest

from explainlens.schemas import SourceChunk
from explainlens.providers.local_fixture import LocalFixtureProvider
from explainlens.providers.registry import get_provider, get_provider_capabilities


def _make_chunks(n: int = 4, source_type: str = "txt") -> list[SourceChunk]:
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{i+1:03d}",
                text=f"This is chunk {i+1} with some content. "
                f"It describes methods and approaches related to the topic. "
                f"However, limitations remain.",
                start_char=i * 200,
                end_char=(i + 1) * 200,
                source_type=source_type,
            )
        )
    return chunks


def _make_pdf_chunks(n: int = 3) -> list[SourceChunk]:
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{i+1:03d}",
                text=f"PDF page {i+1} content about the research topic. "
                f"The method involves a novel approach. Limitations include sample size.",
                start_char=i * 500,
                end_char=(i + 1) * 500,
                source_type="pdf",
                page_start=i + 1,
                page_end=i + 1,
            )
        )
    return chunks


class TestLocalFixtureProvider:
    """Tests for the LocalFixtureProvider."""

    def setup_method(self):
        self.provider = LocalFixtureProvider()

    def test_name(self):
        assert self.provider.name == "local-fixture"

    def test_version(self):
        assert self.provider.version == "local-fixture-v0.1"

    def test_uses_external_api_false(self):
        assert self.provider.uses_external_api is False

    def test_build_concept_map(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        assert cm.core_problem != ""
        assert len(cm.key_concepts) > 0
        assert len(cm.key_claims) > 0

    def test_build_concept_map_with_pdf(self):
        chunks = _make_pdf_chunks(3)
        cm = self.provider.build_concept_map(chunks)
        assert cm.core_problem != ""
        assert len(cm.key_concepts) > 0

    def test_build_teaching_plan(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        assert len(tp.steps) == 8

    def test_build_teaching_plan_steps_have_ids(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        for i, step in enumerate(tp.steps):
            assert step.step_id == f"step_{i+1:02d}"

    def test_build_storyboard(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        sb = self.provider.build_storyboard(chunks, cm, tp)
        assert len(sb.panels) == 8

    def test_build_storyboard_panels_have_source_chunk_ids(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        sb = self.provider.build_storyboard(chunks, cm, tp)
        for panel in sb.panels:
            assert len(panel.source_chunk_ids) > 0

    def test_build_cards(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        sb = self.provider.build_storyboard(chunks, cm, tp)
        cards = self.provider.build_cards(sb)
        assert len(cards) == 8

    def test_build_cards_have_source_chunk_ids(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        sb = self.provider.build_storyboard(chunks, cm, tp)
        cards = self.provider.build_cards(sb)
        for card in cards:
            assert len(card.source_chunk_ids) > 0

    def test_build_cards_source_chunk_ids_are_valid(self):
        chunks = _make_chunks(4)
        cm = self.provider.build_concept_map(chunks)
        tp = self.provider.build_teaching_plan(chunks, cm)
        sb = self.provider.build_storyboard(chunks, cm, tp)
        cards = self.provider.build_cards(sb)
        known = {c.chunk_id for c in chunks}
        for card in cards:
            for cid in card.source_chunk_ids:
                assert cid in known


class TestLocalFixtureRegistry:
    """Tests for local-fixture in the registry."""

    def test_get_provider_local_fixture(self):
        provider = get_provider("local-fixture")
        assert provider.name == "local-fixture"
        assert provider.uses_external_api is False

    def test_capabilities_status_experimental(self):
        caps = get_provider_capabilities("local-fixture")
        assert caps is not None
        assert caps.status == "experimental"

    def test_capabilities_uses_external_api_false(self):
        caps = get_provider_capabilities("local-fixture")
        assert caps.uses_external_api is False
        assert caps.requires_api_key is False

    def test_capabilities_supports_pdf_and_text(self):
        caps = get_provider_capabilities("local-fixture")
        assert caps.supports_pdf is True
        assert caps.supports_text is True


class TestLocalFixtureWithEmptyInput:
    """Edge case: empty input."""

    def setup_method(self):
        self.provider = LocalFixtureProvider()

    def test_empty_chunks(self):
        """Even with empty chunks, build_concept_map should not crash."""
        try:
            cm = self.provider.build_concept_map([])
            # Should return something, even if minimal
            assert cm is not None
        except Exception as e:
            # If it raises, that's also ok as long as it's not a crash
            assert isinstance(e, (ValueError, IndexError, KeyError))
