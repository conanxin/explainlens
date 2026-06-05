"""Mock LLM provider — simulates future LLM output without API calls.

This provider is designed for testing the LLM adapter interface and
generates structured outputs that feel more "LLM-like" than the
rule-based heuristic, while staying entirely offline.

Important safety constraints:
- No external API calls
- No real API keys read
- No fabricated data or paper conclusions
- Analogies are marked as teaching metaphors
- Every card is linked to real source chunks
"""

from __future__ import annotations

import re
from typing import List

from explainlens.providers.base import ExplainProvider
from explainlens.schemas import (
    ConceptMap,
    ImageCard,
    SourceChunk,
    Storyboard,
    StoryboardPanel,
    TeachingPlan,
    TeachingStep,
)
from explainlens.prompts import TEACHING_STEPS, METAPHOR_CATALOG, build_image_prompt


# ── Mock LLM Templates ────────────────────────────────────────────


def _mock_concept_map(chunks: List[SourceChunk]) -> ConceptMap:
    """Build a mock-LLM-style concept map from chunks.

    This produces output that sounds more like a language model wrote it,
    but is still deterministically built from the input chunks.
    """
    full_text = " ".join(c.text for c in chunks)

    # Extract sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?。！？])\s+', full_text) if len(s.strip()) > 20]

    # --- Core problem: find the first substantive sentence that looks like a problem statement
    _problem_words = [
        "problem", "challenge", "issue", "gap", "question", "limitation",
        "问题", "挑战", "不足", "局限", "瓶颈", "难点",
    ]
    problem_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _problem_words)
    ]
    core_problem = (
        f"The core tension here is: {problem_sents[0]}"
        if problem_sents
        else (f"The central question this content explores: {sentences[0]}"
              if sentences
              else "")
    )

    # --- Key concepts: look for definition patterns or capitalized noun phrases
    _concept_words = [
        "is", "are", "refers to", "means", "defined as", "denotes",
        "concept", "idea", "theory", "framework", "model", "principle",
    ]
    concept_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _concept_words)
    ][:5]
    if not concept_sents:
        concept_sents = sentences[:3] if len(sentences) >= 3 else sentences
    key_concepts = concept_sents[:5]

    # --- Key claims: look for argumentation language
    _claim_words = [
        "argue", "claim", "find", "show", "demonstrate", "conclude",
        "insight", "contribution", "novel", "discover", "prove",
        "我们认为", "发现", "表明", "证明", "创新", "贡献",
    ]
    claim_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _claim_words)
    ][:5]
    if not claim_sents:
        claim_sents = [s for s in sentences[:8] if len(s) > 40][:5]
    key_claims = claim_sents[:5]

    # --- Methods: look for methodology language
    _method_words = [
        "method", "approach", "algorithm", "technique", "procedure",
        "framework", "pipeline", "architecture", "mechanism", "design",
        "propose", "introduce", "present", "develop", "implement",
        "方法", "算法", "框架", "模型", "技术", "架构", "提出",
    ]
    method_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _method_words)
    ][:5]
    if not method_sents:
        method_sents = ["(The mock-LLM provider could not identify explicit method descriptions from this content.)"]
    methods_or_mechanisms = method_sents[:5]

    # --- Evidence: look for results/data language
    _evidence_words = [
        "experiment", "result", "evaluation", "benchmark", "dataset",
        "demonstrate", "show that", "found that", "indicate", "suggest",
        "compared to", "outperforms", "achieves", "evidence", "data",
        "实验", "结果", "评估", "数据", "表明", "显示",
    ]
    evidence_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _evidence_words)
    ][:5]
    if not evidence_sents:
        evidence_sents = ["(The mock-LLM provider did not detect explicit evidence claims — this is a simulation, not a real LLM analysis.)"]
    evidence_or_examples = evidence_sents[:5]

    # --- Limitations: look for hedging/caveat language
    _limit_words = [
        "limitation", "caveat", "however", "although", "despite",
        "future work", "remains", "open question", "not yet", "challenge",
        "局限", "不足", "未来", "但是", "然而", "尚需", "有待",
    ]
    limit_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _limit_words)
    ][:5]
    if not limit_sents:
        limit_sents = [
            "⚠ Teaching metaphor: every explanation has boundaries — "
            "the mock-LLM provider reminds you that this analysis is a simulation "
            "and not a real language model."
        ]
    limitations = limit_sents[:5]

    # --- Why it matters
    _importance_words = [
        "important", "significant", "critical", "crucial", "essential",
        "impact", "implication", "fundamental", "key", "vital",
        "重要", "关键", "根本", "重大", "影响",
    ]
    importance_sents = [
        s for s in sentences
        if any(w.lower() in s.lower() for w in _importance_words)
    ][:3]
    why_it_matters = (
        f"Why this matters: {importance_sents[0]}"
        if importance_sents
        else f"This content matters because it introduces ideas around: "
             f"{', '.join(kc[:60] for kc in key_concepts[:3])}"
             if key_concepts
             else "This content presents ideas worth understanding — "
                  "the mock-LLM provider flags this as significant even without explicit importance cues."
    )

    return ConceptMap(
        core_problem=core_problem,
        key_concepts=key_concepts,
        key_claims=key_claims,
        methods_or_mechanisms=methods_or_mechanisms,
        evidence_or_examples=evidence_or_examples,
        limitations=limitations,
        why_it_matters=why_it_matters,
    )


