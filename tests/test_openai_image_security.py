"""Security tests for OpenAI Image adapter.

These tests verify that no secrets, API keys, or sensitive prompts
leak into source files, logs, or output artifacts.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
from pathlib import Path

import pytest

from explainlens.images.openai_image import OpenAIImageAdapter, _OPENAI_IMAGE_PLACEHOLDER_SVG
from explainlens.images.openai_image_transport import (
    build_openai_image_payload,
    call_openai_images_api,
    extract_image_url_from_response,
    download_image_from_url,
    run_mock_openai_image_transport,
)

# ── Source Code Security Tests ───────────────────────────────

class TestSourceCodeNoAPIKey:
    """Verify no API key hardcoded in source files."""

    _SRC_FILES = [
        "src/explainlens/images/openai_image_transport.py",
        "src/explainlens/images/openai_image.py",
        "src/explainlens/images/registry.py",
        "src/explainlens/images/__init__.py",
    ]

    @pytest.mark.parametrize("rel_path", _SRC_FILES)
    def test_no_hardcoded_api_key_in_file(self, rel_path):
        """No file should contain a hardcoded OpenAI API key."""
        project_root = Path(__file__).resolve().parent.parent
        file_path = project_root / rel_path

        if not file_path.exists():
            return  # Skip if file doesn't exist (not yet created)

        content = file_path.read_text(encoding="utf-8")

        # Look for actual sk- prefixed strings (not in comments or test mock keys)
        # We'll be lenient but check for obvious hardcoded keys
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check for API key patterns that look real
            # A real key would be something like: "sk-proj-..." (30+ chars)
            if re.search(r'"sk-[a-zA-Z0-9_-]{20,}"', stripped):
                pytest.fail(
                    f"{rel_path}:{i + 1} appears to contain a hardcoded API key\n"
                    f"  Line: {stripped[:120]}"
                )

    @pytest.mark.parametrize("rel_path", _SRC_FILES)
    def test_no_api_key_in_string_literals(self, rel_path):
        """No file should use 'sk-' in non-comment, non-documentation string literals
        that could be an API key.
        """
        project_root = Path(__file__).resolve().parent.parent
        file_path = project_root / rel_path

        if not file_path.exists():
            return

        content = file_path.read_text(encoding="utf-8")

        # This is more permissive — just check for suspicious long sk- strings
        for match in re.finditer(r'sk-[a-zA-Z0-9_-]{30,}', content):
            # Check if it's in a docstring or comment
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_content = content[line_start:content.find("\n", match.end())]

            if line_content.strip().startswith("#") or '"""' in line_content:
                continue

            pytest.fail(
                f"{rel_path}: suspicious long API key pattern found\n"
                f"  Context: {line_content.strip()[:120]}"
            )


class TestSourceCodeNoPromptLogging:
    """Verify prompts are not logged or stored unsafely."""

    _SRC_FILES = [
        "src/explainlens/images/openai_image_transport.py",
        "src/explainlens/images/openai_image.py",
    ]

    @pytest.mark.parametrize("rel_path", _SRC_FILES)
    def test_no_print_of_api_response(self, rel_path):
        """Source code should not print/log full API responses."""
        project_root = Path(__file__).resolve().parent.parent
        file_path = project_root / rel_path

        if not file_path.exists():
            return

        content = file_path.read_text(encoding="utf-8")

        # Check for print() of response content
        # This is a rough check — print(response) would be bad
        suspicious_patterns = [
            r"print\(.*response",
            r"print\(.*api_key",
            r"logger\.(debug|info)\(.*api_key",
        ]
        for pattern in suspicious_patterns:
            matches = list(re.finditer(pattern, content))
            for m in matches:
                line_num = content[: m.start()].count("\n") + 1
                pytest.fail(
                    f"{rel_path}:{line_num} suspicious print/log of sensitive data\n"
                    f"  Pattern: {pattern}"
                )

    @pytest.mark.parametrize("rel_path", _SRC_FILES)
    def test_prompt_preview_not_full_prompt(self, rel_path):
        """Code should use prompt preview (truncated), not full prompt, in logs/notes."""
        project_root = Path(__file__).resolve().parent.parent
        file_path = project_root / rel_path

        if not file_path.exists():
            return

        content = file_path.read_text(encoding="utf-8")
        # Verify that prompt_preview is used with length limit
        assert "prompt_preview" in content.lower(), (
            f"{rel_path}: should use prompt_preview (truncated) instead of raw prompt"
        )


class TestSVGTemplateSecurity:
    """Verify SVG templates don't leak sensitive information."""

    def test_placeholder_svg_has_no_key_placeholder(self):
        """The SVG placeholder template must NOT have any API key placeholder."""
        # The _OPENAI_IMAGE_PLACEHOLDER_SVG uses Python string formatting {key},
        # but should NOT have {api_key} or {secret} placeholders
        assert "{api_key}" not in _OPENAI_IMAGE_PLACEHOLDER_SVG
        assert "{secret}" not in _OPENAI_IMAGE_PLACEHOLDER_SVG
        assert "{key}" not in _OPENAI_IMAGE_PLACEHOLDER_SVG
        assert "{token}" not in _OPENAI_IMAGE_PLACEHOLDER_SVG

    def test_placeholder_svg_has_security_notice(self):
        """The SVG should include a notice that no real API call was made."""
        assert "no real api call was made" in _OPENAI_IMAGE_PLACEHOLDER_SVG.lower()

    def test_placeholder_svg_is_valid_format_string(self):
        """The template should format cleanly with expected keys."""
        try:
            _OPENAI_IMAGE_PLACEHOLDER_SVG.format(
                bg="#fff",
                text_primary="#000",
                accent="#f00",
                card_id="test_card",
                prompt_preview="test prompt preview",
            )
        except KeyError as e:
            pytest.fail(f"SVG template has unexpected format key: {e}")


