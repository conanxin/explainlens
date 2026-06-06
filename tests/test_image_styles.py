"""Tests for image style presets."""

import pytest
from explainlens.images.styles import get_style, list_styles, STYLES, ImageStyle


class TestImageStyleRegistry:
    """Test that the style registry is correctly populated."""

    def test_registry_contains_four_styles(self):
        """The registry should contain exactly 4 styles."""
        assert len(STYLES) == 4
        expected = {
            "clean-cartoon-explainer",
            "whiteboard",
            "storybook",
            "technical-diagram",
        }
        assert set(STYLES.keys()) == expected

    def test_list_styles_returns_four(self):
        """list_styles() should return 4 entries."""
        result = list_styles()
        assert len(result) == 4

    def test_list_styles_has_name_and_description(self):
        """Each entry should have name and description."""
        for entry in list_styles():
            assert "name" in entry
            assert "description" in entry
            assert entry["name"] in STYLES


class TestGetStyle:
    """Test get_style() lookup."""

    def test_get_style_returns_image_style(self):
        """get_style should return an ImageStyle instance."""
        style = get_style("clean-cartoon-explainer")
        assert isinstance(style, ImageStyle)
        assert style.name == "clean-cartoon-explainer"

    def test_get_style_has_required_fields(self):
        """Each style should have all required fields."""
        for name in STYLES:
            style = get_style(name)
            assert style.background
            assert style.accent
            assert style.accent_light
            assert style.text_primary
            assert style.text_secondary
            assert style.card_badge_fill
            assert style.card_badge_text
            assert style.canvas_width == 960
            assert style.canvas_height == 540

    def test_unknown_style_raises_clear_error(self):
        """Unknown style should raise ValueError with available styles."""
        with pytest.raises(ValueError) as exc:
            get_style("nonexistent-style")
        msg = str(exc.value)
        assert "Unknown image style" in msg
        assert "Available styles" in msg
        for expected_name in STYLES:
            assert expected_name in msg


class TestStyleUniqueness:
    """Test that styles are visually distinct."""

    def test_all_styles_have_unique_backgrounds(self):
        """Each style should have a unique background color."""
        backgrounds = {s.background for s in STYLES.values()}
        assert len(backgrounds) == len(STYLES)

    def test_all_styles_have_unique_accents(self):
        """Each style should have a unique accent color."""
        accents = {s.accent for s in STYLES.values()}
        assert len(accents) == len(STYLES)
