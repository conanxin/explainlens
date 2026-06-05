"""Tests for citation rendering in HTML and Markdown exports."""

from __future__ import annotations

from explainlens.schemas import ImageCard, SourceChunk
from explainlens.renderer import render_cards_html
from explainlens.exporters import export_cards_markdown


class TestHtmlCitations:
    def test_html_contains_source_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="source text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text from page 1",
                        start_char=0, end_char=24, page_start=1, page_end=1,
                        source_type="pdf"),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert "Source Appendix" in html

    def test_html_contains_source_anchor_href(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=1, page_end=1,
                        source_type="pdf"),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert 'href="#source-chunk_001"' in html

    def test_html_contains_source_anchor_id(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=1, page_end=1,
                        source_type="pdf"),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert 'id="source-chunk_001"' in html

    def test_html_card_has_id(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=1, page_end=1),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert 'id="card-card_01"' in html

    def test_html_shows_page_label(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=3, page_end=3,
                        source_type="pdf"),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert "page 3" in html

    def test_html_shows_used_by_in_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=1, page_end=1),
        ]

        html = render_cards_html(cards, "test.pdf", 1, chunks)
        assert "card_01" in html

    def test_html_without_chunks_no_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=[],
                      source_excerpt="text"),
        ]

        html = render_cards_html(cards, "test.txt", 0, None)
        # No chunks means empty appendix section
        assert "Source Appendix" in html


class TestMarkdownCitations:
    def test_markdown_contains_source_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="source text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text from page 1",
                        start_char=0, end_char=24, page_start=1, page_end=1,
                        source_type="pdf"),
        ]

        md = export_cards_markdown(cards, chunks)
        assert "## Source Appendix" in md

    def test_markdown_contains_page_label(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="source text",
                        start_char=0, end_char=11, page_start=2, page_end=2,
                        source_type="pdf"),
        ]

        md = export_cards_markdown(cards, chunks)
        assert "page 2" in md

    def test_markdown_contains_source_excerpt(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="excerpt text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="actual source content here",
                        start_char=0, end_char=29, page_start=1, page_end=1),
        ]

        md = export_cards_markdown(cards, chunks)
        assert "Source excerpt:" in md
        assert "excerpt text" in md

    def test_markdown_used_by_in_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=["chunk_001"],
                      source_excerpt="text"),
        ]
        chunks = [
            SourceChunk(chunk_id="chunk_001", text="hello world",
                        start_char=0, end_char=11),
        ]

        md = export_cards_markdown(cards, chunks)
        assert "Used by: card_01" in md

    def test_markdown_no_chunks_no_appendix(self):
        cards = [
            ImageCard(card_id="card_01", title="T1", explanation="e",
                      image_placeholder_svg="<svg/>", image_prompt="p",
                      takeaway="t", source_chunk_ids=[],
                      source_excerpt="text"),
        ]

        md = export_cards_markdown(cards, None)
        assert "## Source Appendix" not in md
        assert "## 卡片 1" in md
