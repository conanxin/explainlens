"""Local HTTP provider — loopback-only HTTP client for local models.

This provider calls localhost-only HTTP endpoints (Ollama, LM Studio,
llama.cpp server, or OpenAI-compatible endpoints) to generate
explanations from local models.

Safety:
- ONLY loopback endpoints allowed (localhost, 127.0.0.1, ::1)
- NO remote HTTP (no https://, no LAN addresses)
- NO API keys are read or sent
- NO Authorization headers are set
- Network calls require explicit opt-in (allow_network=True)
- Default behavior: fail closed

Provider metadata:
  name    = local-http
  version = local-http-v0.1
  status  = experimental
  uses_external_api = false (loopback only, not "external")
"""

from __future__ import annotations

from typing import List, Optional

from explainlens.providers.base import ExplainProvider
from explainlens.providers.local_http_transport import (
    ProtocolType,
    build_local_http_payload,
    call_local_http_provider,
    extract_structured_response_from_chat_json,
)
from explainlens.providers.prompt_contract import build_prompt_pack
from explainlens.providers.response_contract import parse_provider_response
from explainlens.schemas import (
    ConceptMap,
    ImageCard,
    SourceChunk,
    Storyboard,
    StoryboardPanel,
    TeachingPlan,
    TeachingStep,
)

# ── SVG placeholders for 8 cards ─────────────────────────────

_SVG_TEMPLATES = [
    # Card 1: Overview / Big Picture
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#E8F5E9" rx="8"/>
  <circle cx="200" cy="110" r="50" fill="#43A047" opacity="0.3"/>
  <circle cx="200" cy="110" r="30" fill="#43A047" opacity="0.6"/>
  <text x="200" y="200" text-anchor="middle" font-size="14" fill="#2E7D32">Big Picture</text>
  <text x="200" y="240" text-anchor="middle" font-size="12" fill="#555">Start here to see the full story</text>
</svg>""",
    # Card 2: Core Problem
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#FFF3E0" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">?</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#E65100">Core Problem</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">The central question to explore</text>
</svg>""",
    # Card 3: Key Insight
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#E3F2FD" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">💡</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#1565C0">Key Insight</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">The essential discovery</text>
</svg>""",
    # Card 4: How It Works
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#F3E5F5" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">⚙</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#6A1B9A">How It Works</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">The mechanism explained</text>
</svg>""",
    # Card 5: Evidence Check
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#FFFDE7" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">📊</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#F9A825">Evidence Check</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">What the data actually shows</text>
</svg>""",
    # Card 6: Why It Matters
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#E8EAF6" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">🌟</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#283593">Why It Matters</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">The broader significance</text>
</svg>""",
    # Card 7: Limits & Caveats
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#FCE4EC" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">⚠</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#C62828">Limits &amp; Caveats</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">What we don't know yet</text>
</svg>""",
    # Card 8: Next Steps
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#E0F2F1" rx="8"/>
  <text x="200" y="80" text-anchor="middle" font-size="48">🧭</text>
  <text x="200" y="170" text-anchor="middle" font-size="14" fill="#00695C">Next Steps</text>
  <text x="200" y="220" text-anchor="middle" font-size="12" fill="#555">Your mental compass is ready</text>
</svg>""",
]

_CARD_TITLES_SHORT = [
    "What's This About?",
    "The Core Problem",
    "Key Insight",
    "How It Works",
    "Evidence Check",
    "Why It Matters",
    "Limits & Caveats",
    "What This Means for You",
]

_VISUAL_METAPHORS_SHORT = [
    "Magnifying glass on a page",
    "Maze with one lit path",
    "Detective's corkboard",
    "Blueprint unrolling",
    "Balanced scale with evidence",
    "Lighthouse in fog",
    "Caution sign at bridge",
    "Compass pointing to door",
]

_VISUAL_SCENES_SHORT = [
    "Open book with glowing annotations above it.",
    "Overhead maze with one luminous path to a question mark.",
    "Corkboard with photos, red string, and sticky notes.",
    "Blueprint table with technical drawing and callouts.",
    "Justice scale with evidence blocks on each side.",
    "Lighthouse beam cutting through mist to distant shore.",
    "Bridge with caution sign; a person pauses to read it.",
    "Open door with compass pointing toward it.",
]

_TAKEAWAYS_SHORT = [
    "Start with the big picture.",
    "Every complex topic has a central question.",
    "New ideas connect to what you already know.",
    "Understanding the mechanism makes results stick.",
    "Evidence gives weight to claims.",
    "This has real-world relevance beyond the document.",
    "Knowing the limits is part of understanding.",
    "Your mental map is ready — next step is yours.",
]


# ── Provider ───────────────────────────────────────────────

