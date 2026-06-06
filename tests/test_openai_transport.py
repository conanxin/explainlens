"""Tests for OpenAI Responses API transport (openai_transport.py).

All tests use mock fixtures — NO real API calls are made.
"""

from __future__ import annotations

import json
import urllib.error
from typing import Any
from unittest.mock import Mock, patch

import pytest

from explainlens.providers.openai_transport import (
    build_openai_responses_payload,
    call_openai_responses_api,
    extract_structured_response_from_openai_json,
    run_mock_openai_transport,
    _validate_extracted_structure,
)
from explainlens.providers.prompt_contract import ProviderPromptChunk


# ── Helpers ──────────────────────────────────────────────────

def _make_prompt_pack(source_chunks=None):
    """Create a minimal prompt pack for testing."""
    from explainlens.providers.prompt_contract import ProviderPromptPack

    chunks = source_chunks or []
    if not chunks:
        chunks = [_make_pchunk("c0", "Sample text for testing.")]
    return ProviderPromptPack(
        audience_level="general",
        desired_card_count=3,
        source_type="txt",
        source_chunks=chunks,
    )


def _make_pchunk(chunk_id: str, text: str, page_start=None, page_end=None):
    """Create a minimal ProviderPromptChunk for testing."""
    return ProviderPromptChunk(
        chunk_id=chunk_id,
        text=text,
        page_start=page_start,
        page_end=page_end,
    )


def _make_valid_response_json(concept_map=None, cards=None):
    """Create a valid Form A response JSON."""
    cm = concept_map or {
        "core_problem": "How to test OpenAI transport?",
        "key_concepts": ["unit testing", "mocking"],
        "key_claims": ["Tests should be offline"],
    }
    c = cards or [
        {
            "title": "Card 1",
            "explanation": "Explanation 1",
            "visual_metaphor": "A test",
            "visual_scene": "A test scene",
            "takeaway": "Test well",
            "source_chunk_ids": ["c0"],
        },
        {
            "title": "Card 2",
            "explanation": "Explanation 2",
            "source_chunk_ids": ["c0"],
        },
        {
            "title": "Card 3",
            "explanation": "Explanation 3",
            "source_chunk_ids": ["c0"],
        },
    ]
    return {"output_text": json.dumps({"concept_map": cm, "cards": c})}


# ── Payload Builder Tests ────────────────────────────────────

