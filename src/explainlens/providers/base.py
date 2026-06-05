"""Abstract provider interface for ExplainLens analysis pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from explainlens.schemas import ConceptMap, SourceChunk, Storyboard, TeachingPlan


class ExplainProvider(ABC):
    """Abstract base class for all ExplainLens analysis providers.

    A provider encapsulates the core analysis pipeline:
        chunks -> concept_map -> teaching_plan -> storyboard

    Subclasses implement each step, allowing different backends
    (rule-based heuristic, LLM, mock, etc.) while keeping the
    same interface.
    """

    name: str = "base"
    version: str = "base-v0.1"
    uses_external_api: bool = False

    @abstractmethod
    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """Analyze source chunks and extract structured concepts.

        Args:
            chunks: List of source chunks from the document.

        Returns:
            A ConceptMap with extracted structured information.
        """
        ...

    @abstractmethod
    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """Generate an 8-step teaching plan from the concept map.

        Args:
            chunks: Source document chunks.
            concept_map: Extracted concept map.

        Returns:
            A TeachingPlan with exactly 8 steps.
        """
        ...

    @abstractmethod
    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """Generate a storyboard with 8 cartoon panels.

        Args:
            chunks: Source document chunks.
            concept_map: The concept map.
            teaching_plan: The 8-step teaching plan.

        Returns:
            A Storyboard with exactly 8 panels.
        """
        ...

    @abstractmethod
    def build_cards(
        self,
        storyboard: Storyboard,
    ) -> List:
        """Generate explainer cards from the storyboard.

        Args:
            storyboard: The storyboard with panels.

        Returns:
            A list of ImageCard objects.
        """
        ...
