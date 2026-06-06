"""Data exporters — writes artifacts as JSON, Markdown, and HTML files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict, Optional

from explainlens.schemas import SourceChunk
from explainlens.source_index import format_source_label, build_card_source_links


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for Pydantic models and Path objects."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def write_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """Write data as a pretty-printed JSON file.

    Args:
        data: The data to serialize (must be JSON-serializable or Pydantic model).
        file_path: Output file path.
        indent: JSON indentation level.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, default=_json_serializer)


def write_text(content: str, file_path: Path) -> None:
    """Write plain text to a file.

    Args:
        content: Text content to write.
        file_path: Output file path.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def _page_info(chunk_ids: List[str], chunks: Optional[List[SourceChunk]] = None) -> str:
    """Build page info string for source references."""
    if not chunks:
        return ""
    chunk_by_id = {c.chunk_id: c for c in chunks}
    pages: set[int] = set()
    for cid in chunk_ids:
        ch = chunk_by_id.get(cid)
        if ch and ch.page_start:
            pages.add(ch.page_start)
        if ch and ch.page_end:
            pages.add(ch.page_end)
    if not pages:
        return ""
    sorted_pages = sorted(pages)
    if len(sorted_pages) == 1:
        return f" page {sorted_pages[0]}"
    return f" pages {sorted_pages[0]}-{sorted_pages[-1]}"


def export_cards_markdown(
    cards: List[Any],
    chunks: Optional[List[SourceChunk]] = None,
    image_adapter: Optional[str] = None,
    skip_images: bool = False,
) -> str:
    """Export cards as a Markdown document with source appendix.

    Each card's source section uses clickable-style citation labels.
    Document ends with a Source Appendix listing every chunk with its excerpt.

    Args:
        cards: List of ImageCard objects.
        chunks: Optional list of SourceChunk objects for page info and appendix.
        image_adapter: Name of image adapter used (None if skipped or default).
        skip_images: Whether image generation was skipped.

    Returns:
        Markdown string.
    """
    card_links = build_card_source_links(cards, chunks or [])

    lines = [
        "# ExplainLens — 图解解释卡",
        "",
        f"共 {len(cards)} 张卡片",
        "",
        "---",
        "",
    ]

    for i, card in enumerate(cards, 1):
        links = card_links.get(card.card_id, {})
        source_labels = links.get("labels", [])

        lines.append(f"## 卡片 {i}：{card.title}")
        lines.append("")
        lines.append(f"**解释**：{card.explanation}")
        lines.append("")
        lines.append(f"> **Takeaway**：{card.takeaway}")
        lines.append("")

        # Image reference (if image adapter was used)
        if not skip_images and image_adapter:
            lines.append(f"![{card.card_id}](images/{card.card_id}.svg)")
            lines.append("")

        lines.append(f"**图片 Prompt**：")
        lines.append(f"```")
        lines.append(card.image_prompt)
        lines.append(f"```")
        lines.append("")

        # Citation-style source line
        if source_labels:
            citation_parts = [f"`{label}`" for label in source_labels]
            lines.append(f"**Sources:** {', '.join(citation_parts)}")
        else:
            lines.append(f"**Sources:** `{', '.join(card.source_chunk_ids)}`")
        lines.append("")

        if card.source_excerpt:
            lines.append(f"> Source excerpt: {card.source_excerpt}")
            lines.append("")

        lines.append("---")
        lines.append("")

    if skip_images:
        lines.insert(5, "")
        lines.insert(6, "Image generation skipped.")
        lines.insert(7, "")
    elif image_adapter:
        lines.insert(5, "")
        lines.insert(6, f"Image adapter: {image_adapter}")
        lines.insert(7, "")

    # Source Appendix
    if chunks:
        lines.append("## Source Appendix")
        lines.append("")

        cards_by_chunk: dict[str, list[str]] = {}
        for card in cards:
            for cid in card.source_chunk_ids:
                cards_by_chunk.setdefault(cid, []).append(card.card_id)

        for ch in chunks:
            label = format_source_label(ch)
            lines.append(f"### {label}")
            lines.append("")

            used_by = cards_by_chunk.get(ch.chunk_id, [])
            if used_by:
                lines.append(f"Used by: {', '.join(used_by)}")
                lines.append("")

            if ch.section_title:
                lines.append(f"*Section: {ch.section_title}*")
                lines.append("")

            excerpt = ch.text
            if len(excerpt) > 500:
                excerpt = excerpt[:500] + "..."
            lines.append(f"> {excerpt}")
            lines.append("")

    return "\n".join(lines)