class LocalHttpProvider(ExplainProvider):
    """Local HTTP provider for loopback-only model endpoints.

    Calls localhost-only HTTP endpoints to generate explanations.
    Supports fixture (offline), ollama-chat, and openai-compatible-chat
    protocols.

    Safety:
    - Requires explicit opt-in (allow_network=True) for any HTTP call.
    - Rejects non-loopback endpoints.
    - Does not read or send API keys.

    Attributes:
        endpoint: HTTP endpoint URL (e.g., "http://localhost:11434/api/chat").
        model: Model name to use (e.g., "llama3.2").
        protocol: Protocol type ("fixture", "ollama-chat", "openai-compatible-chat").
        allow_network: Must be True for HTTP calls to proceed.
        timeout_seconds: HTTP timeout (default 30).
    """

    name: str = "local-http"
    version: str = "local-http-v0.1"
    uses_external_api: bool = False  # loopback only, not "external"

    # ── Configuration (set by CLI before use) ─────────────

    endpoint: Optional[str] = None
    model: str = "local-model"
    protocol: ProtocolType = "fixture"
    allow_network: bool = False
    timeout_seconds: float = 30.0

    # ── Concept Map ───────────────────────────────────────

    def build_concept_map(self, chunks: List[SourceChunk]) -> ConceptMap:
        """Build a concept map via local HTTP transport."""
        prompt_pack = build_prompt_pack(chunks)
        raw = call_local_http_provider(
            prompt_pack=prompt_pack,
            endpoint=self.endpoint or "",
            model=self.model,
            protocol=self.protocol,
            timeout_seconds=self.timeout_seconds,
            allow_network=self.allow_network,
        )
        response = parse_provider_response(raw, chunks)

        cm = response.concept_map
        return ConceptMap(
            core_problem=cm.core_problem,
            key_concepts=cm.key_concepts,
            key_claims=cm.key_claims,
            methods_or_mechanisms=cm.methods_or_mechanisms,
            evidence_or_examples=cm.evidence_or_examples,
            limitations=cm.limitations,
            why_it_matters=cm.why_it_matters,
        )

    # ── Teaching Plan ────────────────────────────────────

    def build_teaching_plan(
        self, chunks: List[SourceChunk], concept_map: ConceptMap
    ) -> TeachingPlan:
        """Build an 8-step teaching plan from the concept map."""
        step_titles = [
            "Overview: Setting the Stage",
            "Identifying the Core Problem",
            "Unpacking the Key Insight",
            "How the Mechanism Works",
            "Examining the Evidence",
            "Why This Matters",
            "Limitations and Open Questions",
            "Summary and Next Steps",
        ]

        steps: list[TeachingStep] = []
        for i in range(8):
            chunk_idx = min(i, len(chunks) - 1)
            steps.append(
                TeachingStep(
                    step_id=f"step_{i+1:02d}",
                    title=step_titles[i],
                    teaching_goal=(
                        f"Build understanding of {concept_map.key_concepts[i] if i < len(concept_map.key_concepts) else 'the topic'}"
                    ),
                    source_chunk_ids=[chunks[chunk_idx].chunk_id],
                    simple_explanation=(
                        f"This step explores {'the big picture' if i == 0 else 'a specific aspect'} of the topic."
                    ),
                    visual_metaphor=_VISUAL_METAPHORS_SHORT[i],
                    audience_level="general",
                    risk_note=(
                        "Note: This is a local model output — verify against the original source."
                    ),
                )
            )

        return TeachingPlan(steps=steps)

    # ── Storyboard ──────────────────────────────────────

    def build_storyboard(
        self,
        chunks: List[SourceChunk],
        concept_map: ConceptMap,
        teaching_plan: TeachingPlan,
    ) -> Storyboard:
        """Generate a storyboard with 8 panels."""
        panels: list[StoryboardPanel] = []
        for i in range(8):
            chunk_idx = min(i, len(chunks) - 1)
            panels.append(
                StoryboardPanel(
                    panel_id=f"panel_{i+1:02d}",
                    title=_CARD_TITLES_SHORT[i],
                    source_chunk_ids=[chunks[chunk_idx].chunk_id],
                    plain_explanation=(
                        teaching_plan.steps[i].simple_explanation
                        if i < len(teaching_plan.steps)
                        else f"Panel {i+1} of the storyboard."
                    ),
                    visual_scene=_VISUAL_SCENES_SHORT[i],
                    characters=["Reader", "Explainer"],
                    composition="Center composition with balanced elements",
                    caption=f"Figure {i+1}: {_CARD_TITLES_SHORT[i]}",
                    takeaway=_TAKEAWAYS_SHORT[i],
                    must_include=["title", "visual element", "source citation"],
                    must_avoid=["text-heavy design", "unrelated imagery"],
                    image_prompt=(
                        f"A clean, modern illustration of {_CARD_TITLES_SHORT[i].lower()}. "
                        f"Style: flat vector art with warm colors, suitable for educational content."
                    ),
                    verification_status="pending",
                )
            )

        return Storyboard(panels=panels)

    # ── Cards ───────────────────────────────────────────

    def build_cards(self, storyboard: Storyboard) -> List[ImageCard]:
        """Generate explainer cards from the storyboard."""
        cards: list[ImageCard] = []
        for i, panel in enumerate(storyboard.panels):
            cards.append(
                ImageCard(
                    card_id=f"card_{i+1:02d}",
                    title=panel.title,
                    explanation=(
                        f"{panel.plain_explanation} "
                        f"Takeaway: {panel.takeaway}"
                    ),
                    image_placeholder_svg=_SVG_TEMPLATES[i],
                    image_prompt=panel.image_prompt,
                    takeaway=panel.takeaway,
                    source_chunk_ids=panel.source_chunk_ids,
                    source_excerpt="(excerpt from source — see Source Appendix below)",
                    review_status="pending",
                )
            )

        return cards

    # ── Network manifest helper ─────────────────────────

    def get_network_manifest(self) -> dict:
        """Return network disclosure block for provider_manifest.json.

        Returns:
            Dict with network usage information.
        """
        uses_local_http = self.protocol != "fixture" and self.allow_network

        return {
            "uses_local_http": uses_local_http,
            "allows_remote_http": False,
            "endpoint": self.endpoint if uses_local_http else None,
            "protocol": self.protocol,
            "timeout_seconds": self.timeout_seconds if uses_local_http else 30,
        }
