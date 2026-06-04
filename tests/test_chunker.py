"""Tests for document chunker."""

import pytest
from explainlens.chunker import chunk_text
from explainlens.schemas import SourceChunk


SAMPLE_TEXT = """This is the first paragraph. It contains some content.

This is the second paragraph. It has more text here.

This is the third paragraph, and it is also meaningful."""


def test_chunker_creates_chunks():
    """Chunker should produce at least one chunk from non-empty text."""
    chunks = chunk_text(SAMPLE_TEXT)
    assert len(chunks) > 0, "Expected at least one chunk"


def test_chunk_ids_are_unique():
    """Each chunk should have a unique chunk_id."""
    chunks = chunk_text(SAMPLE_TEXT)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs should be unique"


def test_chunks_have_char_offsets():
    """Each chunk should have start_char and end_char within the original text bounds."""
    chunks = chunk_text(SAMPLE_TEXT)
    for c in chunks:
        assert 0 <= c.start_char <= len(SAMPLE_TEXT), f"start_char out of range: {c.start_char}"
        assert c.start_char <= c.end_char <= len(SAMPLE_TEXT), f"end_char out of range: {c.end_char}"
        assert c.end_char > c.start_char, f"Chunk should have positive length"


def test_chunk_text_preserved():
    """The concatenation of chunk texts should be containable in the original."""
    chunks = chunk_text(SAMPLE_TEXT)
    for c in chunks:
        assert c.text in SAMPLE_TEXT, f"Chunk text not found in original: {c.text[:50]}"


def test_empty_text_returns_empty():
    """Empty text should produce zero chunks."""
    chunks = chunk_text("")
    assert len(chunks) == 0


def test_whitespace_text_returns_empty():
    """Whitespace-only text should produce zero chunks."""
    chunks = chunk_text("   \n\n  \n")
    assert len(chunks) == 0


def test_chunker_with_markdown_headings():
    """Chunker should detect section titles from markdown headings."""
    md_text = "# Introduction\n\n" + "This is the intro. " * 200 + "\n\n" + "## Methods\n\n" + "This section describes methods. " * 200
    chunks = chunk_text(md_text)
    assert len(chunks) >= 1, "Should produce at least one chunk"
    # At least one chunk should have a section_title detected from the heading
    has_section = any(c.section_title for c in chunks)
    assert has_section, "Should detect section_title from markdown headings"
