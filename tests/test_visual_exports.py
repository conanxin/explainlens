"""Tests for visual export quality — SVG, HTML, Markdown."""

import json
import re
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from explainlens.images.placeholder import PlaceholderImageAdapter
from explainlens.images.fixture import FixtureImageAdapter
from explainlens.images.styles import get_style
from explainlens.schemas import ImageCard


# ── Helpers ────────────────────────────────────────────────────

def _make_card(idx: int, title: str = None) -> ImageCard:
    return ImageCard(
        card_id=f"card_{idx:02d}",
        title=title or f"Test Card {idx}",
        explanation=f"Explanation for card {idx}.",
        image_prompt=f"Prompt for card {idx}.",
        takeaway=f"Takeaway from card {idx}.",
        source_chunk_ids=[f"chunk_{idx:03d}"],
    )


# ── SVG Tests ──────────────────────────────────────────────────

class TestPlaceholderSVG:
    """Test placeholder adapter SVG generation."""

    def test_placeholder_respects_style(self, tmp_path):
        """Placeholder adapter should use the specified style."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1), _make_card(2)]
        records = adapter.generate_images(cards, tmp_path, style="whiteboard")

        svg_path = tmp_path / "images" / "card_01.svg"
        assert svg_path.is_file()
        svg = svg_path.read_text()
        style = get_style("whiteboard")
        assert style.background in svg

    def test_placeholder_svg_size_consistent(self, tmp_path):
        """All generated SVGs should have viewBox 0 0 960 540."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(i) for i in range(1, 5)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        for i in range(1, 5):
            svg = (tmp_path / "images" / f"card_{i:02d}.svg").read_text()
            assert 'viewBox="0 0 960 540"' in svg

    def test_placeholder_svg_no_source_excerpt(self, tmp_path):
        """SVGs should not contain source excerpts."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        svg = (tmp_path / "images" / "card_01.svg").read_text()
        assert "source excerpt" not in svg.lower()
        assert "Explanation for card" not in svg

    def test_placeholder_svg_no_api_key(self, tmp_path):
        """SVGs should not contain API keys."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        svg = (tmp_path / "images" / "card_01.svg").read_text()
        assert "OPENAI_API_KEY" not in svg
        assert "sk-" not in svg

    def test_placeholder_svg_has_explainlens_header(self, tmp_path):
        """SVGs should have ExplainLens badge."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        svg = (tmp_path / "images" / "card_01.svg").read_text()
        assert "ExplainLens" in svg

    def test_placeholder_svg_has_footer(self, tmp_path):
        """SVGs should have the 'no external image API' footer."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        svg = (tmp_path / "images" / "card_01.svg").read_text()
        assert "Generated locally" in svg
        assert "no external image API" in svg

    def test_placeholder_unknown_style_raises(self, tmp_path):
        """Unknown style should raise ValueError."""
        adapter = PlaceholderImageAdapter()
        cards = [_make_card(1)]
        with pytest.raises(ValueError) as exc:
            adapter.generate_images(cards, tmp_path, style="bad-style")
        assert "Unknown image style" in str(exc.value)


class TestFixtureSVG:
    """Test fixture adapter SVG generation."""

    def test_fixture_respects_style(self, tmp_path):
        """Fixture adapter should use the specified style."""
        adapter = FixtureImageAdapter()
        cards = [_make_card(1)]
        records = adapter.generate_images(cards, tmp_path, style="storybook")

        svg_path = tmp_path / "images" / "card_01.svg"
        assert svg_path.is_file()
        svg = svg_path.read_text()
        style = get_style("storybook")
        assert style.background in svg

    def test_fixture_svg_size_consistent(self, tmp_path):
        """All fixture SVGs should have viewBox 0 0 960 540."""
        adapter = FixtureImageAdapter()
        cards = [_make_card(i) for i in range(1, 5)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        for i in range(1, 5):
            svg = (tmp_path / "images" / f"card_{i:02d}.svg").read_text()
            assert 'viewBox="0 0 960 540"' in svg

    def test_fixture_svg_no_api_key(self, tmp_path):
        """Fixture SVGs should not contain API keys."""
        adapter = FixtureImageAdapter()
        cards = [_make_card(1)]
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")

        svg = (tmp_path / "images" / "card_01.svg").read_text()
        assert "OPENAI_API_KEY" not in svg
        assert "sk-" not in svg

    def test_fixture_svg_deterministic(self, tmp_path):
        """Fixture adapter should produce identical output every run."""
        adapter = FixtureImageAdapter()
        cards = [_make_card(1), _make_card(2)]

        # Run twice
        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")
        svg1 = (tmp_path / "images" / "card_01.svg").read_text()

        adapter.generate_images(cards, tmp_path, style="clean-cartoon-explainer")
        svg2 = (tmp_path / "images" / "card_01.svg").read_text()

        assert svg1 == svg2


# ── CLI Tests ──────────────────────────────────────────────────

class TestImageStylesCLI:
    """Test the image-styles CLI command."""

    def test_cli_image_styles_lists_all(self):
        """image-styles CLI should list all 4 styles."""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "explainlens.cli", "image-styles"],
            capture_output=True, text=True, timeout=30,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        for style in ["clean-cartoon-explainer", "whiteboard", "storybook", "technical-diagram"]:
            assert style in result.stdout

    def test_cli_unknown_style_fails(self):
        """Using unknown style in analyze should fail."""
        import subprocess
        import sys
        result = subprocess.run(
            [
                sys.executable, "-m", "explainlens.cli", "analyze",
                "--input", "examples/sample_article.txt",
                "--output", "outputs/test_bad_style",
                "--image-style", "nonexistent-style",
            ],
            capture_output=True, text=True, timeout=30,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode != 0
        assert "Unknown image style" in result.stderr
