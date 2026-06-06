"""Tests for image_manifest.json and image_jobs.json output."""

import json
from pathlib import Path

from explainlens.schemas import ImageCard
from explainlens.images.placeholder import PlaceholderImageAdapter
from explainlens.images.jobs import build_image_jobs, write_image_jobs
from explainlens.images.manifest import build_image_manifest, write_image_manifest


class TestImageJobs:
    """Tests for image_jobs.json generation."""

    @staticmethod
    def _make_cards(n=4):
        return [
            ImageCard(
                card_id=f"card_{(i + 1):02d}",
                title=f"Card {i + 1}",
                explanation=f"Explanation {i + 1}",
                image_prompt=f"Prompt {i + 1}",
                takeaway=f"Takeaway {i + 1}",
                source_chunk_ids=[f"chunk_{(i + 1):03d}"],
            )
            for i in range(n)
        ]

    def test_build_image_jobs_structure(self):
        cards = self._make_cards(4)
        jobs = build_image_jobs(cards, adapter="placeholder")

        assert jobs["adapter"] == "placeholder"
        assert jobs["style"] == "clean-cartoon-explainer"
        assert jobs["job_count"] == 4
        assert len(jobs["jobs"]) == 4

        for j in jobs["jobs"]:
            assert j["status"] == "pending"
            assert "job_id" in j
            assert "card_id" in j
            assert "title" in j
            assert "prompt" in j

    def test_build_image_jobs_skipped(self):
        cards = self._make_cards(4)
        jobs = build_image_jobs(cards, skipped=True)

        assert jobs["adapter"] is None
        assert jobs["style"] is None
        assert jobs["job_count"] == 4

        for j in jobs["jobs"]:
            assert j["status"] == "skipped"

    def test_write_image_jobs_creates_file(self, tmp_path):
        cards = self._make_cards(4)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        write_image_jobs(cards, output_dir)

        job_file = output_dir / "image_jobs.json"
        assert job_file.exists()

        data = json.loads(job_file.read_text())
        assert data["adapter"] == "placeholder"
        assert data["job_count"] == 4

    def test_write_image_jobs_skipped(self, tmp_path):
        cards = self._make_cards(4)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        write_image_jobs(cards, output_dir, skipped=True)

        data = json.loads((output_dir / "image_jobs.json").read_text())
        assert data["adapter"] is None
        for j in data["jobs"]:
            assert j["status"] == "skipped"


class TestImageManifest:
    """Tests for image_manifest.json generation."""

    def test_build_manifest_structure(self):
        records = [
            {
                "image_id": "image_001",
                "card_id": "card_01",
                "adapter": "placeholder",
                "status": "generated",
                "path": "images/card_01.svg",
                "prompt": "test prompt",
                "safety_notes": ["No external API calls"],
            }
        ]
        manifest = build_image_manifest(records)

        assert manifest["adapter"] == "placeholder"
        assert manifest["adapter_version"] == "placeholder-v0.1"
        assert manifest["uses_external_api"] is False
        assert manifest["requires_api_key"] is False
        assert manifest["image_count"] == 1
        assert len(manifest["images"]) == 1

    def test_manifest_uses_external_api_false(self):
        records = [
            {
                "image_id": "image_001",
                "card_id": "card_01",
                "adapter": "fixture",
                "status": "generated",
                "path": "images/card_01.svg",
                "prompt": "test",
                "safety_notes": [],
            }
        ]
        manifest = build_image_manifest(
            records,
            adapter="fixture",
            adapter_version="fixture-v0.1",
            uses_external_api=False,
            requires_api_key=False,
        )

        assert manifest["uses_external_api"] is False
        assert manifest["requires_api_key"] is False

    def test_write_manifest_creates_file(self, tmp_path):
        records = [
            {
                "image_id": "image_001",
                "card_id": "card_01",
                "adapter": "placeholder",
                "status": "generated",
                "path": "images/card_01.svg",
                "prompt": "test",
                "safety_notes": [],
            }
        ]
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        write_image_manifest(records, output_dir)

        manifest_file = output_dir / "image_manifest.json"
        assert manifest_file.exists()

        data = json.loads(manifest_file.read_text())
        assert data["uses_external_api"] is False
        assert data["image_count"] == 1

    def test_manifest_paths_are_relative(self, tmp_path):
        records = [
            {
                "image_id": "image_001",
                "card_id": "card_01",
                "adapter": "placeholder",
                "status": "generated",
                "path": "images/card_01.svg",
                "prompt": "test",
                "safety_notes": [],
            }
        ]
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        write_image_manifest(records, output_dir)

        data = json.loads((output_dir / "image_manifest.json").read_text())
        for img in data["images"]:
            p = img["path"]
            assert not p.startswith("/")
            assert not p.startswith("\\")
            assert ":" not in p  # no absolute Windows path

    def test_manifest_no_secrets(self, tmp_path):
        """image_manifest.json must not contain secrets or source excerpts."""
        records = [
            {
                "image_id": "image_001",
                "card_id": "card_01",
                "adapter": "placeholder",
                "status": "generated",
                "path": "images/card_01.svg",
                "prompt": "test prompt",
                "safety_notes": [],
            }
        ]
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        write_image_manifest(records, output_dir)

        raw = (output_dir / "image_manifest.json").read_text()
        assert "OPENAI_API_KEY" not in raw
        assert "sk-" not in raw
        assert "source_excerpt" not in raw
