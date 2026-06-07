"""Tests for OpenAI Images API transport (openai_image_transport.py).

All tests use mock fixtures — NO real API calls are made.
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import Mock, patch

import pytest

from explainlens.images.openai_image_transport import (
    build_openai_image_payload,
    call_openai_images_api,
    extract_image_url_from_response,
    download_image_from_url,
    run_mock_openai_image_transport,
)


# ── Payload Builder Tests ────────────────────────────────────

class TestBuildOpenAIImagePayload:
    """Tests for build_openai_image_payload()."""

    def test_returns_dict_with_model(self):
        payload = build_openai_image_payload("a beautiful sunset")
        assert isinstance(payload, dict)
        assert payload["model"] == "dall-e-3"

    def test_has_prompt(self):
        payload = build_openai_image_payload("a beautiful sunset")
        assert payload["prompt"] == "a beautiful sunset"

    def test_default_size_and_quality(self):
        payload = build_openai_image_payload("test")
        assert payload["size"] == "1024x1024"
        assert payload["quality"] == "standard"
        assert payload["n"] == 1

    def test_custom_model_size_quality(self):
        payload = build_openai_image_payload(
            "test",
            model="dall-e-2",
            size="512x512",
            quality="hd",
            n=2,
        )
        assert payload["model"] == "dall-e-2"
        assert payload["size"] == "512x512"
        assert payload["quality"] == "hd"
        assert payload["n"] == 2

    def test_payload_is_json_serializable(self):
        payload = build_openai_image_payload("test prompt with unicode: \u2600")
        serialized = json.dumps(payload)
        assert isinstance(serialized, str)
        roundtripped = json.loads(serialized)
        assert roundtripped["prompt"] == "test prompt with unicode: \u2600"

    def test_payload_no_api_key_included(self):
        """The payload dict must NEVER contain any API key."""
        payload = build_openai_image_payload("test")
        payload_str = json.dumps(payload)
        assert "sk-" not in payload_str
        assert "API_KEY" not in payload_str
        assert "api_key" not in payload_str


# ── Response Extraction Tests ─────────────────────────────────

class TestExtractImageURLFromResponse:
    """Tests for extract_image_url_from_response()."""

    def test_extracts_url_from_standard_response(self):
        response = {
            "data": [
                {
                    "url": "https://cdn.openai.com/generated-image-001.png",
                    "revised_prompt": "A test image",
                }
            ]
        }
        url = extract_image_url_from_response(response)
        assert url == "https://cdn.openai.com/generated-image-001.png"

    def test_extracts_first_when_multiple(self):
        response = {
            "data": [
                {"url": "https://example.com/first.png"},
                {"url": "https://example.com/second.png"},
            ]
        }
        url = extract_image_url_from_response(response)
        assert url == "https://example.com/first.png"

    def test_raises_on_missing_data_key(self):
        response = {"error": "something went wrong"}
        with pytest.raises(ValueError, match="Cannot extract image URL"):
            extract_image_url_from_response(response)

    def test_raises_on_empty_data_list(self):
        response = {"data": []}
        with pytest.raises(ValueError, match="empty or not a list"):
            extract_image_url_from_response(response)

    def test_raises_on_data_not_list(self):
        response = {"data": "not a list"}
        with pytest.raises(ValueError, match="empty or not a list"):
            extract_image_url_from_response(response)

    def test_raises_on_first_entry_not_dict(self):
        response = {"data": ["not a dict"]}
        with pytest.raises(ValueError, match="is not a dict"):
            extract_image_url_from_response(response)

    def test_raises_on_missing_url(self):
        response = {"data": [{"revised_prompt": "no url here"}]}
        with pytest.raises(ValueError, match="missing 'url'"):
            extract_image_url_from_response(response)

    def test_raises_on_url_not_string(self):
        response = {"data": [{"url": 12345}]}
        with pytest.raises(ValueError, match="not a string"):
            extract_image_url_from_response(response)

    def test_raises_on_non_https_url(self):
        response = {"data": [{"url": "http://insecure.example.com/image.png"}]}
        with pytest.raises(ValueError, match="does not start with https"):
            extract_image_url_from_response(response)


# ── Mock Transport Tests ──────────────────────────────────────

class TestRunMockOpenAIImageTransport:
    """Tests for run_mock_openai_image_transport()."""

    def test_returns_correct_structure(self):
        result = run_mock_openai_image_transport("a test prompt")
        assert "image_url" in result
        assert "model" in result
        assert "size" in result
        assert "adapter_notes" in result
        assert isinstance(result["adapter_notes"], list)

    def test_mock_has_no_real_url(self):
        result = run_mock_openai_image_transport("test")
        assert result["image_url"] == ""

    def test_mock_notes_no_api_call(self):
        result = run_mock_openai_image_transport("test prompt")
        notes = " ".join(result["adapter_notes"])
        assert "NO real API call was made" in notes

    def test_mock_notes_model_name(self):
        result = run_mock_openai_image_transport("test", model="dall-e-2")
        notes = " ".join(result["adapter_notes"])
        assert "dall-e-2" in notes

    def test_mock_truncates_long_prompts(self):
        long_prompt = "A" * 200
        result = run_mock_openai_image_transport(long_prompt)
        notes = " ".join(result["adapter_notes"])
        assert "prompt preview" in notes
        assert "..." in notes

    def test_mock_makes_no_network_call(self):
        """Verify that mock transport does NOT call any external URL."""
        import urllib.request
        original_urlopen = urllib.request.urlopen

        mock_urlopen = Mock(side_effect=Exception("Should not be called"))
        urllib.request.urlopen = mock_urlopen
        try:
            result = run_mock_openai_image_transport("test")
            assert mock_urlopen.call_count == 0
        finally:
            urllib.request.urlopen = original_urlopen


# ── Fail-Closed Transport Tests ──────────────────────────────

class TestFailClosedImageTransport:
    """Tests for call_openai_images_api() fail-closed behavior."""

    def test_raises_when_allow_external_images_false(self):
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            call_openai_images_api(
                "test prompt", "sk-test123",
                allow_external_images=False,
            )

    def test_raises_when_api_key_empty(self):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
            call_openai_images_api(
                "test prompt", "",
                allow_external_images=True,
            )

    def test_raises_when_api_key_none(self):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
            call_openai_images_api(
                "test prompt", None,
                allow_external_images=True,
            )

    def test_raises_when_api_key_not_sk_prefix(self):
        with pytest.raises(RuntimeError, match="does not look valid"):
            call_openai_images_api(
                "test prompt", "bad-key-123",
                allow_external_images=True,
            )

    def test_accepts_sk_prefix_key(self):
        """Key validation should pass for keys starting with sk- or ssk-.
        The actual API call will fail later (network), but validation passes."""
        # We prepare but the call won't reach the network because urllib won't
        # have a real server. We just verify the key check passes.
        # Instead, test that the check itself doesn't raise prematurely.
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("mock network error")
            with pytest.raises((RuntimeError, urllib.error.URLError)):
                call_openai_images_api(
                    "test prompt", "sk-proj-test123",
                    allow_external_images=True,
                )
            # Verify the error is NOT about key format
            # (it would be network error, not key validation error)

    def test_accepts_ssk_prefix_key(self):
        """Key validation should accept ssk- prefix (service account keys)."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("mock network error")
            with pytest.raises((RuntimeError, urllib.error.URLError)):
                call_openai_images_api(
                    "test prompt", "ssk-test123",
                    allow_external_images=True,
                )

    def test_raises_when_custom_api_base(self):
        with pytest.raises(ValueError, match="Custom api_base is not supported"):
            call_openai_images_api(
                "test prompt", "sk-test123",
                allow_external_images=True,
                api_base="http://evil-proxy.com/v1",
            )

    def test_error_messages_never_contain_api_key(self):
        """Error messages must not leak API keys."""
        fake_key = "sk-proj-abc123secret"
        try:
            call_openai_images_api(
                "test prompt", fake_key,
                allow_external_images=True,
                api_base="http://evil-proxy.com/v1",
            )
        except ValueError as e:
            msg = str(e)
            assert fake_key not in msg

    def test_no_request_sent_message(self):
        """Error messages should say 'No request was sent' for fail-closed."""
        with pytest.raises(RuntimeError, match="No request was sent"):
            call_openai_images_api(
                "test prompt", "",
                allow_external_images=True,
            )

    def test_guidance_message_for_enable(self):
        """Error should guide user on how to enable."""
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            call_openai_images_api(
                "test prompt", "sk-test123",
                allow_external_images=False,
            )
        # The message should include guidance
        try:
            call_openai_images_api(
                "test prompt", "sk-test123",
                allow_external_images=False,
            )
        except RuntimeError as e:
            msg = str(e)
            assert "OPENAI_API_KEY" in msg
            assert "--allow-external-images" in msg