def _chunk_ids_for_step(chunks: List[SourceChunk], step_index: int) -> List[str]:
    """Assign relevant chunk IDs based on step index."""
    if not chunks:
        return []
    total = len(chunks)
    start = max(0, (step_index * total) // 8)
    end = max(start + 1, ((step_index + 1) * total) // 8)
    return [c.chunk_id for c in chunks[start:end]]


def _mock_teaching_plan(
    chunks: List[SourceChunk], concept_map: ConceptMap
) -> TeachingPlan:
    """Build a mock-LLM-style teaching plan.

    Uses more conversational, narrative language than the rule-based version.
    """
    steps: List[TeachingStep] = []

    # Narrative-style explanations for each step, keyed by step index
    _step_templates = [
        # Step 0: What problem does this address?
        lambda cm: (
            f"You might be wondering: why was this content written? "
            f"Let me walk you through it. "
            f"{cm.core_problem[:400]}"
        ),
        # Step 1: Why does this matter?
        lambda cm: (
            f"Here's the thing — this isn't just an academic curiosity. "
            f"{cm.why_it_matters[:400]}"
        ),
        # Step 2: What's wrong with the old way?
        lambda cm: (
            f"Before we dive into solutions, let's be honest about where the "
            f"old approach breaks down. "
            f"{'; '.join(cm.limitations[:2])[:400] if cm.limitations else 'The status quo has gaps worth addressing.'}"
        ),
        # Step 3: What are the key ideas?
        lambda cm: (
            f"Now let's build a shared vocabulary. The key ideas you need to "
            f"understand are: {'; '.join(cm.key_concepts[:3])[:400]}"
            if cm.key_concepts
            else "Let me introduce the core concepts that serve as building blocks for everything that follows."
        ),
        # Step 4: How does the new approach actually work?
        lambda cm: (
            f"⚠ Teaching metaphor: imagine you're assembling a puzzle — each "
            f"piece represents a part of the mechanism. Here's how it fits together: "
            f"{'; '.join(cm.methods_or_mechanisms[:2])[:400]}"
        ),
        # Step 5: What does the evidence say?
        lambda cm: (
            f"Alright, claims are nice — but where's the proof? "
            f"The evidence points to: "
            f"{'; '.join(cm.evidence_or_examples[:2])[:400]}"
            if cm.evidence_or_examples
            else "⚠ Teaching metaphor: evidence is like a trail of breadcrumbs — "
                 "the mock-LLM provider is showing you the conceptual breadcrumbs "
                 "found in this content."
        ),
        # Step 6: Where does it fall short?
        lambda cm: (
            f"Let's be fair and balanced. No approach is perfect. "
            f"Here's where the idea still fails or needs more work: "
            f"{'; '.join(cm.limitations[:3])[:400]}"
            if cm.limitations
            else "⚠ Teaching metaphor: every map has blank spaces — "
                 "the mock-LLM provider flags these as areas needing further exploration."
        ),
        # Step 7: What's the big picture?
        lambda cm: (
            f"Stepping back for a moment: what changed in our understanding? "
            f"{cm.why_it_matters[:400]}"
        ),
    ]

    for i, step_def in enumerate(TEACHING_STEPS):
        explanation_fn = _step_templates[i] if i < len(_step_templates) else lambda cm: cm.why_it_matters[:400]
        step = TeachingStep(
            step_id=f"step_{i + 1:02d}",
            title=step_def["title"],
            teaching_goal=step_def["goal"],
            source_chunk_ids=_chunk_ids_for_step(chunks, i),
            simple_explanation=explanation_fn(concept_map),
            visual_metaphor="",
            audience_level=step_def["audience"],
            risk_note=step_def["risk"],
        )
        steps.append(step)

    return TeachingPlan(steps=steps)


def _mock_storyboard(
    chunks: List[SourceChunk],
    concept_map: ConceptMap,
    teaching_plan: TeachingPlan,
) -> Storyboard:
    """Build a mock-LLM-style storyboard.

    Uses the same metaphor catalog but with more narrative scene descriptions.
    """
    def _chunk_ids_for_panel(chunks: List[SourceChunk], panel_index: int) -> List[str]:
        if not chunks:
            return []
        total = len(chunks)
        start = max(0, (panel_index * total) // 8)
        end = max(start + 1, ((panel_index + 1) * total) // 8)
        return [c.chunk_id for c in chunks[start:end]]

    panels: List[StoryboardPanel] = []

    for i, (step, metaphor_def) in enumerate(zip(teaching_plan.steps, METAPHOR_CATALOG)):
        source_ids = _chunk_ids_for_panel(chunks, i)

        image_prompt = build_image_prompt(
            metaphor=metaphor_def["metaphor"],
            scene_desc=metaphor_def["scene"],
        )

        # Mock-LLM style: more narrative scene description
        _narrative_prefixes = [
            "Picture this: ",
            "Imagine: ",
            "The scene opens with: ",
            "Visualize this moment: ",
            "In this frame: ",
            "The visual story shows: ",
            "Here's the visual: ",
            "The closing image: ",
        ]
        narrative_scene = (
            f"{_narrative_prefixes[i]}{metaphor_def['scene']}"
            if i < len(_narrative_prefixes)
            else metaphor_def["scene"]
        )

        panel = StoryboardPanel(
            panel_id=f"panel_{i + 1:02d}",
            title=step.title,
            source_chunk_ids=source_ids,
            plain_explanation=step.simple_explanation,
            visual_scene=narrative_scene,
            characters=metaphor_def["characters"],
            composition=metaphor_def["composition"],
            caption=step.title,
            takeaway=step.simple_explanation[:200],
            must_include=metaphor_def["characters"][:],
            must_avoid=[
                "realistic photo style",
                "dark horror style",
                "text or labels in image",
                "photorealistic faces",
            ],
            image_prompt=image_prompt,
            verification_status="pending",
        )
        panels.append(panel)

    return Storyboard(panels=panels)


class MockLLMProvider(ExplainProvider):
    """Mock LLM provider for testing the provider interface.

    Generates structured outputs that feel more "LLM-like" than the
    rule-based heuristic, while remaining entirely offline.

    Key characteristics:
    - No external API calls
    - Conversational, narrative language
    - Teaching metaphors are explicitly marked
    - All cards linked to real source chunks
    - Exactly 8 explainer cards
    """

    name: str = "mock-llm"
    version: str = "mock-llm-v0.1"
    uses_external_api: bool = False

    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """Build a mock-LLM-style concept map from chunks."""
        return _mock_concept_map(chunks)

    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """Build a mock-LLM-style teaching plan."""
        return _mock_teaching_plan(chunks, concept_map)

    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """Build a mock-LLM-style storyboard."""
        return _mock_storyboard(chunks, concept_map, teaching_plan)

    def build_cards(self, storyboard: Storyboard) -> List[ImageCard]:
        """Generate explainer cards from the storyboard.

        Uses the same SVG placeholder + card creation logic as rule-based,
        since card rendering is independent of the analysis backend.
        """
        from explainlens.renderer import create_cards_from_storyboard
        return create_cards_from_storyboard(storyboard)
