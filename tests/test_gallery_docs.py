"""Tests for gallery documentation and demo assets."""

import json
from pathlib import Path
import pytest


PROJECT_ROOT = Path(__file__).parent.parent


class TestGalleryDocs:
    """Test that gallery documentation and references are correct."""

    def test_gallery_md_exists(self):
        """docs/GALLERY.md should exist."""
        assert (PROJECT_ROOT / "docs" / "GALLERY.md").is_file()

    def test_readme_links_gallery(self):
        """README.md should link to docs/GALLERY.md."""
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        assert "docs/GALLERY.md" in readme

    def test_demo_preview_svg_exists(self):
        """docs/assets/demo-preview.svg should exist."""
        assert (PROJECT_ROOT / "docs" / "assets" / "demo-preview.svg").is_file()

    def test_demo_preview_svg_is_valid(self):
        """demo-preview.svg should be valid SVG."""
        svg_path = PROJECT_ROOT / "docs" / "assets" / "demo-preview.svg"
        svg = svg_path.read_text(encoding="utf-8")
        assert "<svg" in svg
        assert "</svg>" in svg
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_demo_preview_has_v0_2(self):
        """demo-preview.svg should mention v0.2.x."""
        svg = (PROJECT_ROOT / "docs" / "assets" / "demo-preview.svg").read_text(encoding="utf-8")
        assert "v0.2" in svg

    def test_demo_preview_has_image_adapter(self):
        """demo-preview.svg should mention Image Adapter."""
        svg = (PROJECT_ROOT / "docs" / "assets" / "demo-preview.svg").read_text(encoding="utf-8")
        assert "Image Adapter" in svg or "Image" in svg

    def test_gallery_mentions_all_styles(self):
        """GALLERY.md should mention all 4 styles."""
        gallery = (PROJECT_ROOT / "docs" / "GALLERY.md").read_text(encoding="utf-8")
        for style in ["clean-cartoon-explainer", "whiteboard", "storybook", "technical-diagram"]:
            assert style in gallery

    def test_gallery_mentions_no_external_api(self):
        """GALLERY.md should state no external image APIs."""
        gallery = (PROJECT_ROOT / "docs" / "GALLERY.md").read_text(encoding="utf-8")
        # Accept both singular and plural forms, case-insensitive
        assert "no external image api" in gallery.lower().replace("apis", "api")

    def test_gallery_mentions_skip_images(self):
        """GALLERY.md should mention --skip-images."""
        gallery = (PROJECT_ROOT / "docs" / "GALLERY.md").read_text(encoding="utf-8")
        assert "--skip-images" in gallery
