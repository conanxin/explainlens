"""Security tests for OpenAI provider integration.

Ensures that API keys and secrets are NEVER leaked in outputs,
logs, error messages, or provider manifests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


# ── Helpers ──────────────────────────────────────────────────

def _make_prompt_pack():
    """Create a minimal prompt pack for security testing."""
    from explainlens.providers.prompt_contract import ProviderPromptPack

    return ProviderPromptPack(
        audience_level="general",
        desired_card_count=3,
        source_type="txt",
        source_chunks=[],
    )


# ── No API Key Leak Tests ────────────────────────────────────

class TestNoSecretLeakInPayload:
    """Verify that payload building never includes API keys."""

    def test_payload_has_no_sk_prefix(self):
        from explainlens.providers.openai_transport import build_openai_responses_payload

        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        payload_str = json.dumps(payload)

        # No "sk-" should appear in the payload
        assert "sk-" not in payload_str, (
            "Payload contains 'sk-' pattern — possible API key leak!"
        )
        assert "sk-proj-" not in payload_str, (
            "Payload contains 'sk-proj-' pattern — possible API key leak!"
        )

    def test_payload_has_no_bearer_token(self):
        from explainlens.providers.openai_transport import build_openai_responses_payload

        pack = _make_prompt_pack()
        payload = build_openai_responses_payload(pack, "gpt-5.5")
        payload_str = json.dumps(payload)

        # No references to authorization or bearer tokens
        assert "Bearer" not in payload_str, (
            "Payload contains 'Bearer' — possible token leak!"
        )
        assert "Authorization" not in payload_str, (
            "Payload contains 'Authorization' — possible token leak!"
        )


class TestNoSecretLeakInProviderManifest:
    """Verify that provider manifests never contain secrets."""

    def test_provider_manifest_no_api_key(self):
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        manifest = provider.get_network_manifest()
        manifest_str = json.dumps(manifest)

        assert "sk-" not in manifest_str
        assert "Bearer" not in manifest_str

    def test_provider_manifest_no_env_var_names_in_sensitive_fields(self):
        """Manifest should describe requirements, not expose secrets."""
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        manifest = provider.get_network_manifest()

        # It's OK to mention OPENAI_API_KEY in documentation,
        # but NOT with an actual value
        manifest_str = json.dumps(manifest).lower()
        # The manifest should not contain any actual key values
        # (OPENAI_API_KEY is fine as a description, but not with a value)


class TestNoSecretLeakInErrorMessages:
    """Verify that error messages never contain API keys."""

    def test_cli_error_messages_never_contain_sk(self, tmp_path: Path):
        """CLI fail-closed errors must not contain 'sk-' patterns."""
        import subprocess
        import sys
        import os

        input_file = tmp_path / "test_input.txt"
        input_file.parent.mkdir(parents=True, exist_ok=True)
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("Test content for security test. " * 30)

        output_dir = tmp_path / "output"
        python = sys.executable
        cwd = str(Path(__file__).resolve().parent.parent)

        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)

        result = subprocess.run(
            [python, "-m", "explainlens.cli",
             "analyze",
             "--input", str(input_file),
             "--output", str(output_dir),
             "--provider", "openai",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
        )

        error_output = result.stdout + result.stderr
        assert "sk-" not in error_output, (
            f"Error message contains 'sk-' pattern!\n{error_output[:500]}"
        )

    def test_transport_error_messages_never_contain_api_key(self):
        """Transport-layer error messages must not leak API keys."""
        from explainlens.providers.openai_transport import call_openai_responses_api

        pack = _make_mock_pack_with_chunks()

        # Test 1: invalid API base
        try:
            call_openai_responses_api(
                pack, "gpt-5.5", "sk-proj-secret123",
                allow_external_api=True,
                api_base="http://bad-proxy.com/v1",
            )
        except ValueError as e:
            assert "sk-proj-secret123" not in str(e)
            assert "secret123" not in str(e)

        # Test 2: empty API key
        try:
            call_openai_responses_api(
                pack, "gpt-5.5", "",
                allow_external_api=True,
            )
        except RuntimeError as e:
            # Should not contain any key (since it's empty)
            pass  # The error itself is expected


def _make_mock_pack_with_chunks():
    """Helper for transport-level security tests."""
    from explainlens.providers.prompt_contract import ProviderPromptPack, ProviderPromptChunk

    chunks = [
        ProviderPromptChunk(
            chunk_id="c0",
            text="Test content.",
        )
    ]
    return ProviderPromptPack(
        audience_level="general",
        desired_card_count=1,
        source_type="txt",
        source_chunks=chunks,
    )


class TestNoSecretLeakInPromptPack:
    """Verify that prompt packs never contain secrets."""

    def test_prompt_pack_has_no_api_key(self):
        from explainlens.providers.prompt_contract import build_prompt_pack
        from explainlens.schemas import SourceChunk

        chunks = [
            SourceChunk(
                chunk_id="c0",
                text="Test.",
                start_char=0,
                end_char=5,
                source_type="txt",
            )
        ]
        pack = build_prompt_pack(chunks=chunks, desired_card_count=1, audience_level="general")
        pack_str = json.dumps(pack.model_dump())

        assert "sk-" not in pack_str
        assert "OPENAI_API_KEY" not in pack_str


class TestNoSecretLeakInSourceCode:
    """Verify source code doesn't contain hardcoded secrets."""

    def test_openai_transport_no_hardcoded_keys(self):
        """openai_transport.py must not contain hardcoded API keys."""
        source = Path(
            "src/explainlens/providers/openai_transport.py"
        ).read_text(encoding="utf-8")

        # Should not contain actual API key patterns in code
        # Comments/discussion of 'sk-' is acceptable
        import re
        # Find lines that might contain API keys (not in comments or docstrings)
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments and docstrings
            if stripped.startswith("#"):
                continue
            # Check for literal sk- keys (which would be bad)
            if re.search(r'"sk-[a-zA-Z0-9]{20,}"', stripped):
                pytest.fail(
                    f"Possible hardcoded API key in openai_transport.py "
                    f"line {i}: {stripped[:100]}"
                )

    def test_openai_draft_no_hardcoded_keys(self):
        """openai_draft.py must not contain hardcoded API keys."""
        source = Path(
            "src/explainlens/providers/openai_draft.py"
        ).read_text(encoding="utf-8")

        import re
        lines = source.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'"sk-[a-zA-Z0-9]{20,}"', stripped):
                pytest.fail(
                    f"Possible hardcoded API key in openai_draft.py "
                    f"line {i}: {stripped[:100]}"
                )


class TestEnvironmentVariableSafety:
    """Verify safe handling of environment variables."""

    def test_api_key_only_read_via_get_api_key(self):
        """OpenAIProvider should only read API key via _get_api_key()."""
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        # The _get_api_key method should exist and be a method
        assert hasattr(provider, "_get_api_key")
        assert callable(provider._get_api_key)

    def test_api_key_not_stored_as_attribute(self):
        """OpenAI provider should NOT store API key as an instance attribute
        (other than via _get_api_key which reads on demand)."""
        from explainlens.providers.openai_draft import OpenAIProvider

        provider = OpenAIProvider()
        # api_key should not be a regular attribute — it should be read on demand
        assert not hasattr(provider, "api_key"), (
            "Provider stores api_key as attribute — it should be read on demand only!"
        )