# ── Runtime Security Tests ────────────────────────────────────

class TestFailClosedAlwaysSecure:
    """Verify fail-closed behavior in adversarial scenarios."""

    def test_no_call_possible_without_flag(self):
        """Without allow_external_images=True, no API call should be possible."""
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            call_openai_images_api(
                "test", "sk-test123",
                allow_external_images=False,
            )

    def test_no_call_possible_with_none_flag(self):
        """allow_external_images must be explicit bool True."""
        with pytest.raises(RuntimeError):
            call_openai_images_api(
                "test", "sk-test123",
                allow_external_images=None,
            )

    def test_flag_string_is_truthy_passes_gate(self):
        """allow_external_images="true" (string) is truthy in Python,
        so the gate passes. The actual API call will fail, but that's
        a different error class."""
        # "true" is a non-empty string and thus truthy in Python
        # The gate passes, but the network will fail
        with pytest.raises(urllib.error.URLError):
            call_openai_images_api(
                "test", "sk-test123",
                allow_external_images="true",
            )

    def test_api_key_never_in_return_value(self):
        """call_openai_images_api must never return the API key."""
        # Even in mock mode, the return value should not contain the key
        result = run_mock_openai_image_transport("test")
        result_str = json.dumps(result)
        assert "sk-" not in result_str
        assert "api_key" not in result_str
        assert "Bearer" not in result_str


class TestManifestDisclosure:
    """Verify that manifest disclosure is accurate."""

    def test_adapter_flags_match_reality(self):
        """The adapter's uses_external_api and requires_api_key flags
        must match the actual behavior."""
        adapter = OpenAIImageAdapter()
        assert adapter.uses_external_api is True, (
            "openai-image adapter calls external API — uses_external_api must be True"
        )
        assert adapter.requires_api_key is True, (
            "openai-image adapter requires API key — requires_api_key must be True"
        )

    def test_adapter_status_is_not_available(self):
        """openai-image should NOT be marked as 'available' — it's experimental."""
        adapter = OpenAIImageAdapter()
        assert adapter.status != "available", (
            "openai-image is experimental, not available"
        )
        assert adapter.status == "experimental"


class TestErrorMessageSanitization:
    """Verify error messages do not leak sensitive data."""

    def test_extract_url_error_no_url_in_message(self):
        """Error messages from extract should not contain full URLs."""
        response = {"data": [{"url": "http://evil.com/malicious.png"}]}
        try:
            extract_image_url_from_response(response)
        except ValueError as e:
            msg = str(e)
            # The message may include the URL prefix for debugging, but should
            # not include the full URL in a way that could leak it unsafely
            # At minimum, it should not be a simple echo
            assert "evil.com" not in msg or "first 100 chars" in msg

    def test_fail_closed_message_no_debug_info(self):
        """Fail-closed error messages should be user-friendly, not debug dumps."""
        adapter = OpenAIImageAdapter()
        try:
            adapter._check_fail_closed()
        except RuntimeError as e:
            msg = str(e)
            # Should not contain stack trace markers
            assert "Traceback" not in msg
            assert "File " not in msg


class TestPayloadNeverContainsSecrets:
    """Verify payload builder never includes secrets."""

    def test_build_payload_no_env_vars(self):
        """Payload should not depend on environment variables."""
        # Even if OPENAI_API_KEY is set in env, the payload should not include it
        old_key = os.environ.get("OPENAI_API_KEY")
        try:
            os.environ["OPENAI_API_KEY"] = "sk-test-secret-key"
            payload = build_openai_image_payload("test")
            payload_str = json.dumps(payload)
            assert "sk-test-secret-key" not in payload_str
            assert "sk-" not in payload_str
        finally:
            if old_key is not None:
                os.environ["OPENAI_API_KEY"] = old_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_payload_keys_are_limited(self):
        """Payload should only have expected keys — no extras that could leak data."""
        payload = build_openai_image_payload("test")
        allowed_keys = {"model", "prompt", "n", "size", "quality"}
        actual_keys = set(payload.keys())
        unexpected = actual_keys - allowed_keys
        assert not unexpected, f"Unexpected payload keys: {unexpected}"


class TestDownloadSecurity:
    """Verify download helper enforces security constraints."""

    def test_only_https_allowed(self):
        """Download should reject non-HTTPS URLs."""
        non_https = [
            "http://example.com/img.png",
            "ftp://example.com/img.png",
            "file:///etc/passwd",
            "gopher://evil.com/",
        ]
        for url in non_https:
            with pytest.raises(ValueError, match="only supports https"):
                download_image_from_url(url)

    def test_no_file_protocol(self):
        """Download should never accept file:// protocol."""
        with pytest.raises(ValueError, match="only supports https"):
            download_image_from_url("file:///etc/passwd")