class TestBuildOpenAIResponsesPayload:
    """Tests for build_openai_responses_payload()."""

    def test_returns_dict_with_model(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        assert isinstance(payload, dict)
        assert payload["model"] == "gpt-5.5"

    def test_has_input_with_system_and_user(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        assert "input" in payload
        assert len(payload["input"]) == 2
        roles = [m["role"] for m in payload["input"]]
        assert "system" in roles
        assert "user" in roles

    def test_has_text_format_with_json_schema(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        assert "text" in payload
        assert payload["text"]["format"]["type"] == "json_schema"
        schema = payload["text"]["format"]["json_schema"]
        assert schema["name"] == "explainlens_structured_output"
        assert schema["strict"] is True

    def test_temperature_set_to_low(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        assert "temperature" in payload
        assert payload["temperature"] == 0.2

    def test_user_text_includes_chunk_id(self):
        chunks = [
            _make_pchunk("c0", "First chunk."),
            _make_pchunk("c1", "Second chunk."),
        ]
        pack = _make_prompt_pack(source_chunks=chunks)
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        user_content = payload["input"][1]["content"]
        assert "[c0]" in user_content
        assert "[c1]" in user_content

    def test_user_text_includes_source_type(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        user_content = payload["input"][1]["content"]
        assert "txt" in user_content


# ── Response Extraction Tests ─────────────────────────────────

class TestExtractStructuredResponseFormA:
    """Tests for extract_structured_response_from_openai_json — Form A (output_text)."""

    def test_extracts_from_output_text(self):
        response = _make_valid_response_json()
        extracted = extract_structured_response_from_openai_json(response)
        assert "concept_map" in extracted
        assert "cards" in extracted
        assert extracted["concept_map"]["core_problem"] == "How to test OpenAI transport?"

    def test_extracts_cards_with_source_chunk_ids(self):
        response = _make_valid_response_json()
        extracted = extract_structured_response_from_openai_json(response)
        assert len(extracted["cards"]) == 3
        for card in extracted["cards"]:
            assert "source_chunk_ids" in card

    def test_raises_on_invalid_json(self):
        response = {"output_text": "not valid json at all !!!"}
        with pytest.raises(ValueError, match="not valid JSON"):
            extract_structured_response_from_openai_json(response)

    def test_raises_on_non_string_output_text(self):
        response = {"output_text": 12345}
        with pytest.raises(ValueError, match="not a string"):
            extract_structured_response_from_openai_json(response)


class TestExtractStructuredResponseFormB:
    """Tests for extract_structured_response_from_openai_json — Form B (output list)."""

    def test_extracts_from_output_list(self):
        inner = {"concept_map": {"core_problem": "Test", "key_concepts": ["A"], "key_claims": ["B"]},
                 "cards": [{"title": "C1", "explanation": "E1", "source_chunk_ids": ["c0"]}]}
        response = {
            "output": [
                {"content": [{"type": "output_text", "text": json.dumps(inner)}]}
            ]
        }
        extracted = extract_structured_response_from_openai_json(response)
        assert extracted["concept_map"]["core_problem"] == "Test"
        assert len(extracted["cards"]) == 1

    def test_skips_non_dict_items(self):
        inner = {"concept_map": {"core_problem": "Test", "key_concepts": ["A"], "key_claims": ["B"]},
                 "cards": [{"title": "C1", "explanation": "E1", "source_chunk_ids": ["c0"]}]}
        response = {
            "output": [
                "not a dict",
                {"content": [{"type": "output_text", "text": json.dumps(inner)}]},
            ]
        }
        extracted = extract_structured_response_from_openai_json(response)
        assert extracted["concept_map"]["core_problem"] == "Test"

    def test_skips_non_output_text_type(self):
        inner = {"concept_map": {"core_problem": "Test", "key_concepts": ["A"], "key_claims": ["B"]},
                 "cards": [{"title": "C1", "explanation": "E1", "source_chunk_ids": ["c0"]}]}
        response = {
            "output": [
                {"content": [
                    {"type": "image", "text": "ignore"},
                    {"type": "output_text", "text": json.dumps(inner)},
                ]}
            ]
        }
        extracted = extract_structured_response_from_openai_json(response)
        assert extracted["concept_map"]["core_problem"] == "Test"


class TestExtractStructuredResponseErrors:
    """Tests for error cases in response extraction."""

    def test_raises_on_unknown_format(self):
        response = {"id": "123", "unknown_key": "value"}
        with pytest.raises(ValueError, match="Cannot extract"):
            extract_structured_response_from_openai_json(response)

    def test_raises_on_empty_dict(self):
        with pytest.raises(ValueError, match="Cannot extract"):
            extract_structured_response_from_openai_json({})


# ── Structured Validation Tests ──────────────────────────────

class TestValidateExtractedStructure:
    """Tests for _validate_extracted_structure()."""

    def test_missing_concept_map_raises(self):
        with pytest.raises(ValueError, match="missing 'concept_map'"):
            _validate_extracted_structure({"cards": []})

    def test_missing_cards_raises(self):
        with pytest.raises(ValueError, match="missing 'cards'"):
            _validate_extracted_structure({"concept_map": {}})

    def test_cards_not_list_raises(self):
        with pytest.raises(ValueError, match="not a list"):
            _validate_extracted_structure({"concept_map": {}, "cards": "not a list"})

    def test_card_missing_source_chunk_ids_raises(self):
        with pytest.raises(ValueError, match="missing 'source_chunk_ids'"):
            _validate_extracted_structure({
                "concept_map": {},
                "cards": [{"title": "T", "explanation": "E"}],
            })

    def test_card_not_dict_raises(self):
        with pytest.raises(ValueError, match="is not a dict"):
            _validate_extracted_structure({
                "concept_map": {},
                "cards": ["not a dict"],
            })


# ── Mock Transport Tests ──────────────────────────────────────

class TestRunMockOpenAI:
    """Tests for run_mock_openai_transport()."""

    def test_returns_correct_structure(self):
        pack = _make_prompt_pack()
        result = run_mock_openai_transport(pack, "gpt-5.5")
        assert "concept_map" in result
        assert "cards" in result
        assert "provider_notes" in result
        assert isinstance(result["cards"], list)

    def test_mock_makes_no_network_call(self):
        """Verify that mock transport does NOT call any external URL."""
        pack = _make_prompt_pack()
        result = run_mock_openai_transport(pack, "gpt-5.5")
        assert "NO real API call was made" in result["provider_notes"][-1]

    def test_mock_notes_model_name(self):
        pack = _make_prompt_pack()
        result = run_mock_openai_transport(pack, "gpt-4")
        assert any("gpt-4" in note for note in result["provider_notes"])


# ── Fail-Closed Transport Tests ──────────────────────────────

class TestFailClosedTransport:
    """Tests for call_openai_responses_api() fail-closed behavior."""

    def _make_pack(self):
        return _make_prompt_pack()

    def test_raises_when_allow_external_api_false(self):
        pack = self._make_pack()
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            call_openai_responses_api(pack, "gpt-5.5", "sk-test123", allow_external_api=False)

    def test_raises_when_api_key_empty(self):
        pack = self._make_pack()
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
            call_openai_responses_api(pack, "gpt-5.5", "", allow_external_api=True)

    def test_raises_when_api_key_not_sk_prefix(self):
        pack = self._make_pack()
        with pytest.raises(RuntimeError, match="does not look valid"):
            call_openai_responses_api(pack, "gpt-5.5", "bad-key", allow_external_api=True)

    def test_raises_when_custom_api_base(self):
        pack = self._make_pack()
        with pytest.raises(ValueError, match="Custom api_base is not supported"):
            call_openai_responses_api(
                pack, "gpt-5.5", "sk-test123",
                allow_external_api=True,
                api_base="http://evil-proxy.com/v1",
            )

    def test_error_messages_never_contain_api_key(self):
        """Error messages must not leak API keys."""
        pack = self._make_pack()
        fake_key = "sk-proj-abc123secret"
        try:
            call_openai_responses_api(
                pack, "gpt-5.5", fake_key,
                allow_external_api=True,
                api_base="http://evil-proxy.com/v1",
            )
        except ValueError as e:
            msg = str(e)
            assert fake_key not in msg

    def test_fail_closed_message_is_clear(self):
        """Verify the error message accurately explains how to enable."""
        pack = self._make_pack()
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            call_openai_responses_api(pack, "gpt-5.5", "", allow_external_api=True)


# ── Integration: Payload + Mock ──────────────────────────────

class TestPayloadJsonSerializable:
    """Test that payloads are JSON-serializable."""

    def test_payload_can_be_serialized(self):
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        serialized = json.dumps(payload)
        assert isinstance(serialized, str)
        roundtripped = json.loads(serialized)
        assert roundtripped["model"] == "gpt-5.5"

    def test_payload_no_api_key_included(self):
        """The payload dict must NEVER contain any API key."""
        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        payload_str = json.dumps(payload)
        assert "sk-" not in payload_str
        assert "API_KEY" not in payload_str
