"""Tests for local provider docs and config templates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EXAMPLES_DIR = Path("examples/configs")
DOCS_DIR = Path("docs")


# ── Config Templates ─────────────────────────────────────

class TestConfigTemplates:
    """Test that config templates exist and are valid JSON."""

    def test_ollama_config_exists(self):
        """examples/configs/local-http-ollama.example.json should exist."""
        path = EXAMPLES_DIR / "local-http-ollama.example.json"
        assert path.exists(), f"Missing: {path}"
        assert path.is_file(), f"Not a file: {path}"

    def test_lm_studio_config_exists(self):
        """examples/configs/local-http-lmstudio.example.json should exist."""
        path = EXAMPLES_DIR / "local-http-lmstudio.example.json"
        assert path.exists(), f"Missing: {path}"
        assert path.is_file(), f"Not a file: {path}"

    def test_llamacpp_config_exists(self):
        """examples/configs/local-http-llamacpp.example.json should exist."""
        path = EXAMPLES_DIR / "local-http-llamacpp.example.json"
        assert path.exists(), f"Missing: {path}"
        assert path.is_file(), f"Not a file: {path}"

    def test_ollama_config_valid_json(self):
        """Ollama config should be valid JSON."""
        path = EXAMPLES_DIR / "local-http-ollama.example.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Config should be a JSON object"
        assert data.get("provider") == "local-http", "provider should be local-http"
        assert data.get("local_http_protocol") == "ollama-chat", "protocol should be ollama-chat"
        assert "local_http_endpoint" in data, "Should have local_http_endpoint"
        assert "allow_local_http" in data, "Should have allow_local_http"
        assert "timeout_seconds" in data, "Should have timeout_seconds"

    def test_lm_studio_config_valid_json(self):
        """LM Studio config should be valid JSON."""
        path = EXAMPLES_DIR / "local-http-lmstudio.example.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Config should be a JSON object"
        assert data.get("provider") == "local-http", "provider should be local-http"
        assert data.get("local_http_protocol") == "openai-compatible-chat", "protocol should be openai-compatible-chat"
        assert "local_http_endpoint" in data, "Should have local_http_endpoint"
        assert "127.0.0.1" in data["local_http_endpoint"], "Should use 127.0.0.1"

    def test_llamacpp_config_valid_json(self):
        """llama.cpp config should be valid JSON."""
        path = EXAMPLES_DIR / "local-http-llamacpp.example.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Config should be a JSON object"
        assert data.get("provider") == "local-http", "provider should be local-http"
        assert data.get("local_http_protocol") == "openai-compatible-chat", "protocol should be openai-compatible-chat"
        assert "8080" in data["local_http_endpoint"], "Should use port 8080"

    def test_ollama_config_has_loopback_endpoint(self):
        """Ollama config endpoint should be loopback."""
        path = EXAMPLES_DIR / "local-http-ollama.example.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        endpoint = data["local_http_endpoint"]
        assert "localhost" in endpoint, "Should use localhost"

    def test_all_configs_have_required_fields(self):
        """All config templates should have required fields."""
        required_fields = ["provider", "local_http_protocol", "local_http_endpoint",
                          "local_http_model", "allow_local_http", "timeout_seconds"]
        for config_file in EXAMPLES_DIR.glob("local-http-*.example.json"):
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for field in required_fields:
                assert field in data, f"Missing field '{field}' in {config_file.name}"


# ── Local Provider Guide ─────────────────────────────────────

class TestLocalProviderGuide:
    """Test that docs/LOCAL_PROVIDERS.md exists and contains key content."""

    def test_local_providers_md_exists(self):
        """docs/LOCAL_PROVIDERS.md should exist."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        assert path.exists(), f"Missing: {path}"
        assert path.is_file(), f"Not a file: {path}"

    def test_local_providers_md_contains_fail_closed(self):
        """LOCAL_PROVIDERS.md should mention fail-closed."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "fail-closed" in content.lower() or "fail closed" in content.lower(), (
            "LOCAL_PROVIDERS.md should mention fail-closed"
        )

    def test_local_providers_md_contains_loopback(self):
        """LOCAL_PROVIDERS.md should mention loopback."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "loopback" in content.lower() or "localhost" in content.lower(), (
            "LOCAL_PROVIDERS.md should mention loopback"
        )

    def test_local_providers_md_contains_ollama_example(self):
        """LOCAL_PROVIDERS.md should contain Ollama example."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "ollama" in content.lower(), (
            "LOCAL_PROVIDERS.md should mention Ollama"
        )

    def test_local_providers_md_contains_lm_studio_example(self):
        """LOCAL_PROVIDERS.md should contain LM Studio example."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "lm studio" in content.lower() or "lmstudio" in content.lower(), (
            "LOCAL_PROVIDERS.md should mention LM Studio"
        )

    def test_local_providers_md_contains_troubleshooting(self):
        """LOCAL_PROVIDERS.md should have troubleshooting section."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "troubleshoot" in content.lower() or "connection refused" in content.lower(), (
            "LOCAL_PROVIDERS.md should have troubleshooting section"
        )

    def test_local_providers_md_contains_no_streaming_limitation(self):
        """LOCAL_PROVIDERS.md should mention 'no streaming' limitation."""
        path = DOCS_DIR / "LOCAL_PROVIDERS.md"
        content = path.read_text(encoding="utf-8")
        assert "no streaming" in content.lower() or "streaming" in content.lower(), (
            "LOCAL_PROVIDERS.md should mention streaming limitation"
        )


# ── README Links ─────────────────────────────────────

class TestReadmeLinks:
    """Test that README.md links to LOCAL_PROVIDERS.md."""

    def test_readme_links_local_providers(self):
        """README.md should link to docs/LOCAL_PROVIDERS.md."""
        readme = Path("README.md")
        content = readme.read_text(encoding="utf-8")
        assert "LOCAL_PROVIDERS.md" in content, (
            "README.md should link to docs/LOCAL_PROVIDERS.md"
        )

    def test_readme_contains_doctor_command(self):
        """README.md should mention 'doctor' command."""
        readme = Path("README.md")
        content = readme.read_text(encoding="utf-8")
        assert "doctor" in content.lower(), (
            "README.md should mention doctor command"
        )

    def test_readme_contains_validate_endpoint_command(self):
        """README.md should mention 'validate-endpoint' command."""
        readme = Path("README.md")
        content = readme.read_text(encoding="utf-8")
        assert "validate-endpoint" in content or "validate_endpoint" in content, (
            "README.md should mention validate-endpoint command"
        )


# ── Improved Error Messages ─────────────────────────────────────

class TestImprovedErrorMessages:
    """Test that improved error messages are in the source code."""

    def test_fail_closed_error_contains_allow_flag(self):
        """Error message should mention --allow-local-http."""
        transport_file = Path("src/explainlens/providers/local_http_transport.py")
        content = transport_file.read_text(encoding="utf-8")
        assert "--allow-local-http" in content, (
            "local_http_transport.py should mention --allow-local-http in error"
        )

    def test_endpoint_rejection_contains_examples(self):
        """Endpoint rejection error should contain allowed endpoint examples."""
        transport_file = Path("src/explainlens/providers/local_http_transport.py")
        content = transport_file.read_text(encoding="utf-8")
        # Check that error message contains localhost example
        assert "localhost" in content, (
            "Error message should mention localhost example"
        )
        assert "127.0.0.1" in content, (
            "Error message should mention 127.0.0.1 example"
        )
