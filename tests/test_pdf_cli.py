"""Tests for CLI with PDF input."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "-m", "explainlens.cli", "analyze", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )


def test_cli_pdf_sample_generates_source_pages():
    """CLI with PDF input must generate source_pages.json."""
    result = _cli(
        "--input", "examples/sample_paper.pdf",
        "--output", "outputs/test_pdf_cli_source_pages",
    )
    sp = ROOT / "outputs" / "test_pdf_cli_source_pages" / "source_pages.json"
    assert sp.is_file(), f"source_pages.json not found. stderr: {result.stderr}"


def test_cli_pdf_source_pages_has_3_entries():
    """source_pages.json must contain exactly 3 pages."""
    sp = ROOT / "outputs" / "test_pdf_cli_source_pages" / "source_pages.json"
    data = json.loads(sp.read_text(encoding="utf-8"))
    assert len(data) == 3, f"Expected 3 pages, got {len(data)}"
    for entry in data:
        assert "page_number" in entry
        assert "text" in entry
        assert "char_start" in entry
        assert "char_end" in entry


def test_cli_pdf_generates_cards_html():
    """CLI with PDF input must generate cards.html."""
    result = _cli(
        "--input", "examples/sample_paper.pdf",
        "--output", "outputs/test_pdf_cli_cards",
    )
    html = ROOT / "outputs" / "test_pdf_cli_cards" / "cards.html"
    assert html.is_file(), f"cards.html not found. stderr: {result.stderr}"
    content = html.read_text(encoding="utf-8")
    assert "<html" in content.lower()


def test_cli_pdf_generates_run_summary():
    """CLI with PDF must produce run_summary.json with PDF fields."""
    result = _cli(
        "--input", "examples/sample_paper.pdf",
        "--output", "outputs/test_pdf_cli_summary",
    )
    rs = ROOT / "outputs" / "test_pdf_cli_summary" / "run_summary.json"
    assert rs.is_file(), f"run_summary.json not found. stderr: {result.stderr}"
    data = json.loads(rs.read_text(encoding="utf-8"))
    assert data["input_type"] == "pdf"
    assert data["page_count"] == 3
    assert data["extraction_method"] == "pymupdf"
    assert "source_pages.json" in data["output_files"]


def test_cli_pdf_html_contains_page_info():
    """HTML output must reference page numbers for PDF input."""
    _cli(
        "--input", "examples/sample_paper.pdf",
        "--output", "outputs/test_pdf_cli_pageinfo",
    )
    html = ROOT / "outputs" / "test_pdf_cli_pageinfo" / "cards.html"
    content = html.read_text(encoding="utf-8")
    # At least one card's source excerpt should mention a page number
    # (page info is in the Source Excerpt details summary)
    assert "page" in content.lower(), "HTML should reference page numbers"


def test_cli_pdf_source_chunks_have_page_fields():
    """source_chunks.json for PDF must have page fields."""
    _cli(
        "--input", "examples/sample_paper.pdf",
        "--output", "outputs/test_pdf_cli_chunks",
    )
    sc = ROOT / "outputs" / "test_pdf_cli_chunks" / "source_chunks.json"
    data = json.loads(sc.read_text(encoding="utf-8"))
    assert len(data) > 0, "No chunks produced"
    for chunk in data:
        assert chunk["source_type"] == "pdf"
        # page_start/page_end may be null for empty pages, but at least
        # one chunk should have page info
    has_page = any(
        c.get("page_start") is not None and c.get("page_end") is not None
        for c in data
    )
    assert has_page, "No chunks have page_start/page_end"


def test_cli_txt_still_works():
    """TXT input must still work after PDF changes."""
    result = _cli(
        "--input", "examples/sample_article.txt",
        "--output", "outputs/test_pdf_cli_txt_smoke",
    )
    assert result.returncode == 0, f"TXT CLI failed: {result.stderr}"
    html = ROOT / "outputs" / "test_pdf_cli_txt_smoke" / "cards.html"
    assert html.is_file()
    rs = ROOT / "outputs" / "test_pdf_cli_txt_smoke" / "run_summary.json"
    data = json.loads(rs.read_text(encoding="utf-8"))
    assert data["input_type"] in ("txt", "md")


def test_cli_rejects_scanned_pdf_like_error():
    """Empty-text PDF must produce a clear error."""
    # We test this by creating a minimal empty-scanned-like PDF
    # and verifying the parse error message is clear.
    import fitz
    empty_path = ROOT / "outputs" / "__test_empty.pdf"
    empty_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    # Add a page with no text content (like a scanned page)
    page = doc.new_page(width=100, height=100)
    # Insert an image-like rectangle with no text
    page.draw_rect(fitz.Rect(10, 10, 90, 90), color=(0.8, 0.8, 0.8), fill=(0.8, 0.8, 0.8))
    doc.save(str(empty_path))
    doc.close()

    try:
        from explainlens.parser import parse_pdf, ParseError
        with __import__("pytest").raises(ParseError) as exc_info:
            parse_pdf(str(empty_path))
        assert "No extractable text" in str(exc_info.value), (
            f"Expected 'No extractable text' in error, got: {exc_info.value}"
        )
    finally:
        empty_path.unlink(missing_ok=True)
