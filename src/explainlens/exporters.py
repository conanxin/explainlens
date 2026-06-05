"""Data exporters — writes artifacts as JSON, Markdown, and HTML files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict, Optional

from explainlens.schemas import SourceChunk


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


def export_cards_markdown(cards: List[Any], chunks: Optional[List[SourceChunk]] = None) -> str:
    """Export cards as a Markdown document.

    Args:
        cards: List of ImageCard objects.
        chunks: Optional list of SourceChunk objects for page info.

    Returns:
        Markdown string.
    """
    lines = [
        "# ExplainLens — 图解解释卡",
        "",
        f"共 {len(cards)} 张卡片",
        "",
        "---",
        "",
    ]

    for i, card in enumerate(cards, 1):
        lines.append(f"## 卡片 {i}：{card.title}")
        lines.append("")
        lines.append(f"**解释**：{card.explanation}")
        lines.append("")
        lines.append(f"> **Takeaway**：{card.takeaway}")
        lines.append("")
        lines.append(f"**图片 Prompt**：")
        lines.append(f"```")
        lines.append(card.image_prompt)
        lines.append(f"```")
        lines.append("")
        source_line = f"**来源片段**：{', '.join(card.source_chunk_ids)}"
        source_line += _page_info(card.source_chunk_ids, chunks)
        lines.append(source_line)
        lines.append("")
        lines.append(f"> {card.source_excerpt}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
