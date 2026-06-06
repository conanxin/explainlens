"""Tests for image rendering in HTML and Markdown outputs."""

import json
from pathlib import Path

import pytest

from explainlens.schemas import ImageCard, SourceChunk
from explainlens.renderer import render_cards_html, create_cards_from_storyboard
from explainlens.exporters import export_cards_markdown
from explainlens.schemas import Storyboard, StoryboardPanel


def _make_storyboard(n=8):
    panels = []
    for i in range(n):
        panels.append(
            StoryboardPanel(
                panel_id=f"panel_{(i + 1):02d}",
                title=f"Panel {i + 1}",
                plain_explanation=f"Simple explanation for panel {i + 1}",
                visual_scene=f"Scene {i + 1}",
                takeaway=f"Takeaway {i + 1}",
                image_prompt=f"Prompt for panel {i + 1}",
                source_chunk_ids=[f"chunk_{(i + 1):03d}"],
            )
        )
    return Storyboard(panels=panels)


def _make_chunks(n=8):
    """Create mock SourceChunk objects matching the storyboard chunk IDs."""
    chunks = []
    for i in range(n):
        chunks.append(
            SourceChunk(
                chunk_id=f"chunk_{(i + 1):03d}",
                text=f"Sample text for chunk {i + 1}",
                start_char=i * 100,
                end_char=(i + 1) * 100,
            )
        )
    return chunks


class TestHTMLRendering:
    """Tests for HTML output with image adapter features."""

    def test_html_with_image_adapter_uses_img_tags(self):
        """When image_adapter is set, HTML should use <img> tags."""
        cards = create_cards_from_storyboard(_make_storyboard(8))
        html = render_cards_html(
            cards,
            input_title="test.txt",
            chunk_count=4,
            image_adapter="placeholder",
            uses_external_image_api=False,
        )
        assert '<img src="images/card_' in html

    def test_html_without_image_adapter_uses_inline_svg(self):
        """When image_adapter is None, HTML should use inline SVG."""
        cards = create_cards_from_storyboard(_make_storyboard(8))
        html = render_cards_html(
            cards,
            input_title="test.txt",
            chunk_count=4,
            image_adapter=None,
        )
        # Should have inline SVG from placeholders
        assert "<svg" in html
        # Should NOT have img tags with images/
        assert '<img src="images/' not in html

    def test_html_always_contains_source_appendix(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        # Test both with and without image adapter
        for image_adapter in [None, "placeholder"]:
            html = render_cards_html(
                cards,
                input_title="test.txt",
                chunk_count=2,
                image_adapter=image_adapter,
            )
            assert "Source Appendix" in html

    def test_html_footer_has_image_adapter_info(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        html = render_cards_html(
            cards,
            input_title="test.txt",
            chunk_count=2,
            image_adapter="placeholder",
            uses_external_image_api=False,
        )
        assert "Image adapter: placeholder" in html
        assert "External image API: no" in html

    def test_html_footer_no_image_adapter(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        html = render_cards_html(
            cards,
            input_title="test.txt",
            chunk_count=2,
            image_adapter=None,
        )
        assert "does not call external APIs" in html


class TestMarkdownRendering:
    """Tests for Markdown output with image adapter features."""

    def test_md_with_image_adapter_has_image_refs(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        md = export_cards_markdown(
            cards,
            image_adapter="placeholder",
            skip_images=False,
        )
        assert "images/card_" in md
        assert "Image adapter: placeholder" in md

    def test_md_skip_images_has_skip_message(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        md = export_cards_markdown(
            cards,
            skip_images=True,
        )
        assert "Image generation skipped" in md

    def test_md_no_adapter_no_extra_info(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        md = export_cards_markdown(cards)
        assert "Image adapter:" not in md
        assert "Image generation skipped" not in md

    def test_md_has_source_appendix(self):
        cards = create_cards_from_storyboard(_make_storyboard(4))
        chunks = _make_chunks(4)
        md = export_cards_markdown(cards, chunks=chunks, image_adapter="placeholder")
        assert "## Source Appendix" in md
