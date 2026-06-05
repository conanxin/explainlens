"""Tests for release preparation checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def test_prepare_release_script_exists():
    """scripts/prepare_release.py must exist."""
    assert (ROOT / "scripts" / "prepare_release.py").exists(), (
        "scripts/prepare_release.py not found"
    )


def test_prepare_release_script_not_single_line():
    """scripts/prepare_release.py must be multi-line."""
    lines = (ROOT / "scripts" / "prepare_release.py").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 30, (
        f"prepare_release.py looks too short ({len(lines)} lines)"
    )


def test_prepare_release_script_runnable():
    """scripts/prepare_release.py must run and exit with code 0."""
    result = subprocess.run(
        [PYTHON, str(ROOT / "scripts" / "prepare_release.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"prepare_release.py exited with code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_prepare_release_output_contains_pass():
    """scripts/prepare_release.py output must contain PASS."""
    result = subprocess.run(
        [PYTHON, str(ROOT / "scripts" / "prepare_release.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )
    assert "PASS" in result.stdout, (
        f"prepare_release.py output does not contain PASS.\n{result.stdout}"
    )


def test_changelog_contains_version():
    """CHANGELOG.md must contain v0.1.0-alpha."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "v0.1.0-alpha" in changelog, "CHANGELOG.md does not mention v0.1.0-alpha"


def test_release_notes_contain_quick_start():
    """Release notes must contain Quick Start section."""
    notes = (ROOT / "docs" / "releases" / "v0.1.0-alpha.md").read_text(encoding="utf-8")
    assert "Quick Start" in notes or "quick start" in notes.lower(), (
        "v0.1.0-alpha.md does not contain a Quick Start section"
    )


def test_release_notes_mention_safety_boundary():
    """Release notes must mention safety/boundary information."""
    notes = (ROOT / "docs" / "releases" / "v0.1.0-alpha.md").read_text(encoding="utf-8")
    assert "Safety" in notes or "safety" in notes.lower() or "API" in notes, (
        "v0.1.0-alpha.md should mention safety boundary"
    )
