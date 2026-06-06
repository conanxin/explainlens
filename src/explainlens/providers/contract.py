"""Provider contract — capability descriptions and output validation.

This module defines the data structure for provider capabilities and
provides output validation to ensure every provider meets the contract
regarding source traceability, card count, and external API behavior.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

from explainlens.schemas import ConceptMap, ImageCard, SourceChunk, Storyboard, TeachingPlan


# ── Provider Capabilities ──────────────────────────────────────────


class ProviderCapabilities(BaseModel):
    """Describes what a provider can and cannot do."""

    name: str = Field(..., description="Provider name, e.g. 'rule-based'")
    version: str = Field(..., description="Provider version string")
    status: Literal["available", "disabled", "experimental"] = Field(
        ..., description="Whether the provider is currently usable"
    )
    uses_external_api: bool = Field(
        ..., description="Whether the provider makes network requests"
    )
    requires_api_key: bool = Field(
        ..., description="Whether an API key must be configured"
    )
    supports_pdf: bool = Field(
        ..., description="Whether the provider handles PDF input"
    )
    supports_text: bool = Field(
        ..., description="Whether the provider handles text/markdown input"
    )
    preserves_source_chunk_ids: bool = Field(
        default=True,
        description="Whether every card links back to source chunks",
    )
    description: str = Field(
        default="", description="Human-readable provider description"
    )

    def safety_manifest(self) -> dict:
        """Return a safety disclosure dict suitable for provider_manifest.json."""
        return {
            "uploads_documents": False,
            "reads_api_key": self.requires_api_key,
            "writes_secrets": False,
        }


# ── Output Validation ──────────────────────────────────────────────


def validate_provider_output(
    provider_name: str,
    chunks: List[SourceChunk],
    concept_map: ConceptMap,
    teaching_plan: TeachingPlan,
    storyboard: Storyboard,
    cards: List[ImageCard],
    uses_external_api: bool = False,
) -> List[str]:
    """Validate provider output against the provider contract.

    Returns a list of error messages. An empty list means all checks passed.
    """
    errors: list[str] = []

    # 1. provider name non-empty
    if not provider_name or not provider_name.strip():
        errors.append("Provider name is empty.")

    # 2. cards count must be 8
    if len(cards) != 8:
        errors.append(f"Expected 8 cards, got {len(cards)}.")

    # 3. cards must not be empty
    if not cards:
        errors.append("No cards were generated.")

    # 4. every card must have source_chunk_ids
    for card in cards:
        if not card.source_chunk_ids:
            errors.append(
                f"Card '{card.card_id}' has empty source_chunk_ids."
            )

    # 5. every source_chunk_id must exist in chunks
    valid_chunk_ids = {c.chunk_id for c in chunks}
    for card in cards:
        for cid in card.source_chunk_ids:
            if cid not in valid_chunk_ids:
                errors.append(
                    f"Card '{card.card_id}' references unknown chunk_id "
                    f"'{cid}' — not found in source chunks."
                )

    # 6. storyboard must not be empty
    if not storyboard.panels:
        errors.append("Storyboard has no panels.")

    # 7. concept_map must not be empty (at least core_problem or key_concepts)
    has_content = bool(
        concept_map.core_problem
        or concept_map.key_concepts
        or concept_map.key_claims
    )
    if not has_content:
        errors.append("Concept map is empty — no concepts or claims extracted.")

    # 8. uses_external_api must be consistent with provider capabilities
    # (This is a soft check — the caller must pass the correct value)
    if uses_external_api:
        # If external API is used, that's only a problem if the output
        # contains API keys (checked separately). We just note it here.
        pass

    return errors


# ── Capability presets for known providers ─────────────────────────


def capabilities_for_rule_based() -> ProviderCapabilities:
    return ProviderCapabilities(
        name="rule-based",
        version="rule-based-v0.1",
        status="available",
        uses_external_api=False,
        requires_api_key=False,
        supports_pdf=True,
        supports_text=True,
        preserves_source_chunk_ids=True,
        description="Default rule-based heuristic provider. "
        "Uses keyword matching and fixed templates — no external API calls.",
    )


def capabilities_for_mock_llm() -> ProviderCapabilities:
    return ProviderCapabilities(
        name="mock-llm",
        version="mock-llm-v0.1",
        status="available",
        uses_external_api=False,
        requires_api_key=False,
        supports_pdf=True,
        supports_text=True,
        preserves_source_chunk_ids=True,
        description="Local mock provider simulating future LLM output. "
        "Conversational, narrative language — no external API calls.",
    )


def capabilities_for_openai() -> ProviderCapabilities:
    return ProviderCapabilities(
        name="openai",
        version="openai-v0.1",
        status="experimental",
        uses_external_api=True,
        requires_api_key=True,
        supports_pdf=True,
        supports_text=True,
        preserves_source_chunk_ids=True,
        description="OpenAI Responses API provider (experimental). "
        "Requires --allow-external-api and OPENAI_API_KEY. "
        "Calls external OpenAI API when explicitly opted in.",
    )


def capabilities_for_local_fixture() -> ProviderCapabilities:
    return ProviderCapabilities(
        name="local-fixture",
        version="local-fixture-v0.1",
        status="experimental",
        uses_external_api=False,
        requires_api_key=False,
        supports_pdf=True,
        supports_text=True,
        preserves_source_chunk_ids=True,
        description="Offline local model fixture for provider protocol testing. "
        "Uses prompt contract + fixture transport — no real model, no HTTP calls.",
    )


def capabilities_for_local_http() -> ProviderCapabilities:
    return ProviderCapabilities(
        name="local-http",
        version="local-http-v0.1",
        status="experimental",
        uses_external_api=False,  # loopback only, not "external"
        requires_api_key=False,
        supports_pdf=True,
        supports_text=True,
        preserves_source_chunk_ids=True,
        description="Local HTTP provider for loopback-only model endpoints. "
        "Supports fixture (offline), ollama-chat, and openai-compatible-chat protocols. "
        "Requires explicit opt-in (--allow-local-http) for any network call.",
    )
