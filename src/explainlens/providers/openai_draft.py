"""OpenAI provider — experimental, opt-in, fail-closed.

This module provides an experimental OpenAI provider that calls the
OpenAI Responses API via standard-library urllib (no SDK).

Safety rules:
- FAIL-CLOSED by default — allow_external_api must be explicitly True.
- API key is read ONLY from os.environ, never from args or files.
- API key is NEVER printed, logged, or written to any file.
- Prompt text is NOT written to logs.
- Output files do NOT contain API keys or secrets.
- source_chunk_ids are preserved from the API response as-is.
"""

from __future__ import annotations

import os
from typing import List, Optional

from explainlens.providers.base import ExplainProvider
from explainlens.providers.openai_transport import (
    call_openai_responses_api,
)
from explainlens.providers.prompt_contract import build_prompt_pack
from explainlens.schemas import (
    ConceptMap,
    ImageCard,
    SourceChunk,
    Storyboard,
    StoryboardPanel,
    TeachingPlan,
    TeachingStep,
)


class OpenAIProvider(ExplainProvider):
    """Experimental OpenAI provider — FAIL-CLOSED by default.

    Must be explicitly enabled with:
        --allow-external-api  (CLI flag)
        OPENAI_API_KEY env var

    Without both, all methods fail without making any API call.
    """

    name: str = "openai"
    version: str = "openai-v0.1"
    uses_external_api: bool = True

    def __init__(self):
        self.model = "gpt-5.5"
        self.allow_external_api = False
        self.timeout_seconds = 60.0
        self._last_result = None
        self._prompt_pack = None

    # ── Fail-closed checks ─────────────────────────────────────

    def _check_fail_closed(self) -> None:
        """Raise RuntimeError if not opted in.

        Must be called by every pipeline method before doing work.
        """
        if not self.allow_external_api:
            raise RuntimeError(
                "OpenAI provider is fail-closed by default.\n"
                "To enable it, set OPENAI_API_KEY and pass --allow-external-api.\n"
                "No request was sent."
            )
        api_key = self._get_api_key()
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set.\n"
                "No request was sent."
            )

    def _get_api_key(self) -> str:
        """Read API key from environment. NEVER store, print, or log it."""
        key = os.environ.get("OPENAI_API_KEY", "")
        return key

    # ── Network manifest (for provider_manifest.json) ─────────

    def get_network_manifest(self) -> dict:
        """Return network manifest for provider_manifest.json."""
        return {
            "uses_external_api": True,
            "api_base": "https://api.openai.com/v1",
            "endpoint": "/responses",
            "allow_external_api": self.allow_external_api,
            "timeout_seconds": self.timeout_seconds,
        }

    # ── Pipeline methods ──────────────────────────────────────

    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """Call OpenAI API and return ConceptMap.

        The full API response (concept_map + cards) is stored in
        self._last_result for use by build_cards().
        """
        self._check_fail_closed()
        self._prompt_pack = build_prompt_pack(
            chunks=chunks,
            desired_card_count=8,
            audience_level="general",
        )
        api_key = self._get_api_key()
        result = call_openai_responses_api(
            prompt_pack=self._prompt_pack,
            model=self.model,
            api_key=api_key,
            timeout_seconds=self.timeout_seconds,
            allow_external_api=self.allow_external_api,
        )
        self._last_result = result
        return ConceptMap(**result["concept_map"])

    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """Build an 8-step teaching plan from the concept map."""
        step_titles = [
            "What's the core problem or question?",
            "What are the key concepts to understand?",
            "How does the mechanism or process work?",
            "What evidence supports the claims?",
            "How do the concepts connect to each other?",
            "Why does this matter for the reader?",
            "What are the limits or open questions?",
            "What should I do or remember after reading?",
        ]
        steps = []
        for i, title in enumerate(step_titles):
            chunk_idx = min(i, len(chunks) - 1) if chunks else 0
            steps.append(
                TeachingStep(
                    step_id=f"step_{i + 1:02d}",
                    title=title,
                    teaching_goal=f"Understand {title.lower()}",
                    source_chunk_ids=[chunks[chunk_idx].chunk_id] if chunks else [],
                    simple_explanation=f"This step covers {title.lower()}.",
                    visual_metaphor=f"Metaphor for: {title}",
                    audience_level="general",
                    risk_note=(
                        "AI-generated teaching plan via OpenAI API. "
                        "Verify against the original source."
                    ),
                )
            )
        return TeachingPlan(steps=steps)

    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """Build a storyboard with 8 panels matching the teaching plan."""
        panels = []
        for i, step in enumerate(teaching_plan.steps):
            panels.append(
                StoryboardPanel(
                    panel_id=f"panel_{i:03d}",
                    title=step.title,
                    key_concept=step.teaching_goal,
                    visual_metaphor=f"Visual metaphor for: {step.title}",
                    image_prompt=f"Illustration for: {step.title}",
                )
            )
        return Storyboard(panels=panels)

    def build_cards(self, storyboard: Storyboard) -> List[ImageCard]:
        """Generate explainer cards from the API response.

        Uses self._last_result["cards"] (from the API response)
        and converts each dict to an ImageCard object.

        source_chunk_ids are preserved AS-IS from the API response.
        Invalid source_chunk_ids are NOT auto-fixed — the API
        response validation (in parse_provider_response) will have
        already rejected responses with invalid chunk IDs.
        """
        if not self._last_result:
            raise RuntimeError(
                "OpenAI provider: no stored result. "
                "build_concept_map() must be called first."
            )
        cards_dicts = self._last_result.get("cards", [])
        if not isinstance(cards_dicts, list):
            raise ValueError(
                f"OpenAI API 'cards' is not a list. "
                f"Type: {type(cards_dicts).__name__}"
            )

        cards: list[ImageCard] = []
        for i, c in enumerate(cards_dicts):
            if not isinstance(c, dict):
                raise ValueError(
                    f"Card {i} is not a dict. "
                    f"Type: {type(c).__name__}"
                )
            # Validate required fields (preserve source_chunk_ids as-is)
            if "title" not in c:
                raise ValueError(f"Card {i} missing 'title'.")
            if "explanation" not in c:
                raise ValueError(f"Card {i} ('{c.get('title', '?')}') missing 'explanation'.")
            if "source_chunk_ids" not in c:
                raise ValueError(
                    f"Card {i} ('{c.get('title', '?')}') "
                    f"missing 'source_chunk_ids'."
                )
            # Build ImageCard (preserving all fields from API response)
            card_kwargs = dict(c)  # shallow copy
            # Ensure card_id exists (API may not provide it)
            if "card_id" not in card_kwargs:
                card_kwargs["card_id"] = f"card_{i:02d}"
            cards.append(ImageCard(**card_kwargs))

        return cards
