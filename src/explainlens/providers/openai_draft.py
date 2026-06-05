"""Disabled OpenAI provider — draft adapter (NOT FUNCTIONAL).

This module exists as a draft skeleton for a future OpenAI API adapter.
It is intentionally disabled and will NOT run any analysis.

IMPORTANT:
- No openai SDK is imported or required.
- No external API calls are made.
- No API keys are read.
- Attempting to use this provider will raise a clear error.

This is a placeholder for Phase 3.x when real external API providers
are implemented.
"""

from __future__ import annotations

from typing import List

from explainlens.providers.base import ExplainProvider
from explainlens.schemas import ConceptMap, SourceChunk, Storyboard, TeachingPlan


class OpenAIDraftProvider(ExplainProvider):
    """Draft OpenAI provider — DISABLED.

    This provider is a draft skeleton for the future OpenAI integration.
    It is NOT functional. Attempting to use it will raise a clear error.

    When implemented (Phase 3.x), this provider will:
    - Call the OpenAI Chat Completions API
    - Use structured JSON mode for concept extraction
    - Require an OPENAI_API_KEY environment variable
    - Require the `openai` Python SDK

    For now, it serves as documentation and a contract placeholder.
    """

    name: str = "openai"
    version: str = "openai-draft-v0.1"
    uses_external_api: bool = True

    _DISABLED_MSG = (
        "Provider 'openai' is currently disabled. "
        "Real external API providers are not enabled in this release.\n"
        "\n"
        "Available providers:\n"
        "  - rule-based  (default, local heuristic)\n"
        "  - mock-llm    (mock LLM, no API calls)\n"
        "\n"
        "The OpenAI provider will be enabled in a future Phase 3.x release. "
        "For more details, see docs/PROVIDERS.md."
    )

    def _raise_disabled(self):
        """Raise a clear error explaining that this provider is disabled."""
        raise RuntimeError(self._DISABLED_MSG)

    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """DISABLED — will raise RuntimeError."""
        self._raise_disabled()
        return ConceptMap()  # Unreachable, but satisfies type checker

    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """DISABLED — will raise RuntimeError."""
        self._raise_disabled()
        return TeachingPlan(steps=[])  # Unreachable

    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """DISABLED — will raise RuntimeError."""
        self._raise_disabled()
        return Storyboard(panels=[])  # Unreachable

    def build_cards(self, storyboard: Storyboard) -> List:
        """DISABLED — will raise RuntimeError."""
        self._raise_disabled()
        return []  # Unreachable
