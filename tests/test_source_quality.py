"""Tests for source quality metadata in run_summary.json."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import subprocess
import sys


def _run_cli(input_path: str, output_dir: str) -> int:
    """Run CLI analyze and return exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "explainlens.cli", "analyze",
         "--input", input_path, "--output", output_dir],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode


class TestSourceQualityInRunSummary:
    def test_run_summary_contains_source_quality(self):
        """run_summary.json must have source_quality field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_article.txt", str(out_dir))
            assert ret == 0

            summary_path = out_dir / "run_summary.json"
            assert summary_path.exists()

            data = json.loads(summary_path.read_text(encoding="utf-8"))
            assert "source_quality" in data
            sq = data["source_quality"]
            assert "empty_pages" in sq
            assert "short_chunks" in sq
            assert "long_chunks" in sq
            assert "has_page_aware_chunks" in sq
            assert "has_source_index" in sq

    def test_txt_source_quality_no_pages(self):
        """txt input should have has_page_aware_chunks=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_article.txt", str(out_dir))
            assert ret == 0

            data = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))
            assert data["source_quality"]["has_page_aware_chunks"] is False

    def test_pdf_source_quality_page_aware(self):
        """PDF input should have has_page_aware_chunks=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_paper.pdf", str(out_dir))
            assert ret == 0

            data = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))
            assert data["source_quality"]["has_page_aware_chunks"] is True


class TestSourceIndexGenerated:
    def test_txt_generates_source_index(self):
        """txt input must produce source_index.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_article.txt", str(out_dir))
            assert ret == 0

            si_path = out_dir / "source_index.json"
            assert si_path.exists()
            data = json.loads(si_path.read_text(encoding="utf-8"))
            assert data["input_type"] == "txt"
            assert "citations" in data
            assert "cards_by_chunk" in data

    def test_pdf_generates_source_index(self):
        """PDF input must produce source_index.json with chunks_by_page."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_paper.pdf", str(out_dir))
            assert ret == 0

            si_path = out_dir / "source_index.json"
            assert si_path.exists()
            data = json.loads(si_path.read_text(encoding="utf-8"))
            assert data["input_type"] == "pdf"
            assert len(data["chunks_by_page"]) > 0

    def test_every_card_chunk_in_source_index(self):
        """Every card's source_chunk_ids must appear in source_index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_paper.pdf", str(out_dir))
            assert ret == 0

            si = json.loads((out_dir / "source_index.json").read_text(encoding="utf-8"))
            cards_data = json.loads((out_dir / "cards.json").read_text(encoding="utf-8"))

            citation_chunk_ids = {c["chunk_id"] for c in si["citations"]}
            for card in cards_data:
                for cid in card["source_chunk_ids"]:
                    assert cid in citation_chunk_ids, (
                        f"Card {card['card_id']} references {cid} "
                        f"which is not in source_index citations"
                    )

    def test_pdf_source_index_structure_integration(self):
        """source_index.json from actual PDF run has expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_paper.pdf", str(out_dir))
            assert ret == 0

            si = json.loads((out_dir / "source_index.json").read_text(encoding="utf-8"))
            required_keys = [
                "input_type", "source_file", "page_count", "chunk_count",
                "chunks_by_page", "cards_by_chunk", "citations",
            ]
            for key in required_keys:
                assert key in si, f"Missing key '{key}' in source_index.json"


class TestPdfExistingTestsStillPass:
    def test_pdf_smoke_still_works(self):
        """Existing PDF smoke test still produces all expected outputs."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            ret = _run_cli("examples/sample_paper.pdf", str(out_dir))
            assert ret == 0

            # All expected output files must exist
            for fname in ["source_pages.json", "source_chunks.json", "cards.html",
                          "cards.md", "run_summary.json", "source_index.json"]:
                assert (out_dir / fname).exists(), f"Missing output: {fname}"
