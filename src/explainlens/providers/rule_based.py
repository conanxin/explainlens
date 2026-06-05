"""Rule-based provider — wraps existing heuristic analysis pipeline.

This provider delegates all analysis work to the existing modules
(analyzer, planner, storyboard, renderer) and is the default backend.
"""

from __future__ import annotations

from typing import List

from explainlens.providers.base import ExplainProvider
from explainlens.schemas import ConceptMap, SourceChunk, Storyboard, TeachingPlan
from explainlens.analyzer import analyze
from explainlens.planner import create_teaching_plan
from explainlens.storyboard import create_storyboard
from explainlens.renderer import create_cards_from_storyboard


class RuleBasedProvider(ExplainProvider):
    """Default rule-based heuristic analysis provider.

    Uses keyword matching and fixed templates — no external API calls.
    This is the same pipeline used in Phase 1 and Phase 2.
    """

    name: str = "rule-based"
    version: str = "rule-based-v0.1"
    uses_external_api: bool = False

    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """Delegate to the existing heuristic analyzer."""
        return analyze(chunks)

    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """Delegate to the existing teaching plan generator."""
        return create_teaching_plan(concept_map, chunks)

    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """Delegate to the existing storyboard generator."""
        return create_storyboard(teaching_plan, concept_map, chunks)

    def build_cards(
        self,
        storyboard: Storyboard,
    ) -> List:
        """Delegate to the existing card renderer."""
        return create_cards_from_storyboard(storyboard)
