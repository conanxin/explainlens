"""Tests for local_http_transport.py."""

from __future__ import annotations

import json
import urllib.error
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from explainlens.providers.local_http_transport import (
    ProtocolType,
    build_local_http_payload,
    call_local_http_provider,
    extract_structured_response_from_chat_json,
    is_local_endpoint,
)


# ── is_local_endpoint tests ─────────────────────────────────

class TestIsLocalEndpoint:
    """Tests for is_local_endpoint()."""

    def test_accepts_localhost(self):
        assert is_local_endpoint("http://localhost:11434/api/chat") is True

    def test_accepts_localhost_with_path(self):
        assert is_local_endpoint("http://localhost:8080/v1/chat/completions") is True

    def test_accepts_127(self):
        assert is_local_endpoint("http://127.0.0.1:11434/api/chat") is True

    def test_accepts_ipv6_loopback(self):
        assert is_local_endpoint("http://[::1]:11434/api/chat") is True

    def test_rejects_https(self):
        assert is_local_endpoint("https://localhost:11434/api/chat") is False

    def test_rejects_openai(self):
        assert is_local_endpoint("https://api.openai.com/v1/chat/completions") is False
        assert is_local_endpoint("http://api.openai.com/v1/chat/completions") is False

    def test_rejects_example_com(self):
        assert is_local_endpoint("http://example.com/api") is False

    def test_rejects_private_ip(self):
        assert is_local_endpoint("http://192.168.1.1:8080/api") is False
        assert is_local_endpoint("http://10.0.0.1:8080/api") is False
        assert is_local_endpoint("http://172.16.0.1:8080/api") is False

    def test_rejects_empty_url(self):
        assert is_local_endpoint("") is False
        assert is_local_endpoint(None) is False

    def test_rejects_no_scheme(self):
        assert is_local_endpoint("localhost:11434") is False


# ── build_local_http_payload tests ─────────────────────────────

class TestBuildLocalHttpPayload:
    """Tests for build_local_http_payload()."""

    def _make_prompt_pack(self):
        from explainlens.providers.prompt_contract import ProviderPromptPack
        return ProviderPromptPack(
            audience_level="general",
            desired_card_count=8,
            source_type="txt",
            source_chunks=[],
        )

    def test_fixture_protocol_returns_marker(self):
        pack = self._make_prompt_pack()
        payload = build_local_http_payload(pack, "llama3.2", "fixture")
        assert payload.get("__fixture__") is True

    def test_ollama_chat_protocol_builds_payload(self):
        pack = self._make_prompt_pack()
        payload = build_local_http_payload(pack, "llama3.2", "ollama-chat")
        assert payload["model"] == "llama3.2"
        assert isinstance(payload["messages"], list)
        assert payload["stream"] is False
        assert payload["format"] == "json"

    def test_openai_compatible_chat_protocol_builds_payload(self):
        pack = self._make_prompt_pack()
        payload = build_local_http_payload(pack, "local-model", "openai-compatible-chat")
        assert payload["model"] == "local-model"
        assert isinstance(payload["messages"], list)
        assert "stream" not in payload  # OpenAI doesn't use stream in same way

    def test_unsupported_protocol_raises(self):
        pack = self._make_prompt_pack()
        with pytest.raises(ValueError, match="Unsupported protocol"):
            build_local_http_payload(pack, "model", "unsupported-protocol")  # type: ignore


# ── extract_structured_response_from_chat_json tests ────────

