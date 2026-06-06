"""Tests for image adapter CLI integration."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _python():
    return sys.executable


def _run_cli(args, cwd=None, env=None):
    """Run CLI and return (returncode, stdout, stderr)."""
    cmd = [_python(), "-m", "explainlens.cli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env or os.environ.copy(),
    )
    return result.returncode, result.stdout, result.stderr


class TestImageAdaptersCLI:
    """Tests for image-adapters CLI subcommand."""

    def test_image_adapters_command_runs(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        assert rc == 0
        assert "placeholder" in stdout
        assert "fixture" in stdout

    def test_image_adapters_shows_available(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        assert "available" in stdout
        assert "experimental" in stdout

    def test_image_adapters_shows_external_api_no(self):
        rc, stdout, stderr = _run_cli(["image-adapters"])
        assert "External API: no" in stdout


class TestAnalyzeImageCLI:
    """Tests for analyze --image-adapter, --skip-images CLI options."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp = tmp_path
        self.input_file = Path("examples/sample_article.txt")
        if not self.input_file.exists():
            pytest.skip("examples/sample_article.txt not found")

    def test_default_generates_image_manifest(self):
        output_dir = self.tmp / "default_image"
        rc, stdout, stderr = _run_cli(
            ["analyze", "--input", str(self.input_file), "--output", str(output_dir)]
        )
        assert rc == 0

        manifest = output_dir / "image_manifest.json"
        assert manifest.exists(), "Default should generate image_manifest.json"

        data = json.loads(manifest.read_text())
        assert data["uses_external_api"] is False
        assert data["image_count"] > 0
        assert data["adapter"] == "placeholder"

    def test_default_generates_image_jobs(self):
        output_dir = self.tmp / "default_image_jobs"
        rc, stdout, stderr = _run_cli(
            ["analyze", "--input", str(self.input_file), "--output", str(output_dir)]
        )
        assert rc == 0

        jobs = output_dir / "image_jobs.json"
        assert jobs.exists()

        data = json.loads(jobs.read_text())
        assert data["adapter"] == "placeholder"

    def test_image_adapter_fixture(self):
        output_dir = self.tmp / "fixture_image"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
                "--image-adapter", "fixture",
            ]
        )
        assert rc == 0

        manifest = output_dir / "image_manifest.json"
        assert manifest.exists()

        data = json.loads(manifest.read_text())
        assert data["adapter"] == "fixture"

    def test_skip_images_no_manifest(self):
        output_dir = self.tmp / "skip_image"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
                "--skip-images",
            ]
        )
        assert rc == 0

        # image_manifest.json should NOT exist
        assert not (output_dir / "image_manifest.json").exists()

    def test_skip_images_still_has_jobs(self):
        output_dir = self.tmp / "skip_jobs"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
                "--skip-images",
            ]
        )
        assert rc == 0

        # image_jobs.json should still exist (with skipped status)
        jobs = output_dir / "image_jobs.json"
        assert jobs.exists()

        data = json.loads(jobs.read_text())
        assert data["adapter"] is None
        for j in data["jobs"]:
            assert j["status"] == "skipped"

    def test_html_uses_img_tags(self):
        """When image adapter is active, cards.html should use <img> tags."""
        output_dir = self.tmp / "html_img_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
            ]
        )
        assert rc == 0

        html = (output_dir / "cards.html").read_text(encoding="utf-8")
        assert '<img src="images/card_' in html

    def test_html_contains_source_appendix(self):
        """cards.html must still include Source Appendix."""
        output_dir = self.tmp / "html_appendix_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
            ]
        )
        assert rc == 0

        html = (output_dir / "cards.html").read_text(encoding="utf-8")
        assert "Source Appendix" in html

    def test_markdown_has_image_refs(self):
        """When image adapter is active, cards.md should have image references."""
        output_dir = self.tmp / "md_image_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
            ]
        )
        assert rc == 0

        md = (output_dir / "cards.md").read_text(encoding="utf-8")
        assert "images/card_" in md
        assert "**Adapter:**" in md
        assert "`placeholder`" in md

    def test_markdown_skip_images(self):
        """When --skip-images, cards.md should show skip message."""
        output_dir = self.tmp / "md_skip_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
                "--skip-images",
            ]
        )
        assert rc == 0

        md = (output_dir / "cards.md").read_text(encoding="utf-8")
        assert "Image generation skipped" in md

    def test_run_summary_has_image_adapter(self):
        output_dir = self.tmp / "summary_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
            ]
        )
        assert rc == 0

        summary = json.loads((output_dir / "run_summary.json").read_text())
        assert summary["image_adapter"] == "placeholder"
        assert summary["image_count"] > 0
        assert summary["uses_external_image_api"] is False

    def test_run_summary_skip_images(self):
        output_dir = self.tmp / "summary_skip_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
                "--skip-images",
            ]
        )
        assert rc == 0

        summary = json.loads((output_dir / "run_summary.json").read_text())
        assert summary["image_adapter"] is None
        assert summary["image_count"] == 0
        assert summary["uses_external_image_api"] is False

    def test_images_directory_has_svgs(self):
        output_dir = self.tmp / "image_files_test"
        rc, stdout, stderr = _run_cli(
            [
                "analyze",
                "--input", str(self.input_file),
                "--output", str(output_dir),
            ]
        )
        assert rc == 0

        images_dir = output_dir / "images"
        assert images_dir.is_dir()

        svgs = list(images_dir.glob("*.svg"))
        assert len(svgs) > 0
        for svg in svgs:
            content = svg.read_text(encoding="utf-8")
            assert "<svg" in content
            assert "</svg>" in content
            # No secrets
            assert "OPENAI_API_KEY" not in content
            assert "sk-" not in content
