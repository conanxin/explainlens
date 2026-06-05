"""Tests for PDF parsing and sample PDF generation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Test data
_EXAMPLES = ROOT / "examples"
_SAMPLE_PDF = _EXAMPLES / "sample_paper.pdf"
_CREATE_SCRIPT = ROOT / "scripts" / "create_sample_pdf.py"


def _python(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )


# ── Sample PDF generation ───────────────────────────────────────

def test_create_sample_pdf_script_exists():
    """scripts/create_sample_pdf.py must exist."""
    assert _CREATE_SCRIPT.is_file(), "create_sample_pdf.py not found"


def test_create_sample_pdf_generates_file():
    """Running create_sample_pdf.py must produce sample_paper.pdf."""
    result = _python(str(_CREATE_SCRIPT))
    assert result.returncode == 0, (
        f"create_sample_pdf.py failed: {result.stderr}"
    )
    assert _SAMPLE_PDF.is_file(), "sample_paper.pdf was not generated"


def test_sample_pdf_is_non_zero():
    """sample_paper.pdf must have non-zero size."""
    assert _SAMPLE_PDF.is_file(), "run test_create_sample_pdf_generates_file first"
    size = _SAMPLE_PDF.stat().st_size
    assert size > 100, f"sample_paper.pdf too small: {size} bytes"


# ── PDF parsing ──────────────────────────────────────────────────

def test_parse_pdf_returns_3_pages():
    """parse_pdf must return exactly 3 pages for sample_paper.pdf."""
    from explainlens.parser import parse_pdf
    assert _SAMPLE_PDF.is_file(), "run test_create_sample_pdf_generates_file first"
    text, pages = parse_pdf(str(_SAMPLE_PDF))
    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
    assert len(text) > 100, "Full text too short"


def test_pdf_page_text_non_empty():
    """Each page must have non-empty extracted text."""
    from explainlens.parser import parse_pdf
    assert _SAMPLE_PDF.is_file(), "run test_create_sample_pdf_generates_file first"
    _, pages = parse_pdf(str(_SAMPLE_PDF))
    for page in pages:
        assert page.text.strip(), f"Page {page.page_number} has empty text"
        assert page.char_start >= 0
        assert page.char_end > page.char_start


def test_parse_pdf_rejects_nonexistent():
    """parse_pdf must raise ParseError for nonexistent files."""
    from explainlens.parser import parse_pdf, ParseError
    with pytest.raises(ParseError):
        parse_pdf("nonexistent.pdf")


def test_parse_pdf_rejects_non_pdf():
    """parse_pdf must raise ParseError for non-PDF files."""
    from explainlens.parser import parse_pdf, ParseError
    sample_txt = _EXAMPLES / "sample_article.txt"
    assert sample_txt.is_file()
    with pytest.raises(ParseError):
        parse_pdf(str(sample_txt))


def test_detect_source_type():
    """detect_source_type must return correct types."""
    from explainlens.parser import detect_source_type
    assert detect_source_type("foo.txt") == "txt"
    assert detect_source_type("foo.md") == "md"
    assert detect_source_type("foo.markdown") == "md"
    assert detect_source_type("foo.pdf") == "pdf"
    assert detect_source_type("foo.unknown") == "txt"  # default
