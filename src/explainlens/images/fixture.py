"""Fixture image adapter — deterministic SVG templates for CI/testing.

Completely offline.  Uses simple numbered SVG templates that simulate
generated image assets without any external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard
from explainlens.images.base import ImageAdapter
from explainlens.images.styles import get_style, ImageStyle

# ── Fixture SVG template (16:9, 960x540) ────────────────────────

_FIXTURE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
    # Background
    '<rect width="960" height="540" fill="{bg}" rx="16"/>'
    # Top badge
    '<rect x="20" y="20" width="120" height="28" fill="{badge_fill}" rx="6" opacity="0.9"/>'
    '<text x="80" y="39" text-anchor="middle" font-size="11" fill="{badge_text}" '
    'font-family="system-ui,sans-serif" font-weight="700">ExplainLens</text>'
    # Card number
    '<text x="940" y="39" text-anchor="end" font-size="11" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">Card {card_num:02d}</text>'
    # Central card area
    '<rect x="80" y="80" width="800" height="320" fill="{accent_light}" rx="16" '
    'stroke="{accent}" stroke-width="3" opacity="0.6"/>'
    # Icon area (top of card)
    '<circle cx="480" cy="180" r="60" fill="{accent}" opacity="0.15"/>'
    '<text x="480" y="188" text-anchor="middle" font-size="40" fill="{accent}" '
    'font-family="system-ui,sans-serif" font-weight="700" opacity="0.5">{icon_char}</text>'
    # Title
    '<text x="480" y="240" text-anchor="middle" font-size="{title_size}" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="700">{title}</text>'
    # Fixture label
    '<text x="480" y="275" text-anchor="middle" font-size="13" fill="{accent}" '
    'font-family="system-ui,sans-serif">[fixture {idx}]</text>'
    # Scene label
    '<text x="480" y="305" text-anchor="middle" font-size="12" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">{scene_label}</text>'
    # Safety note
    '<text x="480" y="335" text-anchor="middle" font-size="11" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">No external API calls</text>'
    # Bottom label
    '<text x="480" y="505" text-anchor="middle" font-size="{title_size}" fill="{text_primary}" '
    'font-family="system-ui,sans-serif" font-weight="700">{label}</text>'
    # Footer
    '<text x="480" y="528" text-anchor="middle" font-size="9" fill="{text_secondary}" '
    'font-family="system-ui,sans-serif">'
    'Generated locally &middot; no external image API</text>'
    '</svg>'
)

# Visual scene labels per card index (deterministic)
_SCENE_LABELS = [
    "path-finding through complexity",
    "zooming into details",
    "before and after contrast",
    "hierarchical concept tree",
    "step-by-step process",
    "connecting the evidence",
    "bridging theory and practice",
    "the moment of insight",
]

# Icon characters per scene
_ICON_CHARS = [
    "\u25c9",   # ◉ maze
    "\u25cb",   # ○ magnifier
    "\u25d0",   # ◐ split
    "\u25b3",   # △ tree
    "\u25a1",   # □ robot
    "\u25c6",   # ◆ detective
    "\u2248",   # ≈ bridge
    "\u2606",   # ☆ lightbulb
]


class FixtureImageAdapter(ImageAdapter):
    """Deterministic fixture image adapter for CI and testing.

    Generates simple numbered SVG files — identical output every run.
    No network, no API keys, no external services.
    """

    name = "fixture"
    version = "fixture-v0.1"
    status = "experimental"
    uses_external_api = False
    requires_api_key = False

    def generate_images(
        self,
        cards: Sequence[ImageCard],
        output_dir: Path,
        *,
        style: str = "clean-cartoon-explainer",
    ) -> list[dict]:
        """Generate fixture SVG images for all cards.

        Args:
            cards: List of ImageCard objects.
            output_dir: Output directory path.
            style: Visual style name.

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
            title = card.title[:50] if card.title else f"Card {i + 1}"
            label = card.title[:40] if card.title else f"Card {i + 1}"
            scene_idx = i % len(_SCENE_LABELS)
            icon_char = _ICON_CHARS[scene_idx]

            svg = _FIXTURE_SVG.format(
                bg=style_obj.background,
                badge_fill=style_obj.card_badge_fill,
                badge_text=style_obj.card_badge_text,
                text_primary=style_obj.text_primary,
                text_secondary=style_obj.text_secondary,
                accent=style_obj.accent,
                accent_light=style_obj.accent_light,
                title_size=style_obj.title_size,
                card_num=i + 1,
                title=title,
                label=label,
                idx=i + 1,
                scene_label=_SCENE_LABELS[scene_idx],
                icon_char=icon_char,
            )

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
                    "Generated locally as fixture SVG",
                    "No external API calls",
                    "Deterministic — identical output every run",
                ],
            })

        return records
