"""Fixture image adapter — deterministic SVG templates for CI/testing.

Completely offline.  Uses simple numbered SVG templates that simulate
generated image assets without any external dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard
from explainlens.images.base import ImageAdapter


_FIXTURE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
    '<rect width="400" height="250" fill="#f5f5f5" rx="12"/>'
    '<rect x="30" y="30" width="340" height="160" fill="#e0e7ff" rx="8" stroke="#a5b4fc" stroke-width="2"/>'
    '<text x="200" y="95" text-anchor="middle" font-size="16" fill="#4338ca" '
    'font-family="system-ui,sans-serif" font-weight="700">{title}</text>'
    '<text x="200" y="125" text-anchor="middle" font-size="12" fill="#6366f1" '
    'font-family="system-ui,sans-serif">[fixture {idx}]</text>'
    '<text x="200" y="155" text-anchor="middle" font-size="11" fill="#818cf8" '
    'font-family="system-ui,sans-serif">No external API calls</text>'
    '<text x="200" y="225" text-anchor="middle" font-size="10" fill="#9ca3af" '
    'font-family="system-ui,sans-serif">ExplainLens fixture adapter</text>'
    '</svg>'
)


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
        """Generate fixture SVG images for all cards."""
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        records: list[dict] = []

        for i, card in enumerate(cards):
            image_id = f"image_{i + 1:03d}"
            title = card.title[:50] if card.title else f"Card {i + 1}"

            svg = _FIXTURE_SVG.format(title=title, idx=i + 1)

            image_path = images_dir / f"{card.card_id}.svg"
            image_path.write_text(svg, encoding="utf-8")

            records.append({
                "image_id": image_id,
                "card_id": card.card_id,
                "adapter": self.name,
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
