"""Tests for image adapters, registry, and image generation."""

import json
import os
import sys
from pathlib import Path

import pytest

from explainlens.schemas import ImageCard
from explainlens.images.base import ImageAdapter
from explainlens.images.placeholder import PlaceholderImageAdapter
from explainlens.images.fixture import FixtureImageAdapter
from explainlens.images.registry import (
    AVAILABLE_IMAGE_ADAPTERS,
    get_image_adapter,
    list_image_adapters,
)


class TestImageRegistry:
    """Tests for image adapter registry."""

    def test_registry_contains_placeholder(self):
        assert "placeholder" in AVAILABLE_IMAGE_ADAPTERS

    def test_registry_contains_fixture(self):
        assert "fixture" in AVAILABLE_IMAGE_ADAPTERS

    def test_get_placeholder_adapter(self):
        adapter = get_image_adapter("placeholder")
        assert isinstance(adapter, PlaceholderImageAdapter)
        assert adapter.name == "placeholder"
        assert adapter.uses_external_api is False

    def test_get_fixture_adapter(self):
        adapter = get_image_adapter("fixture")
        assert isinstance(adapter, FixtureImageAdapter)
        assert adapter.name == "fixture"
        assert adapter.uses_external_api is False

    def test_unknown_adapter_raises_clear_error(self):
        with pytest.raises(ValueError, match="Unknown image adapter"):
            get_image_adapter("non-existent")

    def test_unknown_adapter_message_lists_available(self):
        with pytest.raises(ValueError, match="placeholder"):
            get_image_adapter("zzz")

    def test_list_image_adapters_returns_list(self):
        adapters = list_image_adapters()
        assert isinstance(adapters, list)
        assert len(adapters) >= 2

        names = [a["name"] for a in adapters]
        assert "placeholder" in names
        assert "fixture" in names

    def test_list_image_adapters_has_metadata(self):
        for adapter in list_image_adapters():
            assert "name" in adapter
            assert "version" in adapter
            assert "status" in adapter
            assert "uses_external_api" in adapter
            assert "requires_api_key" in adapter


class TestPlaceholderAdapter:
    """Tests for the placeholder image adapter."""

    @pytest.fixture
    def sample_cards(self):
        return [
            ImageCard(
                card_id=f"card_{(i + 1):02d}",
                title=f"Card {i + 1}",
                explanation=f"Explanation for card {i + 1}",
                image_prompt=f"A clean illustration of concept {i + 1}",
                takeaway=f"Takeaway {i + 1}",
                source_chunk_ids=[f"chunk_{(i + 1):03d}"],
            )
            for i in range(8)
        ]

    def test_placeholder_metadata(self):
        adapter = PlaceholderImageAdapter()
        assert adapter.name == "placeholder"
        assert adapter.version == "placeholder-v0.1"
        assert adapter.status == "available"
        assert adapter.uses_external_api is False
        assert adapter.requires_api_key is False

    def test_generate_images_creates_svgs(self, sample_cards, tmp_path):
        adapter = PlaceholderImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        # Verify records
        assert len(records) == 8

        # Verify images directory and files exist
        images_dir = output_dir / "images"
        assert images_dir.is_dir()

        for i in range(8):
            card_id = f"card_{(i + 1):02d}"
            svg_path = images_dir / f"{card_id}.svg"
            assert svg_path.exists(), f"Expected {svg_path} to exist"
            content = svg_path.read_text(encoding="utf-8")
            assert "<svg" in content
            assert "</svg>" in content
            # Should contain visual metaphor label (card title)
            assert f"Card {i + 1}" in content

    def test_generate_images_record_structure(self, sample_cards, tmp_path):
        adapter = PlaceholderImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        for rec in records:
            assert "image_id" in rec
            assert "card_id" in rec
            assert "adapter" in rec
            assert rec["adapter"] == "placeholder"
            assert "status" in rec
            assert rec["status"] == "generated"
            assert "path" in rec
            assert "prompt" in rec
            assert "safety_notes" in rec
            assert isinstance(rec["safety_notes"], list)
            assert "No external API calls" in rec["safety_notes"]

    def test_paths_are_relative(self, sample_cards, tmp_path):
        adapter = PlaceholderImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        for rec in records:
            path = rec["path"]
            # Should be relative (e.g., "images/card_01.svg"), no absolute prefix
            assert not path.startswith("/")
            assert not path.startswith("\\")
            assert not ":" in path  # no Windows drive letter
            assert path.startswith("images/")

    def test_images_not_contain_secrets(self, sample_cards, tmp_path):
        adapter = PlaceholderImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(sample_cards, output_dir)
        images_dir = output_dir / "images"

        for svg_file in images_dir.glob("*.svg"):
            content = svg_file.read_text(encoding="utf-8")
            assert "OPENAI_API_KEY" not in content
            assert "sk-" not in content
            # Source excerpts should not be in images
            assert "Explanation for" not in content


class TestFixtureAdapter:
    """Tests for the fixture image adapter."""

    @pytest.fixture
    def sample_cards(self):
        return [
            ImageCard(
                card_id=f"card_{(i + 1):02d}",
                title=f"Fixture Card {i + 1}",
                explanation=f"Fixture explanation for card {i + 1}",
                image_prompt=f"Fixture prompt for concept {i + 1}",
                takeaway=f"Fixture takeaway {i + 1}",
                source_chunk_ids=[f"chunk_{(i + 1):03d}"],
            )
            for i in range(8)
        ]

    def test_fixture_metadata(self):
        adapter = FixtureImageAdapter()
        assert adapter.name == "fixture"
        assert adapter.version == "fixture-v0.1"
        assert adapter.status == "experimental"
        assert adapter.uses_external_api is False
        assert adapter.requires_api_key is False

    def test_generate_images_creates_svgs(self, sample_cards, tmp_path):
        adapter = FixtureImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        assert len(records) == 8

        images_dir = output_dir / "images"
        assert images_dir.is_dir()

        for i in range(8):
            card_id = f"card_{(i + 1):02d}"
            svg_path = images_dir / f"{card_id}.svg"
            assert svg_path.exists()

    def test_fixture_is_deterministic(self, sample_cards, tmp_path):
        adapter = FixtureImageAdapter()
        output_dir1 = tmp_path / "run1"
        output_dir2 = tmp_path / "run2"
        output_dir1.mkdir()
        output_dir2.mkdir()

        adapter.generate_images(sample_cards, output_dir1)
        adapter.generate_images(sample_cards, output_dir2)

        for i in range(8):
            card_id = f"card_{(i + 1):02d}"
            content1 = (output_dir1 / "images" / f"{card_id}.svg").read_text(
                encoding="utf-8"
            )
            content2 = (output_dir2 / "images" / f"{card_id}.svg").read_text(
                encoding="utf-8"
            )
            assert content1 == content2, f"Fixture must be deterministic for {card_id}"

    def test_fixture_paths_are_relative(self, sample_cards, tmp_path):
        adapter = FixtureImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        for rec in records:
            assert rec["path"].startswith("images/")

    def test_fixture_no_external_api(self, sample_cards, tmp_path):
        adapter = FixtureImageAdapter()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(sample_cards, output_dir)

        for rec in records:
            assert "No external API calls" in rec["safety_notes"]
