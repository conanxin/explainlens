"""Provider response contract — structured response from a provider.

Defines the expected response format that any LLM/non-LLM provider
must conform to. This is the "what we expect back" side of the
provider protocol.

parse_provider_response() validates raw provider output against
this contract, rejecting anything that violates safety or
traceability rules.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, ValidationError, field_validator

from explainlens.schemas import SourceChunk


# ── Response sub-models ───────────────────────────────────────────


class ProviderConceptMapResponse(BaseModel):
    """Concept map as returned by the provider."""

    core_problem: str = Field(default="", description="The main problem the content addresses")
    key_concepts: list[str] = Field(default_factory=list, description="Key concepts introduced")
    key_claims: list[str] = Field(default_factory=list, description="Core claims or thesis statements")
    methods_or_mechanisms: list[str] = Field(
        default_factory=list, description="Methods, algorithms, or mechanisms"
    )
    evidence_or_examples: list[str] = Field(
        default_factory=list, description="Evidence, data, or examples cited"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Limitations, caveats, or open questions"
    )
    why_it_matters: str = Field(default="", description="Why this content is significant")


class ProviderCardResponse(BaseModel):
    """A single explainer card as returned by the provider."""

    title: str = Field(..., description="Card title")
    explanation: str = Field(..., description="Plain-language explanation")
    visual_metaphor: str = Field(default="", description="Visual metaphor for this concept")
    visual_scene: str = Field(default="", description="Description of the visual scene")
    takeaway: str = Field(default="", description="Key takeaway")
    source_chunk_ids: list[str] = Field(
        default_factory=list, description="Referenced source chunk IDs"
    )

    @field_validator("source_chunk_ids")
    @classmethod
    def source_chunk_ids_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Each card must have at least one source_chunk_id")
        return v


class ProviderStructuredResponse(BaseModel):
    """Complete structured response from a provider."""

    concept_map: ProviderConceptMapResponse = Field(
        default_factory=ProviderConceptMapResponse, description="Extracted concept map"
    )
    cards: list[ProviderCardResponse] = Field(
        default_factory=list, description="Explainer cards (exactly 8)"
    )
    provider_notes: list[str] = Field(
        default_factory=list, description="Provider notes / disclaimers"
    )

    @field_validator("cards")
    @classmethod
    def cards_count_must_be_eight(cls, v: list[ProviderCardResponse]) -> list[ProviderCardResponse]:
        if len(v) != 8:
            raise ValueError(
                f"Expected exactly 8 cards, got {len(v)}. "
                "Rejecting: card count mismatch violates provider contract."
            )
        return v


# ── Parser / Validator ────────────────────────────────────────────


def parse_provider_response(
    raw: dict,
    chunks: list[SourceChunk],
) -> ProviderStructuredResponse:
    """Parse and validate a raw provider response against the contract.

    This performs:
    1. Pydantic validation of structure
    2. Card count check (exactly 8)
    3. Every card's source_chunk_ids must be non-empty
    4. Every source_chunk_id must exist in the provided chunks

    Args:
        raw: Raw dict from the provider.
        chunks: Original source chunks (for chunk_id validation).

    Returns:
        A validated ProviderStructuredResponse.

    Raises:
        ValidationError: If the response fails any contract check.
        ValueError: If source_chunk_ids reference unknown chunks.
    """
    try:
        response = ProviderStructuredResponse(**raw)
    except ValidationError:
        raise  # Re-raise with full pydantic detail

    # --- Chunk ID cross-validation ---
    known_ids = {c.chunk_id for c in chunks}
    for i, card in enumerate(response.cards):
        unknown = [cid for cid in card.source_chunk_ids if cid not in known_ids]
        if unknown:
            raise ValueError(
                f"Card {i+1} ({card.title!r}) references unknown source_chunk_ids: "
                f"{unknown}. Known chunk IDs: {sorted(known_ids)}. "
                "Rejecting: source traceability is broken."
            )

    return response
