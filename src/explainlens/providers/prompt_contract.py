"""Provider prompt contract — structured prompt pack for LLM providers.

Converts raw SourceChunks into a structured ProviderPromptPack that
a real LLM provider would send as part of its message payload.

This is the "what we send" side of the provider protocol.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

from explainlens.schemas import SourceChunk

# ── Prompt Chunk (source chunk adapted for provider prompts) ──────


class ProviderPromptChunk(BaseModel):
    """A source chunk adapted for inclusion in a provider prompt.

    Mirrors SourceChunk but strips fields irrelevant to the LLM
    (like character offsets) and adds page context where available.
    """

    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. 'chunk_001'")
    page_start: int | None = Field(default=None, description="First page this chunk spans (PDF)")
    page_end: int | None = Field(default=None, description="Last page this chunk spans (PDF)")
    text: str = Field(..., description="The chunk text content")


# ── Prompt Pack (the full structured prompt) ──────────────────────


class ProviderPromptPack(BaseModel):
    """Structured prompt pack sent to a provider.

    Encodes the task, source material, output expectations,
    and safety rules into a single typed object.
    """

    task: Literal["explain_complex_content"] = "explain_complex_content"
    audience_level: str = Field(default="general", description="Target audience level")
    desired_card_count: int = Field(default=8, description="Desired number of explainer cards")
    source_type: str = Field(default="txt", description="Source type: txt, md, or pdf")
    source_chunks: list[ProviderPromptChunk] = Field(
        default_factory=list, description="Source chunks to analyze"
    )
    output_contract: dict = Field(
        default_factory=dict,
        description="Expected output JSON structure the provider must return",
    )
    safety_rules: list[str] = Field(
        default_factory=list,
        description="Safety rules the provider must follow",
    )


# ── Output contract (what the LLM must return) ────────────────────


def _default_output_contract() -> dict:
    """Return the output contract that describes the expected JSON structure.

    This is what a real LLM provider would be instructed to follow.
    """
    return {
        "cards": {
            "count": 8,
            "required_fields": [
                "title",
                "explanation",
                "visual_metaphor",
                "visual_scene",
                "takeaway",
                "source_chunk_ids",
            ],
        },
        "concept_map": {
            "required_fields": [
                "core_problem",
                "key_concepts",
                "key_claims",
                "methods_or_mechanisms",
                "evidence_or_examples",
                "limitations",
                "why_it_matters",
            ],
        },
        "source_traceability": "Every card MUST include source_chunk_ids referencing chunks from the prompt.",
    }


# ── Safety rules (must be embedded in every prompt) ───────────────


def _default_safety_rules() -> list[str]:
    """Return the safety rules that accompany every prompt.

    These rules protect the user and ensure output integrity.
    """
    return [
        "preserve source_chunk_ids from the provided chunks",
        "do not invent unsupported claims",
        "mark metaphors as metaphors",
        "do not include API keys or secrets",
        "return exactly 8 cards",
    ]


# ── Builder ───────────────────────────────────────────────────────


def build_prompt_pack(
    chunks: List[SourceChunk],
    desired_card_count: int = 8,
    audience_level: str = "general",
) -> ProviderPromptPack:
    """Build a structured prompt pack from source chunks.

    Args:
        chunks: Source document chunks (from chunker.chunk_text).
        desired_card_count: How many cards to request (default 8).
        audience_level: Target audience level (e.g. "general", "expert").

    Returns:
        A ProviderPromptPack ready for delivery to a provider.
    """
    if not chunks:
        raise ValueError("Cannot build prompt pack: chunks list is empty.")

    # Determine source_type from the first chunk
    source_type = chunks[0].source_type if chunks else "txt"

    prompt_chunks: list[ProviderPromptChunk] = []
    for c in chunks:
        prompt_chunks.append(
            ProviderPromptChunk(
                chunk_id=c.chunk_id,
                page_start=c.page_start,
                page_end=c.page_end,
                text=c.text,
            )
        )

    return ProviderPromptPack(
        audience_level=audience_level,
        desired_card_count=desired_card_count,
        source_type=source_type,
        source_chunks=prompt_chunks,
        output_contract=_default_output_contract(),
        safety_rules=_default_safety_rules(),
    )
