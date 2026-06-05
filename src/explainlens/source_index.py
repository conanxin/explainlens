"""Source index builder — maps cards to chunks to pages for citation UX.

Produces source_index.json with cross-references between source chunks,
pages, and explainer cards. Used by HTML and Markdown exporters for
clickable citations.
"""

from __future__ import annotations

from typing import List, Optional

from explainlens.schemas import SourceChunk, SourcePage, ImageCard


def format_source_label(chunk: SourceChunk) -> str:
    """Build a human-readable label for a source chunk.

    Examples:
        chunk_003
        chunk_003 · page 2
        chunk_007 · pages 3-4
    """
    label = chunk.chunk_id
    if chunk.page_start is not None and chunk.page_end is not None:
        if chunk.page_start == chunk.page_end:
            label += f" · page {chunk.page_start}"
        else:
            label += f" · pages {chunk.page_start}-{chunk.page_end}"
    elif chunk.approx_page is not None:
        label += f" · page {chunk.approx_page}"
    return label


def build_card_source_links(
    cards: List[ImageCard],
    chunks: List[SourceChunk],
) -> dict[str, dict]:
    """Build a lookup dict from card_id to its source chunk details.

    Returns:
        Dict keyed by card_id with:
          - chunk_ids: list of chunk IDs this card references
          - labels: human-readable citation labels
          - page_start/page_end: first and last page referenced
    """
    chunk_by_id = {c.chunk_id: c for c in chunks}
    result: dict[str, dict] = {}

    for card in cards:
        labels: list[str] = []
        pages: set[int] = set()
        for cid in card.source_chunk_ids:
            ch = chunk_by_id.get(cid)
            if ch:
                labels.append(format_source_label(ch))
                if ch.page_start:
                    pages.add(ch.page_start)
                if ch.page_end:
                    pages.add(ch.page_end)

        result[card.card_id] = {
            "chunk_ids": list(card.source_chunk_ids),
            "labels": labels,
            "page_start": min(pages) if pages else None,
            "page_end": max(pages) if pages else None,
        }

    return result


def build_source_index(
    chunks: List[SourceChunk],
    cards: List[ImageCard],
    pages: Optional[List[SourcePage]] = None,
    source_file: str = "",
    input_type: str = "txt",
) -> dict:
    """Build the complete source_index.json data structure.

    Args:
        chunks: All source chunks from the document.
        cards: All generated explainer cards.
        pages: Source pages (required for PDF input).
        source_file: Path to the input file.
        input_type: 'txt', 'md', or 'pdf'.

    Returns:
        Dict ready for JSON serialization representing the full source index.
    """
    page_count = len(pages) if pages else None

    # chunks_by_page: map page number → list of chunk IDs
    chunks_by_page: dict[str, list[str]] = {}
    for ch in chunks:
        if ch.page_start is not None and ch.page_end is not None:
            for p in range(ch.page_start, ch.page_end + 1):
                key = str(p)
                chunks_by_page.setdefault(key, []).append(ch.chunk_id)

    # cards_by_chunk: map chunk ID → list of card IDs
    cards_by_chunk: dict[str, list[str]] = {}
    for card in cards:
        for cid in card.source_chunk_ids:
            cards_by_chunk.setdefault(cid, []).append(card.card_id)

    # Build citations list
    citations: list[dict] = []
    for ch in chunks:
        used_by = cards_by_chunk.get(ch.chunk_id, [])
        excerpt = ch.text
        if len(excerpt) > 600:
            excerpt = excerpt[:600] + "..."
        citation = {
            "citation_id": f"src-{ch.chunk_id.split('_')[1]}" if "_" in ch.chunk_id else f"src-{ch.chunk_id}",
            "chunk_id": ch.chunk_id,
            "page_start": ch.page_start,
            "page_end": ch.page_end,
            "source_excerpt": excerpt,
            "used_by_cards": used_by,
        }
        if ch.section_title:
            citation["section_title"] = ch.section_title
        citations.append(citation)

    return {
        "input_type": input_type,
        "source_file": source_file,
        "page_count": page_count,
        "chunk_count": len(chunks),
        "chunks_by_page": chunks_by_page,
        "cards_by_chunk": cards_by_chunk,
        "citations": citations,
    }


def build_source_quality(
    chunks: List[SourceChunk],
    pages: Optional[List[SourcePage]] = None,
) -> dict:
    """Build source quality metadata for run_summary.json.

    Returns:
        Dict with empty_pages, short_chunks, long_chunks, and flags.
    """
    empty_pages: list[int] = []
    if pages:
        for p in pages:
            if not p.text.strip():
                empty_pages.append(p.page_number)

    short_chunks: list[str] = []
    long_chunks: list[str] = []
    for ch in chunks:
        text_len = len(ch.text.strip())
        if text_len < 80:
            short_chunks.append(ch.chunk_id)
        if text_len > 1500:
            long_chunks.append(ch.chunk_id)

    return {
        "empty_pages": empty_pages,
        "short_chunks": short_chunks,
        "long_chunks": long_chunks,
        "has_page_aware_chunks": any(
            ch.page_start is not None for ch in chunks
        ),
        "has_source_index": True,
    }
