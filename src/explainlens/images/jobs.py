"""Image jobs — build and write image_jobs.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard


def build_image_jobs(
    cards: Sequence[ImageCard],
    *,
    adapter: str = "placeholder",
    style: str = "clean-cartoon-explainer",
    skipped: bool = False,
) -> dict:
    """Build the image_jobs payload.

    Args:
        cards: The ImageCard objects to create jobs for.
        adapter: Name of the image adapter.
        style: Visual style hint.
        skipped: Whether image generation was skipped.

    Returns:
        Dict suitable for writing to image_jobs.json.
    """
    jobs = []
    for i, card in enumerate(cards):
        status = "skipped" if skipped else "pending"
        jobs.append({
            "job_id": f"image_job_{i + 1:03d}",
            "card_id": card.card_id,
            "title": card.title,
            "prompt": card.image_prompt,
            "visual_metaphor": card.image_prompt[:100] if card.image_prompt else "",
            "source_chunk_ids": card.source_chunk_ids,
            "status": status,
        })

    return {
        "adapter": adapter if not skipped else None,
        "style": style if not skipped else None,
        "job_count": len(jobs),
        "jobs": jobs,
    }


def write_image_jobs(
    cards: Sequence[ImageCard],
    output_dir: Path,
    *,
    adapter: str = "placeholder",
    style: str = "clean-cartoon-explainer",
    skipped: bool = False,
) -> dict:
    """Build image_jobs payload and write it to output_dir/image_jobs.json.

    Args:
        cards: The ImageCard objects.
        output_dir: Directory to write image_jobs.json into.
        adapter: Name of the image adapter.
        style: Visual style hint.
        skipped: Whether images were skipped.

    Returns:
        The image_jobs dict that was written.
    """
    jobs = build_image_jobs(
        cards,
        adapter=adapter,
        style=style,
        skipped=skipped,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "image_jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    return jobs
