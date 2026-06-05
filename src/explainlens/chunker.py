"""Document chunker — splits text into manageable chunks by paragraphs.

Supports two modes:
- txt/md: paragraph-based chunking (original behavior)
- pdf: page-aware chunking that preserves page boundaries
"""

from __future__ import annotations

import re
from typing import List

from explainlens.schemas import SourceChunk, SourcePage


# Detect Markdown headings for section title extraction
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
# Paragraphs separated by blank lines
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


# ── txt / md chunking (original behavior) ────────────────────────

def _chunk_text_paragraphs(
    text: str,
    max_chunk_chars: int = 2000,
    source_type: str = "txt",
) -> List[SourceChunk]:
    """Split text into chunks by paragraph, keeping each under max_chunk_chars.

    Original behavior for txt and md inputs.
    """
    if not text.strip():
        return []

    # Extract all heading positions for section title assignment
    headings: List[tuple[int, str]] = []
    for m in _HEADING_RE.finditer(text):
        headings.append((m.start(), m.group(1).strip()))

    # Split into paragraph blocks
    raw_paragraphs = _PARAGRAPH_SPLIT_RE.split(text)

    # Group short adjacent paragraphs
    merged: List[str] = []
    current = ""
    for para in raw_paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        if current and len(current) + len(stripped) + 2 <= max_chunk_chars:
            current += "\n\n" + stripped
        else:
            if current:
                merged.append(current)
            current = stripped
    if current:
        merged.append(current)

    # Build chunks with offsets
    chunks: List[SourceChunk] = []
    search_start = 0

    for i, para_text in enumerate(merged):
        # Find this paragraph in the original text
        pos = text.find(para_text, search_start)
        if pos == -1:
            pos = text.find(para_text[:50], search_start)
            if pos == -1:
                pos = search_start

        start_char = pos
        end_char = pos + len(para_text)
        search_start = end_char

        # Find nearest preceding heading
        section_title = None
        for h_start, h_title in headings:
            if h_start <= start_char:
                section_title = h_title
            else:
                break

        chunk_id = f"chunk_{i + 1:03d}"

        chunks.append(SourceChunk(
            chunk_id=chunk_id,
            text=para_text,
            start_char=start_char,
            end_char=end_char,
            approx_page=None,
            page_start=None,
            page_end=None,
            section_title=section_title,
            source_type=source_type,
        ))

    return chunks


# ── PDF page-aware chunking ──────────────────────────────────────

def _chunk_pdf_pages(
    full_text: str,
    pages: List[SourcePage],
    max_chunk_chars: int = 900,
    min_chunk_chars: int = 120,
) -> List[SourceChunk]:
    """Split PDF text into page-aware chunks.

    Chunks prefer page boundaries: each chunk belongs to a single page
    unless a page contains very little text (merged with neighbors).
    Long pages are split into multiple chunks by paragraph.
    """
    if not pages:
        return []

    chunks: List[SourceChunk] = []
    chunk_index = 0

    for page in pages:
        page_text = page.text

        if not page_text.strip():
            # Empty page — skip, no chunk
            continue

        if len(page_text) <= max_chunk_chars:
            # Single-page chunk
            chunk_index += 1
            chunks.append(SourceChunk(
                chunk_id=f"chunk_{chunk_index:03d}",
                text=page_text.strip(),
                start_char=page.char_start,
                end_char=page.char_end,
                approx_page=page.page_number,
                page_start=page.page_number,
                page_end=page.page_number,
                section_title=None,
                source_type="pdf",
            ))
            continue

        # Long page — split into paragraphs within the page
        paragraphs = _PARAGRAPH_SPLIT_RE.split(page_text)
        current = ""
        current_start = page.char_start

        for para in paragraphs:
            stripped = para.strip()
            if not stripped:
                continue

            if (current
                    and len(current) + len(stripped) + 2 <= max_chunk_chars):
                current += "\n\n" + stripped
            else:
                if current and len(current) >= min_chunk_chars:
                    ch_start = page.char_start + page_text.find(current)
                    ch_end = ch_start + len(current)
                    chunk_index += 1
                    chunks.append(SourceChunk(
                        chunk_id=f"chunk_{chunk_index:03d}",
                        text=current,
                        start_char=ch_start,
                        end_char=ch_end,
                        approx_page=page.page_number,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        section_title=None,
                        source_type="pdf",
                    ))
                current = stripped

        # Flush remaining
        if current and len(current) >= min_chunk_chars:
            ch_start = page.char_start + page_text.find(current)
            ch_end = ch_start + len(current)
            chunk_index += 1
            chunks.append(SourceChunk(
                chunk_id=f"chunk_{chunk_index:03d}",
                text=current,
                start_char=ch_start,
                end_char=ch_end,
                approx_page=page.page_number,
                page_start=page.page_number,
                page_end=page.page_number,
                section_title=None,
                source_type="pdf",
            ))

    return chunks


# ── Public API ───────────────────────────────────────────────────

def chunk_text(
    text: str,
    max_chunk_chars: int = 2000,
    source_type: str = "txt",
    pages: List[SourcePage] | None = None,
) -> List[SourceChunk]:
    """Split source text into chunks.

    For txt/md: paragraph-based chunking.
    For pdf: page-aware chunking with page boundaries.

    Args:
        text: Full source text.
        max_chunk_chars: Soft maximum characters per chunk.
        source_type: 'txt', 'md', or 'pdf'.
        pages: List of SourcePage objects (required for PDF).

    Returns:
        List of SourceChunk objects.
    """
    if source_type == "pdf":
        if pages is None:
            # Fall back to paragraph-based if no page info
            return _chunk_text_paragraphs(text, max_chunk_chars, source_type)
        return _chunk_pdf_pages(text, pages, max_chunk_chars=900)
    else:
        return _chunk_text_paragraphs(text, max_chunk_chars, source_type)
