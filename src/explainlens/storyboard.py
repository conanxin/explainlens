"""Storyboard generator — creates cartoon panels with visual metaphors."""

from __future__ import annotations

from typing import List

from explainlens.schemas import (
    ConceptMap,
    SourceChunk,
    Storyboard,
    StoryboardPanel,
    TeachingPlan,
    TeachingStep,
)
from explainlens.prompts import METAPHOR_CATALOG, build_image_prompt


def _chunk_ids_for_panel(chunks: List[SourceChunk], panel_index: int) -> List[str]:
    """Assign chunk IDs to a panel based on its index."""
    if not chunks:
        return []
    total = len(chunks)
    start = max(0, (panel_index * total) // 8)
    end = max(start + 1, ((panel_index + 1) * total) // 8)
    return [c.chunk_id for c in chunks[start:end]]


def _get_source_excerpt(chunks: List[SourceChunk], panel_index: int) -> str:
    """Get a relevant source excerpt for the panel."""
    if not chunks:
        return ""
    total = len(chunks)
    start = max(0, (panel_index * total) // 8)
    end = max(start + 1, ((panel_index + 1) * total) // 8)
    excerpts = [c.text[:200] + ("..." if len(c.text) > 200 else "") for c in chunks[start:end]]
    return " ".join(excerpts)[:500]


def create_storyboard(
    teaching_plan: TeachingPlan,
    concept_map: ConceptMap,
    chunks: List[SourceChunk],
) -> Storyboard:
    """Generate a storyboard with 8 cartoon panels from the teaching plan.

    Args:
        teaching_plan: The 8-step teaching plan.
        concept_map: The concept map.
        chunks: Source document chunks.

    Returns:
        A Storyboard with exactly 8 panels.
    """
    panels: List[StoryboardPanel] = []

    for i, (step, metaphor_def) in enumerate(zip(teaching_plan.steps, METAPHOR_CATALOG)):
        source_ids = _chunk_ids_for_panel(chunks, i)
        source_excerpt = _get_source_excerpt(chunks, i)

        # Build must_include and must_avoid based on step
        must_include = metaphor_def["characters"][:]
        must_avoid = [
            "realistic photo style",
            "dark horror style",
            "text or labels in image",
            "photorealistic faces",
        ]

        # Build image prompt
        image_prompt = build_image_prompt(
            metaphor=metaphor_def["metaphor"],
            scene_desc=metaphor_def["scene"],
        )

        panel = StoryboardPanel(
            panel_id=f"panel_{i + 1:02d}",
            title=step.title,
            source_chunk_ids=source_ids,
            plain_explanation=step.simple_explanation,
            visual_scene=metaphor_def["scene"],
            characters=metaphor_def["characters"],
            composition=metaphor_def["composition"],
            caption=step.title,
            takeaway=step.simple_explanation[:200],
            must_include=must_include,
            must_avoid=must_avoid,
            image_prompt=image_prompt,
            verification_status="pending",
        )
        panels.append(panel)

    return Storyboard(panels=panels)
