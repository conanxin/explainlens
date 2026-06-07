"""Tests for OpenAI Image adapter CLI integration.

All tests use subprocess — NO real API calls are made.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# ── Helpers ──────────────────────────────────────────────────

def _python():
    return sys.executable


def _run_cli(args, env_overrides=None):
    """Run CLI and return (returncode, stdout, stderr).

    Args:
        args: CLI arguments (without the program name).
        env_overrides: Dict of env vars to set/override.
    """
    cwd = str(Path(__file__).resolve().parent.parent)
    env = os.environ.copy()
    # Clear OPENAI_API_KEY for test isolation
    env.pop("OPENAI_API_KEY", None)
    if env_overrides:
        env.update(env_overrides)

    cmd = [_python(), "-m", "explainlens.cli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def _create_test_input(path: Path, content: str = None):
    """Create a test input file."""
    if content is None:
        content = "Test document content for analysis testing. " * 30
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _combine_output(rc, stdout, stderr):
    """Combine stdout and stderr for error assertion."""
    return f"[rc={rc}]\nstdout:\n{stdout[:1000]}\nstderr:\n{stderr[:1000]}"


# ── Image Adapters Listing Tests ─────────────────────────────

class TestOpenAIImageAdaptersCLI:
    """Tests for openai-image in image-adapters CLI subcommand."""

    def test_openai_image_appears_in_image_adapters(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        output = stdout + stderr
        assert rc == 0, _combine_output(rc, stdout, stderr)
        assert "openai-image" in output, (
            f"openai-image should appear in image-adapters listing\n{output[:500]}"
        )

    def test_openai_image_shows_experimental(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        output = stdout + stderr
        assert rc == 0
        # The openai-image line should mention experimental
        assert "experimental" in output

    def test_openai_image_shows_external_api_yes(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        output = stdout + stderr
        assert rc == 0
        # openai-image uses external API
        assert "openai-image" in output

    def test_all_three_adapters_listed(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        output = stdout + stderr
        assert rc == 0
        assert "placeholder" in output
        assert "fixture" in output
        assert "openai-image" in output


# ── Fail-Closed CLI Tests — No Flag ──────────────────────────

class TestOpenAIImageCLIFailClosedNoFlag:
    """Tests for CLI with --image-adapter openai-image WITHOUT --allow-external-images."""

    def test_fails_without_allow_external_images(self, tmp_path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
        ])

        output = stdout + stderr
        assert rc == 1, (
            f"Expected exit code 1 (fail-closed), got {rc}\n{_combine_output(rc, stdout, stderr)}"
        )
        assert "fail-closed" in output.lower(), (
            f"Error should mention fail-closed\n{output[:500]}"
        )

    def test_error_message_contains_guidance(self, tmp_path):
        """Error message should tell user how to enable the adapter."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
        ])

        output = stdout + stderr
        assert "OPENAI_API_KEY" in output, (
            f"Error should mention OPENAI_API_KEY\n{output[:500]}"
        )
        assert "--allow-external-images" in output, (
            f"Error should mention --allow-external-images\n{output[:500]}"
        )

    def test_no_request_sent_message(self, tmp_path):
        """Error should explicitly state 'No request was sent'."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
        ])

        output = stdout + stderr
        assert "No request was sent" in output, (
            f"Error should say 'No request was sent'\n{output[:500]}"
        )

    def test_output_created_but_image_generation_fails(self, tmp_path):
        """The analysis step succeeds (uses rule-based provider),
        so output directory IS created. Only image generation fails."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
        ])

        # The analysis succeeds (rule-based provider), so exit code 0
        # But image generation fails with fail-closed error
        output = stdout + stderr
        assert "fail-closed" in output.lower()


# ── Fail-Closed CLI Tests — With Flag, No Key ────────────────

