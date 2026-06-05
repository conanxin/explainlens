"""Tests for source_index.py — source_index.json generation and cross-references."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from explainlens.source_index import (
    format_source_label,
    build_card_source_links,
    build_source_index,
    build_source_quality,
)
from explainlens.schemas import SourceChunk, SourcePage, ImageCard


class TestFormatSourceLabel:
    def test_chunk_no_page(self):
        ch = SourceChunk(
            chunk_id="chunk_003", text="hello", start_char=0, end_char=5,
        )
        assert format_source_label(ch) == "chunk_003"

    def test_chunk_single_page(self):
        ch = SourceChunk(
            chunk_id="chunk_003", text="hello", start_char=0, end_char=5,
            page_start=2, page_end=2,
        )
        assert format_source_label(ch) == "chunk_003 · page 2"

    def test_chunk_page_range(self):
        ch = SourceChunk(
            chunk_id="chunk_007", text="hello", start_char=0, end_char=5,
            page_start=3, page_end=4,
        )
        assert format_source_label(ch) == "chunk_007 · pages 3-4"

    def test_chunk_approx_page(self):
        ch = SourceChunk(
            chunk_id="chunk_005", text="hello", start_char=0, end_char=5,
            approx_page=5,
        )
        assert format_source_label(ch) == "chunk_005 · page 5"


class TestBuildCardSourceLinks:
    def test_single_chunk_single_page(self):
        chunks = [
            SourceChunk(chunk_id="c1", text="t1", start_char=0, end_char=2,
                        page_start=1, page_end=1),
        ]
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["c1"], source_excerpt="e"),
        ]
        links = build_card_source_links(cards, chunks)
        assert links["card_01"]["chunk_ids"] == ["c1"]
        assert links["card_01"]["labels"] == ["c1 · page 1"]
        assert links["card_01"]["page_start"] == 1
        assert links["card_01"]["page_end"] == 1

    def test_multi_chunk_multi_page(self):
        chunks = [
            SourceChunk(chunk_id="c1", text="t1", start_char=0, end_char=2,
                        page_start=1, page_end=1),
            SourceChunk(chunk_id="c2", text="t2", start_char=3, end_char=5,
                        page_start=2, page_end=3),
        ]
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["c1", "c2"],
                      source_excerpt="e"),
        ]
        links = build_card_source_links(cards, chunks)
        assert "c1 · page 1" in links["card_01"]["labels"]
        assert "c2 · pages 2-3" in links["card_01"]["labels"]
        assert links["card_01"]["page_start"] == 1
        assert links["card_01"]["page_end"] == 3


class TestBuildSourceIndex:
    def test_pdf_source_index_structure(self):
        pages = [
            SourcePage(page_number=1, text="Page one content", char_start=0, char_end=16),
            SourcePage(page_number=2, text="Page two content", char_start=17, char_end=33),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="Page one content",
                        start_char=0, end_char=16,
                        page_start=1, page_end=1, source_type="pdf"),
            SourceChunk(chunk_id="chunk_002", text="Page two content",
                        start_char=17, end_char=33,
                        page_start=2, page_end=2, source_type="pdf"),
        ]
        cards = [
            ImageCard(card_id="card_01", title="Card 1", explanation="e1",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001", "chunk_002"],
                      source_excerpt="e"),
        ]

        si = build_source_index(chunks, cards, pages, "test.pdf", "pdf")

        assert si["input_type"] == "pdf"
        assert si["source_file"] == "test.pdf"
        assert si["page_count"] == 2
        assert si["chunk_count"] == 2
        assert "chunks_by_page" in si
        assert "1" in si["chunks_by_page"]
        assert "2" in si["chunks_by_page"]
        assert si["chunks_by_page"]["1"] == ["chunk_001"]
        assert si["chunks_by_page"]["2"] == ["chunk_002"]
        assert "cards_by_chunk" in si
        assert si["cards_by_chunk"]["chunk_001"] == ["card_01"]
        assert si["cards_by_chunk"]["chunk_002"] == ["card_01"]
        assert len(si["citations"]) == 2

    def test_txt_source_index(self):
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="Hello world",
                        start_char=0, end_char=11, source_type="txt"),
        ]
        cards = [
            ImageCard(card_id="card_01", title="C1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="e"),
        ]

        si = build_source_index(chunks, cards, input_type="txt")
        assert si["input_type"] == "txt"
        assert si["page_count"] is None
        assert si["chunks_by_page"] == {}

    def test_cards_by_chunk_mapping(self):
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="a", start_char=0, end_char=1),
            SourceChunk(chunk_id="chunk_002", text="b", start_char=2, end_char=3),
        ]
        cards = [
            ImageCard(card_id="card_01", title="C1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="e"),
            ImageCard(card_id="card_02", title="C2", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001", "chunk_002"],
                      source_excerpt="e"),
        ]

        si = build_source_index(chunks, cards)
        assert si["cards_by_chunk"]["chunk_001"] == ["card_01", "card_02"]
        assert si["cards_by_chunk"]["chunk_002"] == ["card_02"]

    def test_citation_excerpt_truncation(self):
        long_text = "x" * 700
        chunks = [
            SourceChunk(chunk_id="chunk_001", text=long_text,
                        start_char=0, end_char=700),
        ]
        cards = [
            ImageCard(card_id="card_01", title="C1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="e"),
        ]

        si = build_source_index(chunks, cards)
        assert len(si["citations"][0]["source_excerpt"]) <= 604  # 600 + "..."


class TestBuildSourceQuality:
    def test_pdf_with_empty_pages(self):
        pages = [
            SourcePage(page_number=1, text="content", char_start=0, char_end=7),
            SourcePage(page_number=2, text="", char_start=8, char_end=8),
            SourcePage(page_number=3, text="more", char_start=9, char_end=13),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="content",
                        start_char=0, end_char=7, page_start=1, page_end=1),
            SourceChunk(chunk_id="chunk_002", text="more",
                        start_char=9, end_char=13, page_start=3, page_end=3),
        ]

        sq = build_source_quality(chunks, pages)
        assert sq["empty_pages"] == [2]
        assert sq["has_page_aware_chunks"] is True
        assert sq["has_source_index"] is True

    def test_short_long_chunks(self):
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="hi",
                        start_char=0, end_char=2),
            SourceChunk(chunk_id="chunk_002", text="x" * 2000,
                        start_char=3, end_char=2003),
        ]

        sq = build_source_quality(chunks)
        assert "chunk_001" in sq["short_chunks"]
        assert "chunk_002" in sq["long_chunks"]

    def test_normal_chunks_no_warnings(self):
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="a" * 200,
                        start_char=0, end_char=200),
        ]

        sq = build_source_quality(chunks)
        assert sq["short_chunks"] == []
        assert sq["long_chunks"] == []
        assert sq["empty_pages"] == []
