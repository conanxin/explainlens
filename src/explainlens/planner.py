"""Teaching plan generator — creates 8-step educational path from concept map."""

from __future__ import annotations

from typing import List

from explainlens.schemas import ConceptMap, SourceChunk, TeachingPlan, TeachingStep
from explainlens.prompts import TEACHING_STEPS


def _chunk_ids_for_step(chunks: List[SourceChunk], step_index: int) -> List[str]:
    """Assign relevant chunk IDs based on step index and chunk count."""
    if not chunks:
        return []
    total = len(chunks)
    # Distribute chunks roughly evenly across 8 steps
    start = max(0, (step_index * total) // 8)
    end = max(start + 1, ((step_index + 1) * total) // 8)
    return [c.chunk_id for c in chunks[start:end]]


def _build_simple_explanation(step_index: int, concept_map: ConceptMap, chunks: List[SourceChunk]) -> str:
    """Build a simple explanation for the step using heuristic extraction."""
    # Assign relevant chunks
    if not chunks:
        return "No source content available for this step."

    total = len(chunks)
    start = max(0, (step_index * total) // 8)
    end = max(start + 1, ((step_index + 1) * total) // 8)
    relevant = chunks[start:end]

    if step_index == 0:
        return f"本文讨论的核心问题是：{concept_map.core_problem[:300]}"
    elif step_index == 1:
        return f"这个问题之所以重要，是因为：{concept_map.why_it_matters[:300]}"
    elif step_index == 2:
        return f"在现有方法中，存在以下不足和局限：{'；'.join(concept_map.limitations[:2])[:300]}"
    elif step_index == 3:
        concepts = concept_map.key_concepts[:3]
        return f"关键概念包括：{'；'.join(concepts)[:300]}" if concepts else "本文引入的核心概念如下：" + (relevant[0].text[:200] if relevant else "")
    elif step_index == 4:
        methods = concept_map.methods_or_mechanisms[:2]
        return f"新方法/机制的核心思路是：{'；'.join(methods)[:300]}"
    elif step_index == 5:
        evidence = concept_map.evidence_or_examples[:2]
        return f"支持这些结论的证据包括：{'；'.join(evidence)[:300]}"
    elif step_index == 6:
        limits = concept_map.limitations[:3]
        return f"需要注意的局限和风险：{'；'.join(limits)[:300]}" if limits else "当前分析未检测到明确的局限性声明，需要人工审查。"
    elif step_index == 7:
        return f"总结：{concept_map.why_it_matters[:400]}"
    return relevant[0].text[:300] if relevant else ""


def create_teaching_plan(concept_map: ConceptMap, chunks: List[SourceChunk]) -> TeachingPlan:
    """Generate an 8-step teaching plan from the concept map and source chunks.

    Args:
        concept_map: Extracted concept map from the analyzer.
        chunks: Source document chunks.

    Returns:
        A TeachingPlan with exactly 8 steps.
    """
    steps: List[TeachingStep] = []

    for i, step_def in enumerate(TEACHING_STEPS):
        step = TeachingStep(
            step_id=f"step_{i + 1:02d}",
            title=step_def["title"],
            teaching_goal=step_def["goal"],
            source_chunk_ids=_chunk_ids_for_step(chunks, i),
            simple_explanation=_build_simple_explanation(i, concept_map, chunks),
            visual_metaphor="",  # Filled by storyboard
            audience_level=step_def["audience"],
            risk_note=step_def["risk"],
        )
        steps.append(step)

    return TeachingPlan(steps=steps)
