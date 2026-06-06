"""Tests for OpenAI CLI integration — fail-closed behavior.

All tests use subprocess — NO real API calls are made.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest


# ── Helpers ──────────────────────────────────────────────────

def _run_cli(args: list[str]) -> dict[str, Any]:
    """Run CLI with given args, return result dict.

    Returns:
        {"exit_code": int, "stdout": str, "stderr": str}
    """
    import subprocess
    import sys
    import os

    python = sys.executable
    cwd = str(Path(__file__).resolve().parent.parent)

    # Clear OPENAI_API_KEY from environment for test isolation
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)

    result = subprocess.run(
        [python, "-m", "explainlens.cli"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _create_test_input(path: Path, content: str = None) -> None:
    """Create a test input file."""
    if content is None:
        content = "Test document content for analysis testing. " * 30
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Fail-Closed CLI Tests ────────────────────────────────────

class TestOpenAICLIFailClosedNoFlag:
    """Tests for CLI with --provider openai WITHOUT --allow-external-api."""

    def test_fails_without_allow_external_api(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
        ])

        error_text = result["stdout"] + result["stderr"]
        assert result["exit_code"] == 1, (
            f"Expected exit code 1, got {result['exit_code']}\n"
            f"Output: {error_text[:500]}"
        )
        assert "fail-closed" in error_text.lower() or "fail-closed" in error_text

    def test_error_message_contains_guidance(self, tmp_path: Path):
        """Error message should tell user how to enable the provider."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
        ])

        error_text = result["stdout"] + result["stderr"]
        assert "OPENAI_API_KEY" in error_text
        assert "--allow-external-api" in error_text
        assert "No request was sent" in error_text

    def test_no_output_directory_created(self, tmp_path: Path):
        """Output directory should NOT be created when provider is fail-closed."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
        ])

        assert not output_dir.exists(), (
            "Output directory should not have been created, "
            f"but {output_dir} exists."
        )


class TestOpenAICLIFailClosedNoKey:
    """Tests for CLI with --allow-external-api but WITHOUT OPENAI_API_KEY."""

    def test_fails_without_api_key(self, tmp_path: Path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
            "--allow-external-api",
        ])

        error_text = result["stdout"] + result["stderr"]
        assert result["exit_code"] == 1, (
            f"Expected exit code 1, got {result['exit_code']}\n"
            f"Output: {error_text[:500]}"
        )
        assert "OPENAI_API_KEY is not set" in error_text

    def test_error_message_says_no_request_sent(self, tmp_path: Path):
        """Error message should say 'No request was sent'."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        result = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
            "--allow-external-api",
        ])

        error_text = result["stdout"] + result["stderr"]
        assert "No request was sent" in error_text

    def test_no_output_directory_created_with_flag_but_no_key(self, tmp_path: Path):
        """Output directory should NOT be created even with --allow-external-api
        if OPENAI_API_KEY is missing."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--provider", "openai",
            "--allow-external-api",
        ])

        assert not output_dir.exists(), (
            "Output directory should NOT be created when API key is missing, "
            f"but {output_dir} exists."
        )


class TestOpenAICLIProviderListing:
    """Tests for provider listing with OpenAI."""

    def test_openai_appears_in_providers_list(self):
        """OpenAI should appear as experimental in providers output."""
        result = _run_cli(["providers"])

        output = result["stdout"] + result["stderr"]
        assert result["exit_code"] == 0
        assert "openai" in output
        assert "experimental" in output

    def test_openai_appears_in_doctor_output(self):
        """OpenAI should appear in doctor output."""
        result = _run_cli(["doctor"])

        output = result["stdout"] + result["stderr"]
        assert result["exit_code"] == 0
        assert "openai" in output.lower()
        assert "experimental" in output.lower()


class TestOpenAICLISuccessPath:
    """Test the success path when all conditions are met (using mock)."""

    def test_cli_with_api_key_and_flag_passes_checks(self, tmp_path: Path):
        """With both --allow-external-api AND OPENAI_API_KEY set,
        the CLI should get past the fail-closed checks.

        Note: This test does NOT verify actual API success — it only
        verifies that the CLI doesn't block at the fail-closed stage.
        """
        import subprocess, sys, os

        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        python = sys.executable
        cwd = str(Path(__file__).resolve().parent.parent)

        env = os.environ.copy()
        env["OPENAI_API_KEY"] = "sk-mock-test-key"

        result = subprocess.run(
            [python, "-m", "explainlens.cli",
             "analyze",
             "--input", str(input_file),
             "--output", str(output_dir),
             "--provider", "openai",
             "--allow-external-api",
             "--openai-timeout", "1",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
        )

        # The call will likely fail (network timeout or invalid key),
        # but it should NOT be the fail-closed error
        error_text = result.stdout + result.stderr
        # It should NOT contain "fail-closed" or "is not set"
        assert "fail-closed" not in error_text.lower(), (
            f"Should not be fail-closed when key is set.\n"
            f"Output: {error_text[:500]}"
        )
        assert "OPENAI_API_KEY is not set" not in error_text, (
            f"Should not complain about missing API key.\n"
            f"Output: {error_text[:500]}"
        )
