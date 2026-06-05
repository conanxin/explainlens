"""Tests for provider prompt contract (prompt_contract.py)."""

from explainlens.schemas import SourceChunk
from explainlens.providers.prompt_contract import (
    build_prompt_pack,
    ProviderPromptPack,
    ProviderPromptChunk,
)


def _make_chunks(n: int = 4, source_type: str = "txt") -> list[SourceChunk]:
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{i+1:03d}",
                text=f"This is chunk {i+1} with sample content for testing.",
                start_char=i * 100,
                end_char=(i + 1) * 100,
                source_type=source_type,
            )
        )
    return chunks


def _make_pdf_chunks(n: int = 3) -> list[SourceChunk]:
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{i+1:03d}",
                text=f"PDF chunk {i+1} content.",
                start_char=i * 500,
                end_char=(i + 1) * 500,
                source_type="pdf",
                page_start=i + 1,
                page_end=i + 1,
            )
        )
    return chunks


class TestBuildPromptPack:
    """Tests for build_prompt_pack()."""

    def test_contains_all_chunk_ids(self):
        chunks = _make_chunks(4)
        pack = build_prompt_pack(chunks)
        ids = {c.chunk_id for c in pack.source_chunks}
        assert ids == {"chunk_001", "chunk_002", "chunk_003", "chunk_004"}

    def test_pdf_prompt_chunk_has_page_info(self):
        chunks = _make_pdf_chunks(3)
        pack = build_prompt_pack(chunks)
        assert pack.source_chunks[0].page_start == 1
        assert pack.source_chunks[0].page_end == 1
        assert pack.source_chunks[2].page_start == 3

    def test_safety_rules_include_preserve_chunk_ids(self):
        pack = build_prompt_pack(_make_chunks(3))
        assert any(
            "preserve source_chunk_ids" in r or "source_chunk_ids" in r
            for r in pack.safety_rules
        )

    def test_safety_rules_include_exactly_8_cards(self):
        pack = build_prompt_pack(_make_chunks(3))
        assert any("exactly 8" in r for r in pack.safety_rules)

    def test_output_contract_requires_cards(self):
        pack = build_prompt_pack(_make_chunks(3))
        assert "cards" in pack.output_contract
        assert pack.output_contract["cards"]["count"] == 8

    def test_output_contract_requires_source_traceability(self):
        pack = build_prompt_pack(_make_chunks(3))
        assert "source_traceability" in pack.output_contract

    def test_task_is_explain_complex_content(self):
        pack = build_prompt_pack(_make_chunks(2))
        assert pack.task == "explain_complex_content"

    def test_desired_card_count(self):
        pack = build_prompt_pack(_make_chunks(2), desired_card_count=6)
        assert pack.desired_card_count == 6

    def test_empty_chunks_raises(self):
        try:
            build_prompt_pack([])
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_prompt_pack_model_dump(self):
        pack = build_prompt_pack(_make_chunks(2))
        d = pack.model_dump()
        assert d["task"] == "explain_complex_content"
        assert len(d["source_chunks"]) == 2
        assert len(d["safety_rules"]) > 0
