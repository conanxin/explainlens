"""Tests for CLI entry point."""

import os
import sys
import json
import subprocess
from pathlib import Path
import pytest


# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = PROJECT_ROOT / "examples" / "sample_article.txt"


def _run_cli(input_path: str, output_dir: str) -> subprocess.CompletedProcess:
    """Run the CLI as a subprocess."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "explainlens.cli", "analyze",
         "--input", input_path, "--output", output_dir],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(PROJECT_ROOT),
    )


def test_cli_runs_with_sample_article(tmp_path: Path):
    """CLI should complete successfully with the sample article."""
    output_dir = tmp_path / "test_output"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0, f"CLI failed:\n{result.stderr}\n{result.stdout}"


def test_cli_produces_source_chunks(tmp_path: Path):
    """CLI should produce source_chunks.json."""
    output_dir = tmp_path / "test_output2"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    chunks_path = output_dir / "source_chunks.json"
    assert chunks_path.exists(), "source_chunks.json not created"
    with open(chunks_path, encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) > 0, "source_chunks.json is empty"


def test_cli_produces_concept_map(tmp_path: Path):
    """CLI should produce concept_map.json."""
    output_dir = tmp_path / "test_output3"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    cm_path = output_dir / "concept_map.json"
    assert cm_path.exists()
    with open(cm_path, encoding="utf-8") as f:
        data = json.load(f)
        assert "core_problem" in data


def test_cli_produces_teaching_plan(tmp_path: Path):
    """CLI should produce teaching_plan.json with 8 steps."""
    output_dir = tmp_path / "test_output4"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    tp_path = output_dir / "teaching_plan.json"
    assert tp_path.exists()
    with open(tp_path, encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["steps"]) == 8


def test_cli_produces_storyboard(tmp_path: Path):
    """CLI should produce storyboard.json with 8 panels."""
    output_dir = tmp_path / "test_output5"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    sb_path = output_dir / "storyboard.json"
    assert sb_path.exists()
    with open(sb_path, encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["panels"]) == 8


def test_cli_produces_image_prompts(tmp_path: Path):
    """CLI should produce non-empty image_prompts.json."""
    output_dir = tmp_path / "test_output6"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    ip_path = output_dir / "image_prompts.json"
    assert ip_path.exists()
    with open(ip_path, encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) > 0, "image_prompts.json should not be empty"
        for item in data:
            assert item.get("prompt"), "Each prompt entry should have a prompt field"


def test_cli_produces_cards_json(tmp_path: Path):
    """CLI should produce cards.json."""
    output_dir = tmp_path / "test_output7"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    cj_path = output_dir / "cards.json"
    assert cj_path.exists()
    with open(cj_path, encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 8


def test_cli_produces_cards_html(tmp_path: Path):
    """CLI should produce cards.html that contains ExplainLens."""
    output_dir = tmp_path / "test_output8"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    ch_path = output_dir / "cards.html"
    assert ch_path.exists()
    with open(ch_path, encoding="utf-8") as f:
        content = f.read()
        assert "ExplainLens" in content


def test_cli_produces_cards_md(tmp_path: Path):
    """CLI should produce cards.md."""
    output_dir = tmp_path / "test_output9"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    md_path = output_dir / "cards.md"
    assert md_path.exists()


def test_cli_produces_run_summary(tmp_path: Path):
    """CLI should produce run_summary.json."""
    output_dir = tmp_path / "test_output10"
    result = _run_cli(str(SAMPLE_FILE), str(output_dir))
    assert result.returncode == 0
    rs_path = output_dir / "run_summary.json"
    assert rs_path.exists()
    with open(rs_path, encoding="utf-8") as f:
        data = json.load(f)
        assert data["chunk_count"] > 0
        assert data["card_count"] == 8
        assert len(data["output_files"]) > 0
