"""Tests for page-aware chunking."""

from __future__ import annotations

from explainlens.chunker import chunk_text, _chunk_pdf_pages
from explainlens.schemas import SourcePage


# ── Page-aware chunking ──────────────────────────────────────────

def test_chunk_pdf_pages_basic():
    """Page-aware chunking must produce chunks with page metadata."""
    pages = [
        SourcePage(page_number=1, text="Page one content here.\n\nSecond paragraph.",
                   char_start=0, char_end=41),
        SourcePage(page_number=2, text="Page two content here.\n\nAnother paragraph.",
                   char_start=42, char_end=86),
    ]
    full_text = "Page one content here.\n\nSecond paragraph.\n\nPage two content here.\n\nAnother paragraph."
    chunks = _chunk_pdf_pages(full_text, pages, max_chunk_chars=900)
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"


def test_chunk_pdf_pages_have_page_numbers():
    """Every PDF chunk must have page_start and page_end set."""
    pages = [
        SourcePage(page_number=1, text="First page content here with enough text.",
                   char_start=0, char_end=45),
        SourcePage(page_number=2, text="Second page content here.",
                   char_start=46, char_end=75),
    ]
    full_text = "First page content here with enough text.\n\nSecond page content here."
    chunks = _chunk_pdf_pages(full_text, pages, max_chunk_chars=900)

    for ch in chunks:
        assert ch.page_start is not None, f"Chunk {ch.chunk_id} missing page_start"
        assert ch.page_end is not None, f"Chunk {ch.chunk_id} missing page_end"
        assert ch.source_type == "pdf"
        assert 1 <= ch.page_start <= 2
        assert 1 <= ch.page_end <= 2


def test_chunk_pdf_pages_empty_input():
    """Empty pages list must return empty chunks."""
    chunks = _chunk_pdf_pages("", [], max_chunk_chars=900)
    assert len(chunks) == 0


def test_chunk_pdf_pages_single_page():
    """Single page must produce exactly one chunk."""
    pages = [
        SourcePage(page_number=1, text="Single page content.",
                   char_start=0, char_end=21),
    ]
    chunks = _chunk_pdf_pages("Single page content.", pages, max_chunk_chars=900)
    assert len(chunks) == 1
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 1


def test_chunk_txt_does_not_set_page():
    """txt/md chunking must not set page fields."""
    text = "This is a test paragraph.\n\nAnother paragraph."
    chunks = chunk_text(text, source_type="txt")
    assert len(chunks) > 0
    for ch in chunks:
        assert ch.page_start is None
        assert ch.page_end is None
        assert ch.source_type == "txt"


def test_chunk_with_source_type_txt():
    """source_type must be 'txt' for text input."""
    text = "Paragraph one.\n\nParagraph two."
    chunks = chunk_text(text, source_type="txt")
    for ch in chunks:
        assert ch.source_type == "txt"


def test_approx_page_set_for_pdf():
    """PDF chunks must have approx_page set to page_start."""
    pages = [
        SourcePage(page_number=1, text="Page 1 text here.", char_start=0, char_end=17),
    ]
    chunks = _chunk_pdf_pages("Page 1 text here.", pages, max_chunk_chars=900)
    for ch in chunks:
        assert ch.approx_page == ch.page_start
