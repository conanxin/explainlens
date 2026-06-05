"""Tests for demo assets and documentation files."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_demo_md_exists():
    """docs/DEMO.md must exist."""
    assert (ROOT / "docs" / "DEMO.md").exists(), "docs/DEMO.md not found"


def test_demo_preview_svg_exists():
    """docs/assets/demo-preview.svg must exist."""
    assert (ROOT / "docs" / "assets" / "demo-preview.svg").exists(), (
        "docs/assets/demo-preview.svg not found"
    )


def test_demo_preview_svg_is_valid_svg():
    """docs/assets/demo-preview.svg must start with <svg."""
    content = (ROOT / "docs" / "assets" / "demo-preview.svg").read_text(encoding="utf-8").strip()
    assert content.startswith("<svg"), "demo-preview.svg does not start with <svg"


def test_release_notes_exist():
    """docs/releases/v0.1.0-alpha.md must exist."""
    assert (ROOT / "docs" / "releases" / "v0.1.0-alpha.md").exists(), (
        "docs/releases/v0.1.0-alpha.md not found"
    )


def test_readme_references_demo_md():
    """README.md must contain a reference to docs/DEMO.md."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/DEMO.md" in readme, "README.md does not reference docs/DEMO.md"


def test_sample_ai_research_note_exists():
    """examples/sample_ai_research_note.txt must exist."""
    assert (ROOT / "examples" / "sample_ai_research_note.txt").exists(), (
        "examples/sample_ai_research_note.txt not found"
    )


def test_sample_ai_research_note_length():
    """AI research note example should be at least 1000 characters."""
    content = (ROOT / "examples" / "sample_ai_research_note.txt").read_text(encoding="utf-8")
    assert len(content) >= 1000, (
        f"sample_ai_research_note.txt too short: {len(content)} chars"
    )
