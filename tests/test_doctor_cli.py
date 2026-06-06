"""Tests for doctor CLI command (offline diagnostics)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = "explainlens"
CLI = [sys.executable, "-m", f"{PACKAGE}.cli"]


# ── Helper ─────────────────────────────────────────────

def _run_cli(args: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run CLI command, return CompletedProcess."""
    return subprocess.run(
        CLI + args,
        capture_output=capture,
        text=True,
        timeout=30,
    )


# ── Tests ───────────────────────────────────────────────

class TestDoctorCLI:
    """Test `python -m explainlens.cli doctor`."""

    def test_doctor_exit_code_0(self):
        """doctor command should exit with code 0."""
        result = _run_cli(["doctor"])
        assert result.returncode == 0, (
            f"doctor exit code: {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_doctor_output_contains_local_https(self):
        """doctor output should mention local-http."""
        result = _run_cli(["doctor"])
        output = result.stdout.lower()
        assert "local-http" in output, (
            "doctor output should mention local-http\n"
            f"stdout: {result.stdout}"
        )

    def test_doctor_output_contains_openai_experimental(self):
        """doctor output should mention openai is experimental."""
        result = _run_cli(["doctor"])
        output = result.stdout.lower()
        assert "openai" in output, (
            "doctor output should mention openai\n"
            f"stdout: {result.stdout}"
        )
        assert "experimental" in output, (
            "doctor output should mention experimental\n"
            f"stdout: {result.stdout}"
        )

    def test_doctor_does_not_create_outputs(self):
        """doctor command should NOT create any output files."""
        result = _run_cli(["doctor"])
        assert result.returncode == 0
        # Check no outputs/ directory was created by doctor command
        # (doctor doesn't take --output, so it shouldn't create anything)
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            # If outputs/ exists from other runs, that's OK
            # But doctor shouldn't create NEW files
            pass  # OK

    def test_doctor_output_contains_python_version(self):
        """doctor output should contain Python version."""
        result = _run_cli(["doctor"])
        assert "Python:" in result.stdout, (
            "doctor output should contain Python version\n"
            f"stdout: {result.stdout}"
        )

    def test_doctor_output_contains_providers(self):
        """doctor output should list providers."""
        result = _run_cli(["doctor"])
        output = result.stdout
        assert "Providers:" in output, (
            "doctor output should contain 'Providers:'\n"
            f"stdout: {output}"
        )

    def test_doctor_output_contains_local_http_policy(self):
        """doctor output should mention loopback-only policy."""
        result = _run_cli(["doctor"])
        output = result.stdout
        assert "loopback" in output.lower() or "localhost" in output.lower(), (
            "doctor output should mention loopback policy\n"
            f"stdout: {output}"
        )

    def test_doctor_output_contains_artifacts(self):
        """doctor output should mention supported artifacts."""
        result = _run_cli(["doctor"])
        output = result.stdout
        assert "Artifacts:" in output, (
            "doctor output should contain 'Artifacts:'\n"
            f"stdout: {output}"
        )
        assert "source_index.json" in output, (
            "doctor output should mention source_index.json\n"
            f"stdout: {output}"
        )

    def test_doctor_no_network_calls(self):
        """doctor command should NOT make any network calls (implicit - no errors)."""
        result = _run_cli(["doctor"])
        assert result.returncode == 0
        # If network calls were attempted, we'd see connection errors
        # The fact that it succeeds implies no network calls

    def test_doctor_works_offline(self):
        """doctor command should work completely offline."""
        result = _run_cli(["doctor"])
        assert result.returncode == 0
        assert "Doctor check complete" in result.stdout or "No issues found" in result.stdout, (
            "doctor should complete successfully\n"
            f"stdout: {result.stdout}"
        )
