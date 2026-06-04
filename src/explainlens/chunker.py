"""Document chunker — splits text into manageable chunks by paragraphs."""

from __future__ import annotations

import re
from typing import List

from explainlens.schemas import SourceChunk


# Detect Markdown headings for section title extraction
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
# Paragraphs separated by blank lines
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


def chunk_text(text: str, max_chunk_chars: int = 2000) -> List[SourceChunk]:
    """Split text into chunks by paragraph, keeping each under max_chunk_chars.

    Each chunk preserves its character-offset span in the original text.
    Adjacent short paragraphs may be merged to avoid tiny chunks.

    Args:
        text: The full source text.
        max_chunk_chars: Soft maximum characters per chunk (default 2000).

    Returns:
        List of SourceChunk objects.
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
            # Fallback: find by first 50 chars
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
            section_title=section_title,
        ))

    return chunks