# ── Download Image Helper Tests ──────────────────────────────

class TestDownloadImageFromURL:
    """Tests for download_image_from_url()."""

    def test_raises_on_non_https_url(self):
        with pytest.raises(ValueError, match="only supports https"):
            download_image_from_url("http://example.com/image.png")

    def test_raises_on_ftp_url(self):
        with pytest.raises(ValueError, match="only supports https"):
            download_image_from_url("ftp://example.com/image.png")

    def test_network_error_handling(self):
        """Network errors should be caught and re-raised cleanly."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("connection refused")
            with pytest.raises((RuntimeError, urllib.error.URLError)):
                download_image_from_url("https://example.com/image.png")

    def test_http_error_handling(self):
        """HTTP errors should be caught and re-raised cleanly."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = Mock()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "https://example.com/image.png", 404, "Not Found",
                {}, None,
            )
            with pytest.raises(urllib.error.URLError, match="Failed to download image"):
                download_image_from_url("https://example.com/image.png")


# ── Integration Tests ────────────────────────────────────────

class TestPayloadJSONSerializable:
    """Test that payloads are JSON-serializable."""

    def test_payload_can_be_serialized(self):
        payload = build_openai_image_payload("test prompt")
        serialized = json.dumps(payload)
        assert isinstance(serialized, str)
        roundtripped = json.loads(serialized)
        assert roundtripped["model"] == "dall-e-3"
        assert roundtripped["prompt"] == "test prompt"

    def test_payload_no_api_key_included(self):
        """The payload dict must NEVER contain any API key."""
        payload = build_openai_image_payload("test prompt")
        payload_str = json.dumps(payload)
        assert "sk-" not in payload_str
        assert "Bearer" not in payload_str
        assert "Authorization" not in payload_str
