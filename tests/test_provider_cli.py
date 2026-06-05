"""Tests for CLI provider integration."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_TXT = PROJECT_ROOT / "examples" / "sample_article.txt"
SAMPLE_PDF = PROJECT_ROOT / "examples" / "sample_paper.pdf"


def _run_cli(input_path: str, output_dir: str, provider: str = "rule-based") -> subprocess.CompletedProcess:
    """Run the CLI as a subprocess with an optional provider."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "explainlens.cli", "analyze",
         "--input", input_path, "--output", output_dir,
         "--provider", provider],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(PROJECT_ROOT),
    )


class TestCLIDefaultProvider:
    """Tests for default provider behavior."""

    def test_default_provider_is_rule_based(self, tmp_path: Path):
        """CLI without --provider should use rule-based by default."""
        output_dir = tmp_path / "default_provider"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir))
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"

        # Check run_summary
        with open(output_dir / "run_summary.json", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["provider"] == "rule-based"
        assert summary["provider_version"] == "rule-based-v0.1"
        assert summary["uses_external_api"] is False

    def test_cli_output_shows_provider_info(self, tmp_path: Path):
        """CLI stdout should show provider info."""
        output_dir = tmp_path / "provider_info"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir))
        assert result.returncode == 0
        assert "Provider:" in result.stdout


class TestCLIMockLLMProvider:
    """Tests for mock-llm provider via CLI."""

    def test_mock_llm_runs_text_complete(self, tmp_path: Path):
        """mock-llm provider should complete txt analysis successfully."""
        output_dir = tmp_path / "mock_text"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0, (
            f"mock-llm CLI failed:\n{result.stderr}\n{result.stdout}"
        )

    def test_mock_llm_produces_all_output_files(self, tmp_path: Path):
        """mock-llm should produce all expected output files."""
        output_dir = tmp_path / "mock_files"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        expected_files = [
            "source_chunks.json",
            "source_index.json",
            "concept_map.json",
            "teaching_plan.json",
            "storyboard.json",
            "image_prompts.json",
            "cards.json",
            "cards.md",
            "cards.html",
            "run_summary.json",
        ]
        for fname in expected_files:
            assert (output_dir / fname).exists(), f"Missing: {fname}"

    def test_mock_llm_run_summary_metadata(self, tmp_path: Path):
        """run_summary.json should include provider metadata."""
        output_dir = tmp_path / "mock_meta"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        with open(output_dir / "run_summary.json", encoding="utf-8") as f:
            summary = json.load(f)

        assert summary["provider"] == "mock-llm"
        assert summary["provider_version"] == "mock-llm-v0.1"
        assert summary["uses_external_api"] is False

    def test_mock_llm_source_index_exists(self, tmp_path: Path):
        """source_index.json should exist with mock-llm."""
        output_dir = tmp_path / "mock_si"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        with open(output_dir / "source_index.json", encoding="utf-8") as f:
            si = json.load(f)
        assert "citations" in si
        assert "cards_by_chunk" in si

    def test_mock_llm_html_has_source_appendix(self, tmp_path: Path):
        """cards.html should contain Source Appendix with mock-llm."""
        output_dir = tmp_path / "mock_html"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        with open(output_dir / "cards.html", encoding="utf-8") as f:
            html = f.read()
        assert "Source Appendix" in html, "cards.html should have Source Appendix"
        assert "source-chunk_" in html, "cards.html should have source-chunk anchors"

    def test_mock_llm_8_cards(self, tmp_path: Path):
        """mock-llm should produce exactly 8 cards."""
        output_dir = tmp_path / "mock_eight"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        with open(output_dir / "cards.json", encoding="utf-8") as f:
            cards = json.load(f)
        assert len(cards) == 8
        for card in cards:
            assert len(card["source_chunk_ids"]) >= 1, (
                f"Card {card['card_id']} should have source_chunk_ids"
            )


class TestCLIRuleBasedProvider:
    """Tests that rule-based provider still works via CLI --provider flag."""

    def test_explicit_rule_based_runs(self, tmp_path: Path):
        """Explicit --provider rule-based should work."""
        output_dir = tmp_path / "explicit_rb"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="rule-based")
        assert result.returncode == 0

    def test_explicit_rule_based_summary(self, tmp_path: Path):
        """run_summary should show rule-based metadata."""
        output_dir = tmp_path / "rb_meta"
        result = _run_cli(str(SAMPLE_TXT), str(output_dir), provider="rule-based")
        assert result.returncode == 0

        with open(output_dir / "run_summary.json", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["provider"] == "rule-based"
        assert summary["provider_version"] == "rule-based-v0.1"
        assert summary["uses_external_api"] is False


class TestCLIMockLLMPDF:
    """Tests for mock-llm with PDF input (requires generated sample PDF)."""

    @pytest.mark.skipif(
        not SAMPLE_PDF.exists(),
        reason="sample_paper.pdf not found — run scripts/create_sample_pdf.py first",
    )
    def test_mock_llm_runs_pdf_complete(self, tmp_path: Path):
        """mock-llm provider should complete PDF analysis successfully."""
        output_dir = tmp_path / "mock_pdf"
        result = _run_cli(str(SAMPLE_PDF), str(output_dir), provider="mock-llm")
        assert result.returncode == 0, (
            f"mock-llm PDF CLI failed:\n{result.stderr}\n{result.stdout}"
        )

    @pytest.mark.skipif(
        not SAMPLE_PDF.exists(),
        reason="sample_paper.pdf not found — run scripts/create_sample_pdf.py first",
    )
    def test_mock_llm_pdf_has_source_pages(self, tmp_path: Path):
        """PDF with mock-llm should produce source_pages.json."""
        output_dir = tmp_path / "mock_pdf_sp"
        result = _run_cli(str(SAMPLE_PDF), str(output_dir), provider="mock-llm")
        assert result.returncode == 0
        assert (output_dir / "source_pages.json").exists()

    @pytest.mark.skipif(
        not SAMPLE_PDF.exists(),
        reason="sample_paper.pdf not found — run scripts/create_sample_pdf.py first",
    )
    def test_mock_llm_pdf_source_index(self, tmp_path: Path):
        """PDF with mock-llm should produce source_index.json."""
        output_dir = tmp_path / "mock_pdf_si"
        result = _run_cli(str(SAMPLE_PDF), str(output_dir), provider="mock-llm")
        assert result.returncode == 0

        with open(output_dir / "source_index.json", encoding="utf-8") as f:
            si = json.load(f)
        assert "chunks_by_page" in si, "PDF source_index should have chunks_by_page"