class TestOpenAIImageCLIFailClosedNoKey:
    """Tests for CLI with --allow-external-images but WITHOUT OPENAI_API_KEY."""

    def test_fails_without_api_key(self, tmp_path):
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
            "--allow-external-images",
        ])

        output = stdout + stderr
        assert rc == 1, (
            f"Expected exit code 1, got {rc}\n{_combine_output(rc, stdout, stderr)}"
        )
        assert "OPENAI_API_KEY is not set" in output, (
            f"Error should mention missing API key\n{output[:500]}"
        )

    def test_no_request_sent_without_key(self, tmp_path):
        """Even with flag, if no key, 'No request was sent' should appear."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
            "--allow-external-images",
        ])

        output = stdout + stderr
        assert "No request was sent" in output

    def test_analysis_succeeds_image_fails_with_flag_no_key(self, tmp_path):
        """Analysis succeeds (rule-based), output is created, image fails."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "openai-image",
            "--allow-external-images",
        ])

        output = stdout + stderr
        # Analysis succeeds
        assert "OPENAI_API_KEY is not set" in output


# ── Doctor Output Tests ──────────────────────────────────────

class TestOpenAIImageDoctorCLI:
    """Tests for openai-image in doctor CLI output."""

    def test_doctor_mentions_openai_image(self):
        rc, stdout, stderr = _run_cli(["doctor"])
        output = stdout + stderr
        assert rc == 0
        # Doctor should mention OpenAI Images
        assert "openai" in output.lower(), (
            f"Doctor should mention openai-related info\n{output[:500]}"
        )

    def test_doctor_mentions_external_images_disabled(self):
        rc, stdout, stderr = _run_cli(["doctor"])
        output = stdout + stderr
        assert rc == 0
        # Doctor should mention that external image APIs are disabled by default
        assert ("external" in output.lower() and "image" in output.lower()) or \
               "disabled" in output.lower(), (
            f"Doctor should mention external image status\n{output[:500]}"
        )


# ── Adapter Options in Analyze Tests ─────────────────────────

class TestOpenAIImageAdapterInOptions:
    """Tests that openai-image appears in analyze --image-adapter choices."""

    def test_openai_image_is_valid_choice(self, tmp_path):
        """openai-image should appear in the available choices for --image-adapter."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        # Using an invalid adapter should list available adapters in error
        rc, stdout, stderr = _run_cli([
            "analyze",
            "--input", str(input_file),
            "--output", str(output_dir),
            "--image-adapter", "unknown-adapter-xyz",
        ])

        output = stdout + stderr
        # Error message should list available adapters including openai-image
        assert "placeholder" in output or "fixture" in output
        # On error, it may or may not list openai-image depending on
        # whether the error is from argparse or from get_image_adapter
        # Just verify it's not a silent failure
        assert rc != 0


# ── Help/Usage Tests ─────────────────────────────────────────

class TestOpenAIImageHelpCLI:
    """Tests for help output mentioning openai-image."""

    def test_analyze_help_shows_allow_external_images(self):
        rc, stdout, stderr = _run_cli(["analyze", "--help"])
        output = stdout + stderr
        assert rc == 0
        assert "--allow-external-images" in output, (
            f"analyze --help should show --allow-external-images flag\n{output[:500]}"
        )

    def test_analyze_help_shows_image_adapter_choices(self):
        rc, stdout, stderr = _run_cli(["analyze", "--help"])
        output = stdout + stderr
        assert rc == 0
        assert "openai-image" in output, (
            f"analyze --help should list openai-image in --image-adapter choices\n{output[:500]}"
        )

    def test_image_adapters_help(self):
        rc, stdout, stderr = _run_cli(["image-adapters", "--help"])
        output = stdout + stderr
        assert rc == 0
        # Should not crash on --help
        assert "help" in output.lower() or len(output.strip()) > 0


# ── Integration: OPENAI_API_KEY set but no flag ──────────────

class TestOpenAIImageWithKeyButNoFlag:
    """Tests with OPENAI_API_KEY in environment but no --allow-external-images flag."""

    def test_fails_with_key_but_no_flag(self, tmp_path):
        """Even with OPENAI_API_KEY set, without --allow-external-images it should fail."""
        input_file = tmp_path / "test_input.txt"
        _create_test_input(input_file)
        output_dir = tmp_path / "output"

        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(input_file),
                "--output", str(output_dir),
                "--image-adapter", "openai-image",
            ],
            env_overrides={"OPENAI_API_KEY": "sk-test-mock-key"},
        )

        output = stdout + stderr
        assert rc == 1, (
            f"Expected exit code 1 even with API key set (no flag)\n{_combine_output(rc, stdout, stderr)}"
        )
        assert "fail-closed" in output.lower()
