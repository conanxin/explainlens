"""Placeholder image adapter — generates local SVG images.

This adapter is fully offline.  It creates one SVG image per ImageCard
using clean, education-style visuals with style preset support.
No external API calls are made.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard
from explainlens.images.base import ImageAdapter
from explainlens.images.styles import get_style, ImageStyle

# ── SVG templates per card index (8 visual metaphors) ─────────────

# Each template uses unified 16:9 canvas (960x540).
# Variables: {bg}, {accent}, {accent_light}, {label}, {card_num},
#             {text_primary}, {text_secondary}, {badge_fill}, {badge_text}

_SVG_WRAPPER_TOP = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
    '<rect width="960" height="540" fill="{bg}" rx="16"/>'
    # Top badge
    '<rect x="20" y="20" width="120" height="28" fill="{badge_fill}" rx="6" opacity="0.9"/>'
    '<text x="80" y="39" text-anchor="middle" font-size="11" fill="{badge_text}" '
    'font-family="system-ui,sans-serif" font-weight="700">ExplainLens</text>'
    # Card number
    '<text x="940" y="39" text-anchor="end" font-size="11" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">{card_num}</text>'
)

_SVG_WRAPPER_BOTTOM = (
    # Metaphor label
    '<text x="480" y="505" text-anchor="middle" font-size="{title_size}" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="700">{label}</text>'
    # Footer note
    '<text x="480" y="528" text-anchor="middle" font-size="9" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">'
    'Generated locally &middot; no external image API</text>'
    '</svg>'
)

# ── Visual metaphor scenes (center area, placed at y=60 to y=490) ──

_SCENE_MAZE = (
    '<g transform="translate(160,60)">'
    '<path d="M40,0 L200,0 L200,80 L120,80 L120,160 L260,160 L260,0 '
    'L320,0 L320,260 L400,260 L400,120 L480,120 L480,360 L560,360 L560,0 L640,0" '
    'fill="none" stroke="{accent}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="60" cy="0" r="12" fill="{accent}" opacity="0.6"/>'
    '<circle cx="620" cy="360" r="12" fill="{text_secondary}" opacity="0.6"/>'
    '<text x="340" y="395" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Complex path &rarr; one solution</text>'
    '</g>'
)

_SCENE_MAGNIFIER = (
    '<g transform="translate(240,60)">'
    '<ellipse cx="200" cy="210" rx="120" ry="110" fill="{accent_light}" opacity="0.3"/>'
    '<circle cx="200" cy="210" r="95" fill="none" stroke="{accent}" stroke-width="6"/>'
    '<line x1="272" y1="275" x2="380" y2="370" stroke="{accent}" stroke-width="8" '
    'stroke-linecap="round"/>'
    '<text x="200" y="218" text-anchor="middle" font-size="48" fill="{accent}" '
    'font-family="system-ui,sans-serif" font-weight="700">?</text>'
    '<text x="200" y="395" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Zoom in on what matters</text>'
    '</g>'
)

_SCENE_SPLIT = (
    '<g transform="translate(60,60)">'
    '<rect x="20" y="30" width="265" height="280" fill="#e5e7eb" rx="16" opacity="0.5"/>'
    '<rect x="555" y="30" width="265" height="280" fill="{accent_light}" rx="16" opacity="0.4"/>'
    '<text x="152" y="178" text-anchor="middle" font-size="20" fill="#6b7280" '
    'font-family="system-ui,sans-serif" font-weight="600">Old approach</text>'
    '<text x="687" y="178" text-anchor="middle" font-size="20" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">New approach</text>'
    '<path d="M420,170 L380,140 L350,120 M420,170 L380,200 L350,220" '
    'fill="none" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>'
    '<text x="420" y="400" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Before vs. after</text>'
    '</g>'
)

_SCENE_TREE = (
    '<g transform="translate(0,40)">'
    '<rect x="460" y="80" width="40" height="250" fill="#92400e" rx="6" opacity="0.7"/>'
    '<circle cx="480" cy="50" r="70" fill="#4ade80" opacity="0.45"/>'
    '<circle cx="390" cy="45" r="48" fill="{accent}" opacity="0.4"/>'
    '<circle cx="570" cy="45" r="48" fill="#f59e0b" opacity="0.4"/>'
    '<circle cx="360" cy="140" r="35" fill="#ef4444" opacity="0.35"/>'
    '<circle cx="600" cy="140" r="35" fill="#a855f7" opacity="0.35"/>'
    '<circle cx="340" cy="210" r="26" fill="{accent}" opacity="0.3"/>'
    '<circle cx="620" cy="210" r="26" fill="#22d3ee" opacity="0.3"/>'
    '<text x="480" y="400" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Concepts branch like a tree</text>'
    '</g>'
)

_SCENE_ROBOT = (
    '<g transform="translate(60,60)">'
    # Robot body
    '<rect x="140" y="130" width="140" height="170" fill="{accent}" rx="18" opacity="0.8"/>'
    '<rect x="170" y="70" width="80" height="70" fill="{accent}" rx="14" opacity="0.85"/>'
    '<circle cx="190" cy="102" r="10" fill="{bg}"/>'
    '<circle cx="230" cy="102" r="10" fill="{bg}"/>'
    '<rect x="180" y="200" width="60" height="12" fill="{accent}" rx="4" opacity="0.5"/>'
    '<rect x="180" y="222" width="60" height="12" fill="{accent}" rx="4" opacity="0.5"/>'
    '<rect x="180" y="244" width="60" height="12" fill="{accent}" rx="4" opacity="0.5"/>'
    '<rect x="180" y="266" width="60" height="12" fill="{accent}" rx="4" opacity="0.5"/>'
    # Speech bubble steps
    '<rect x="320" y="100" width="240" height="36" fill="{accent_light}" rx="8" opacity="0.5"/>'
    '<rect x="320" y="150" width="240" height="36" fill="{accent_light}" rx="8" opacity="0.6"/>'
    '<rect x="320" y="200" width="200" height="36" fill="{accent_light}" rx="8" opacity="0.7"/>'
    '<text x="340" y="124" font-size="13" fill="{text_primary}" '
    'font-family="system-ui,sans-serif">Step A: Identify problem</text>'
    '<text x="340" y="174" font-size="13" fill="{text_primary}" '
    'font-family="system-ui,sans-serif">Step B: Apply method</text>'
    '<text x="340" y="224" font-size="13" fill="{text_primary}" '
    'font-family="system-ui,sans-serif">Step C: Verify result</text>'
    '<text x="360" y="395" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Step-by-step mechanism</text>'
    '</g>'
)

_SCENE_DETECTIVE = (
    '<g transform="translate(40,40)">'
    # Detective figure
    '<circle cx="120" cy="90" r="40" fill="{accent}" opacity="0.6"/>'
    '<line x1="120" y1="130" x2="120" y2="260" stroke="{accent}" stroke-width="8" opacity="0.6"/>'
    '<line x1="120" y1="170" x2="200" y2="200" stroke="{accent}" stroke-width="6" opacity="0.6"/>'
    '<line x1="120" y1="170" x2="40" y2="200" stroke="{accent}" stroke-width="6" opacity="0.6"/>'
    # Evidence board
    '<rect x="260" y="40" width="380" height="280" fill="{accent_light}" rx="12" opacity="0.4"/>'
    '<rect x="260" y="40" width="380" height="40" fill="{accent}" rx="12" opacity="0.5"/>'
    '<rect x="260" y="52" width="380" height="28" fill="{accent}" opacity="0.5"/>'
    '<text x="450" y="70" text-anchor="middle" font-size="13" fill="{badge_text}" '
    'font-family="system-ui,sans-serif" font-weight="600">EVIDENCE BOARD</text>'
    # Evidence items
    '<circle cx="300" cy="115" r="10" fill="{accent}" opacity="0.5"/>'
    '<circle cx="340" cy="115" r="10" fill="{accent}" opacity="0.4"/>'
    '<circle cx="380" cy="115" r="10" fill="{text_secondary}" opacity="0.3"/>'
    '<line x1="290" y1="155" x2="610" y2="155" stroke="{accent}" stroke-width="2" opacity="0.4"/>'
    '<line x1="290" y1="185" x2="610" y2="185" stroke="{accent}" stroke-width="2" opacity="0.4"/>'
    '<line x1="290" y1="215" x2="560" y2="215" stroke="{accent}" stroke-width="2" opacity="0.4"/>'
    '<line x1="290" y1="245" x2="610" y2="245" stroke="{accent}" stroke-width="2" opacity="0.4"/>'
    '<line x1="290" y1="275" x2="500" y2="275" stroke="{accent}" stroke-width="2" opacity="0.4"/>'
    '<text x="430" y="400" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Evidence board</text>'
    '</g>'
)

_SCENE_BRIDGE = (
    '<g transform="translate(0,40)">'
    '<rect x="0" y="310" width="960" height="190" fill="{accent_light}" rx="0" opacity="0.3"/>'
    '<rect x="0" y="310" width="960" height="6" fill="{accent}" opacity="0.5"/>'
    '<path d="M80,310 Q480,80 880,310" fill="none" stroke="{accent}" stroke-width="10" '
    'stroke-linecap="round" opacity="0.8"/>'
    '<line x1="80" y1="270" x2="80" y2="310" stroke="{accent}" stroke-width="8" '
    'stroke-linecap="round" opacity="0.7"/>'
    '<line x1="880" y1="270" x2="880" y2="310" stroke="{accent}" stroke-width="8" '
    'stroke-linecap="round" opacity="0.7"/>'
    '<path d="M220,310 L220,240 M400,310 L400,200 M580,310 L580,240 M760,310 L760,240" '
    'stroke="{accent}" stroke-width="4" stroke-dasharray="6,4" opacity="0.5"/>'
    '<text x="480" y="400" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Bridge the gap</text>'
    '</g>'
)

_SCENE_LIGHTBULB = (
    '<g transform="translate(0,20)">'
    '<ellipse cx="480" cy="220" rx="110" ry="120" fill="{accent_light}" opacity="0.4"/>'
    '<path d="M408,280 Q480,360 552,280" fill="none" stroke="{accent}" stroke-width="7" '
    'stroke-linecap="round" opacity="0.7"/>'
    '<rect x="448" y="340" width="64" height="28" fill="{accent}" rx="6" opacity="0.6"/>'
    # Light rays
    '<line x1="480" y1="170" x2="480" y2="80" stroke="{accent}" stroke-width="5" opacity="0.5"/>'
    '<line x1="430" y1="180" x2="380" y2="100" stroke="{accent}" stroke-width="5" opacity="0.4"/>'
    '<line x1="530" y1="180" x2="580" y2="100" stroke="{accent}" stroke-width="5" opacity="0.4"/>'
    '<line x1="390" y1="210" x2="320" y2="170" stroke="{accent}" stroke-width="4" opacity="0.3"/>'
    '<line x1="570" y1="210" x2="640" y2="170" stroke="{accent}" stroke-width="4" opacity="0.3"/>'
    '<text x="480" y="430" text-anchor="middle" font-size="16" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="600">Insight changes the picture</text>'
    '</g>'
)

_SCENE_TEMPLATES = [
    _SCENE_MAZE,
    _SCENE_MAGNIFIER,
    _SCENE_SPLIT,
    _SCENE_TREE,
    _SCENE_ROBOT,
    _SCENE_DETECTIVE,
    _SCENE_BRIDGE,
    _SCENE_LIGHTBULB,
]


def _build_svg(
    scene_idx: int,
    card_num_str: str,
    label: str,
    style: ImageStyle,
) -> str:
    """Build a complete SVG for one card using the given style.

    Args:
        scene_idx: Index into _SCENE_TEMPLATES (0-7).
        card_num_str: Card number display string (e.g. "Card 03").
        label: Card title/label text.
        style: ImageStyle profile.

    Returns:
        Complete SVG string.
    """
    idx = scene_idx % len(_SCENE_TEMPLATES)
    scene = _SCENE_TEMPLATES[idx]

    top = _SVG_WRAPPER_TOP.format(
        bg=style.background,
        badge_fill=style.card_badge_fill,
        badge_text=style.card_badge_text,
        text_secondary=style.text_secondary,
        card_num=card_num_str,
    )
    bottom = _SVG_WRAPPER_BOTTOM.format(
        title_size=style.title_size,
        text_primary=style.text_primary,
        text_secondary=style.text_secondary,
        label=label,
    )
    body = scene.format(
        bg=style.background,
        accent=style.accent,
        accent_light=style.accent_light,
        text_primary=style.text_primary,
        text_secondary=style.text_secondary,
        badge_fill=style.card_badge_fill,
        badge_text=style.card_badge_text,
    )
    return top + body + bottom


class PlaceholderImageAdapter(ImageAdapter):
    """Generates local SVG placeholder images for each card.

    Fully offline — no external APIs are called.  Each SVG is a
    clean, education-style illustration labelled with the card's
    visual metaphor.  Supports style presets.
    """

    name = "placeholder"
    version = "placeholder-v0.1"
    status = "available"
    uses_external_api = False
    requires_api_key = False

    def generate_images(
        self,
        cards: Sequence[ImageCard],
        output_dir: Path,
        *,
        style: str = "clean-cartoon-explainer",
    ) -> list[dict]:
        """Generate SVG placeholder images for all cards.

        Writes images/ subdirectory under output_dir with one SVG per card.

        Args:
            cards: List of ImageCard objects.
            output_dir: Output directory path.
            style: Visual style name (default: clean-cartoon-explainer).

        Returns:
            List of image record dicts.

        Raises:
            ValueError: If style name is unknown.
        """
        style_obj = get_style(style)
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        records: list[dict] = []

        for i, card in enumerate(cards):
            image_id = f"image_{i + 1:03d}"
            card_num_str = f"Card {i + 1:02d}"
            label = card.title[:40] if card.title else f"Card {i + 1}"

            svg = _build_svg(i, card_num_str, label, style_obj)

            image_path = images_dir / f"{card.card_id}.svg"
            image_path.write_text(svg, encoding="utf-8")

            records.append({
                "image_id": image_id,
                "card_id": card.card_id,
                "adapter": self.name,
                "style": style,
                "status": "generated",
                "path": f"images/{card.card_id}.svg",
                "prompt": card.image_prompt,
                "safety_notes": [
                    "Generated locally as SVG placeholder",
                    "No external API calls",
                ],
            })

        return records