class TestExtractStructuredResponseFromChatJson:
    """Tests for extract_structured_response_from_chat_json()."""

    def test_parses_ollama_like_response(self):
        raw = {
            "message": {
                "content": json.dumps({
                    "concept_map": {"core_problem": "Test"},
                    "cards": [],
                })
            }
        }
        result = extract_structured_response_from_chat_json(raw, "ollama-chat")
        assert "concept_map" in result
        assert "cards" in result

    def test_parses_openai_compatible_response(self):
        raw = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "concept_map": {"core_problem": "Test"},
                            "cards": [],
                        })
                    }
                }
            ]
        }
        result = extract_structured_response_from_chat_json(raw, "openai-compatible-chat")
        assert "concept_map" in result
        assert "cards" in result

    def test_invalid_json_content_raises(self):
        raw = {
            "message": {
                "content": "not valid json {{{}"
            }
        }
        with pytest.raises(ValueError, match="not valid JSON"):
            extract_structured_response_from_chat_json(raw, "ollama-chat")

    def test_missing_concept_map_raises(self):
        raw = {
            "message": {
                "content": json.dumps({"cards": []})
            }
        }
        with pytest.raises(ValueError, match="missing.*concept_map"):
            extract_structured_response_from_chat_json(raw, "ollama-chat")

    def test_missing_cards_raises(self):
        raw = {
            "message": {
                "content": json.dumps({"concept_map": {"core_problem": "Test"}})
            }
        }
        with pytest.raises(ValueError, match="missing.*cards"):
            extract_structured_response_from_chat_json(raw, "ollama-chat")

    def test_unknown_response_format_returns_none_content(self):
        raw = {"unknown_key": "value"}
        with pytest.raises(ValueError, match="Could not extract"):
            extract_structured_response_from_chat_json(raw, "ollama-chat")


# ── call_local_http_provider tests ───────────────────────────

class TestCallLocalHttpProvider:
    """Tests for call_local_http_provider()."""

    def _make_prompt_pack(self):
        from explainlens.providers.prompt_contract import (
            ProviderPromptChunk,
            ProviderPromptPack,
        )
        return ProviderPromptPack(
            audience_level="general",
            desired_card_count=8,
            source_type="txt",
            source_chunks=[
                ProviderPromptChunk(chunk_id="chunk_001", text="Test content")
            ],
        )

    def test_allow_network_false_raises_runtime_error(self):
        pack = self._make_prompt_pack()
        with pytest.raises(RuntimeError, match="explicit network opt-in"):
            call_local_http_provider(
                prompt_pack=pack,
                endpoint="http://localhost:11434/api/chat",
                model="llama3.2",
                protocol="ollama-chat",
                allow_network=False,
            )

    def test_fixture_protocol_uses_offline_transport(self):
        pack = self._make_prompt_pack()
        result = call_local_http_provider(
            prompt_pack=pack,
            endpoint="http://localhost:11434/api/chat",
            model="llama3.2",
            protocol="fixture",
            allow_network=False,  # fixture doesn't need network
        )
        assert "concept_map" in result
        assert "cards" in result
        assert len(result["cards"]) == 8
        assert any("offline" in n.lower() or "fixture" in n.lower()
                   for n in result.get("provider_notes", []))

    @patch("urllib.request.urlopen")
    def test_successful_http_call(self, mock_urlopen):
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "content": json.dumps({
                    "concept_map": {"core_problem": "Test problem"},
                    "cards": [
                        {
                            "title": f"Card {i+1}",
                            "explanation": "Test explanation",
                            "visual_metaphor": "Test metaphor",
                            "visual_scene": "Test scene",
                            "takeaway": "Test takeaway",
                            "source_chunk_ids": ["chunk_001"],
                        }
                        for i in range(8)
                    ],
                })
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__ = lambda s: mock_response
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        pack = self._make_prompt_pack()
        result = call_local_http_provider(
            prompt_pack=pack,
            endpoint="http://localhost:11434/api/chat",
            model="llama3.2",
            protocol="ollama-chat",
            allow_network=True,
        )
        assert "concept_map" in result
        assert len(result["cards"]) == 8

    def test_non_loopback_endpoint_raises(self):
        pack = self._make_prompt_pack()
        with pytest.raises(ValueError, match="not a.*loopback"):
            call_local_http_provider(
                prompt_pack=pack,
                endpoint="http://192.168.1.1:8080/api",
                model="llama3.2",
                protocol="ollama-chat",
                allow_network=True,
            )

    def test_empty_endpoint_raises(self):
        pack = self._make_prompt_pack()
        with pytest.raises(ValueError, match="Endpoint must be a non-empty"):
            call_local_http_provider(
                prompt_pack=pack,
                endpoint="",
                model="llama3.2",
                protocol="ollama-chat",
                allow_network=True,
            )
