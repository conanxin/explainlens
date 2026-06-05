"""Tests for local-http CLI integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from explainlens.providers import list_providers


# ── Helper ─────────────────────────────────────────────

def _run_cli(args: list[str]) -> dict[str, Any]:
    """Run CLI with given args, return result dict.

    Returns:
        {"exit_code": int, "stdout": str, "stderr": str}
    """
    import io
    import subprocess
    import sys

    python = sys.executable
    result = subprocess.run(
        [python, "-m", "explainlens.cli"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _create_test_input(path: Path, content: str = "Test document content for analysis. " * 50) -> None:
    """Create a test input file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Provider listing tests ─────────────────────────────

class TestProvidersCommand:
    """Tests for `python -m explainlens.cli providers`."""

    def test_local_http_shown_in_providers_list(self):
        providers = list_providers()
        names = [p["name"] for p in providers]
        assert "local-http" in names


# ── Fixture protocol tests ────────────────────────

class TestLocalHttpFixtureProtocol:
    """Tests for fixture protocol (offline, no HTTP)."""

    def test_fixture_mode_runs_successfully(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "fixture",
        ])

        assert result["exit_code"] == 0, (
            f"CLI failed with exit code {result['exit_code']}\n"
            f"STDOUT:\n{result['stdout']}\n"
            f"STDERR:\n{result['stderr']}"
        )
        assert output_dir.exists()
        assert (output_dir / "provider_manifest.json").exists()
        assert (output_dir / "source_index.json").exists()
        assert (output_dir / "cards.html").exists()

    def test_fixture_mode_generates_8_cards(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "fixture",
        ])
        assert result["exit_code"] == 0

        # Check cards.json
        cards_path = output_dir / "cards.json"
        assert cards_path.exists()
        with open(cards_path, "r", encoding="utf-8") as f:
            cards = json.load(f)
        assert len(cards) == 8

    def test_fixture_mode_provider_manifest(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "fixture",
        ])
        assert result["exit_code"] == 0

        manifest_path = output_dir / "provider_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["provider"] == "local-http"
        assert manifest["uses_external_api"] is False
        assert "network" in manifest
        assert manifest["network"]["uses_local_http"] is False
        assert manifest["network"]["allows_remote_http"] is False
        assert manifest["network"]["protocol"] == "fixture"


# ── Fail-closed tests ────────────────────────────────

class TestLocalHttpFailClosed:
    """Tests for fail-closed behavior."""

    def test_non_fixture_without_allow_fails(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "ollama-chat",
            "--local-http-endpoint", "http://localhost:11434/api/chat",
        ])

        # Should fail because --allow-local-http is not set
        assert result["exit_code"] != 0
        # Error message should mention --allow-local-http or opt-in
        combined = result["stdout"] + result["stderr"]
        assert "allow" in combined.lower() or "opt-in" in combined.lower()

    def test_ollama_protocol_without_allow_fails(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "ollama-chat",
        ])

        assert result["exit_code"] != 0

    def test_openai_compatible_without_allow_fails(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "openai-compatible-chat",
        ])

        assert result["exit_code"] != 0


# ── Source Appendix tests ────────────────────────────

class TestLocalHttpSourceAppendix:
    """Tests for Source Appendix in HTML output."""

    def test_source_appendix_present(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "local-http",
            "--local-http-protocol", "fixture",
        ])
        assert result["exit_code"] == 0

        html_path = output_dir / "cards.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        assert "Source Appendix" in html_content
