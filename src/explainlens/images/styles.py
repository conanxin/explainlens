"""Image style presets for ExplainLens.

Defines visual style profiles that affect SVG image generation across
all adapters.  Each style controls background, accent, layout, and
typography parameters.

Usage:
    from explainlens.images.styles import get_style, list_styles, STYLES
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ImageStyle:
    """Visual style profile for image generation."""

    name: str
    description: str
    background: str          # CSS bg / gradient
    accent: str              # Primary accent color
    accent_light: str        # Light variant of accent
    text_primary: str        # Primary text color
    text_secondary: str      # Secondary text color
    card_badge_fill: str     # Top badge background
    card_badge_text: str     # Top badge text color
    canvas_width: int = 960
    canvas_height: int = 540
    aspect_ratio: str = "16:9"
    font_family: str = "system-ui, -apple-system, sans-serif"
    title_size: int = 18
    body_size: int = 13
    small_size: int = 10
    visual_motif: str = ""   # Description of visual motif


# ── Style definitions ──────────────────────────────────────────

STYLES: Dict[str, ImageStyle] = {
    "clean-cartoon-explainer": ImageStyle(
        name="clean-cartoon-explainer",
        description="Clean cartoon-style illustrations for scientific and technical concepts.",
        background="#eef2ff",
        accent="#4f6ef7",
        accent_light="#c7d2fe",
        text_primary="#3730a3",
        text_secondary="#6366f1",
        card_badge_fill="#4f6ef7",
        card_badge_text="#ffffff",
        visual_motif="simple geometric shapes, rounded rectangles, clean lines",
    ),
    "whiteboard": ImageStyle(
        name="whiteboard",
        description="Whiteboard sketch style — hand-drawn feel with marker-style lines.",
        background="#fafaf9",
        accent="#334155",
        accent_light="#e2e8f0",
        text_primary="#1e293b",
        text_secondary="#475569",
        card_badge_fill="#334155",
        card_badge_text="#ffffff",
        visual_motif="sketch lines, hand-drawn shapes, marker annotations",
    ),
    "storybook": ImageStyle(
        name="storybook",
        description="Storybook illustration style — warm, inviting, with character scenes.",
        background="#fef7ed",
        accent="#d97706",
        accent_light="#fde68a",
        text_primary="#78350f",
        text_secondary="#b45309",
        card_badge_fill="#d97706",
        card_badge_text="#ffffff",
        visual_motif="soft shapes, warm palette, scene compositions, character silhouettes",
    ),
    "technical-diagram": ImageStyle(
        name="technical-diagram",
        description="Precise technical diagram style — nodes, connectors, and structured layouts.",
        background="#f0fdf4",
        accent="#15803d",
        accent_light="#bbf7d0",
        text_primary="#14532d",
        text_secondary="#166534",
        card_badge_fill="#15803d",
        card_badge_text="#ffffff",
        visual_motif="boxes, arrows, node graphs, structured grid layouts",
    ),
}


def get_style(name: str) -> ImageStyle:
    """Get an image style by name.

    Args:
        name: Style name (e.g., 'clean-cartoon-explainer').

    Returns:
        ImageStyle dataclass.

    Raises:
        ValueError: If style name is unknown.
    """
    if name not in STYLES:
        available = ", ".join(sorted(STYLES.keys()))
        raise ValueError(
            f"Unknown image style: '{name}'. "
            f"Available styles: {available}"
        )
    return STYLES[name]


def list_styles() -> List[Dict[str, str]]:
    """List all available image styles with descriptions.

    Returns:
        List of dicts with 'name' and 'description' keys.
    """
    return [
        {"name": s.name, "description": s.description}
        for s in STYLES.values()
    ]
