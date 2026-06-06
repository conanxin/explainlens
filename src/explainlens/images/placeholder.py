"""Placeholder image adapter — generates local SVG images.

This adapter is fully offline.  It creates one SVG image per ImageCard
using clean, education-style visuals.  No external API calls are made.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard
from explainlens.images.base import ImageAdapter


# ── SVG template per card index ────────────────────────────────

_SVG_TEMPLATES = [
    # 0 — maze / path-finding
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#eef2ff" rx="12"/>'
        '<path d="M40,40 L120,40 L120,80 L80,80 L80,130 L160,130 L160,40 '
        'L200,40 L200,160 L240,160 L240,80 L280,80 L280,200 L320,200 L320,40 L360,40" '
        'fill="none" stroke="#4f6ef7" stroke-width="4" stroke-linecap="round"/>'
        '<circle cx="55" cy="40" r="8" fill="#4f6ef7" opacity="0.7"/>'
        '<circle cx="345" cy="200" r="8" fill="#22c55e" opacity="0.8"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#3730a3" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 1 — magnifier / zoom
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#fff7ed" rx="12"/>'
        '<ellipse cx="180" cy="118" rx="80" ry="62" fill="#fed7aa" opacity="0.5"/>'
        '<circle cx="180" cy="118" r="55" fill="none" stroke="#f97316" stroke-width="5"/>'
        '<line x1="223" y1="153" x2="280" y2="204" stroke="#f97316" stroke-width="7" '
        'stroke-linecap="round"/>'
        '<text x="180" y="122" text-anchor="middle" font-size="30" fill="#ea580c" '
        'font-family="system-ui,sans-serif">?</text>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#9a3412" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 2 — split / before-after
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#f0fdf4" rx="12"/>'
        '<rect x="20" y="40" width="155" height="140" fill="#d1d5db" rx="10" opacity="0.6"/>'
        '<rect x="225" y="40" width="155" height="140" fill="#4ade80" rx="10" opacity="0.5"/>'
        '<text x="97" y="115" text-anchor="middle" font-size="14" fill="#6b7280" '
        'font-family="system-ui,sans-serif">Old approach</text>'
        '<text x="302" y="115" text-anchor="middle" font-size="14" fill="#166534" '
        'font-family="system-ui,sans-serif">New approach</text>'
        '<path d="M175,110 L200,95 L225,110 M200,95 L200,130" fill="none" '
        'stroke="#16a34a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        '<text x="200" y="218" text-anchor="middle" font-size="13" fill="#15803d" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 3 — tree / branching
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#fefce8" rx="12"/>'
        '<rect x="188" y="90" width="24" height="120" fill="#92400e" rx="4"/>'
        '<circle cx="200" cy="72" r="45" fill="#22c55e" opacity="0.55"/>'
        '<circle cx="145" cy="68" r="30" fill="#3b82f6" opacity="0.5"/>'
        '<circle cx="255" cy="68" r="30" fill="#f59e0b" opacity="0.5"/>'
        '<circle cx="130" cy="125" r="22" fill="#ef4444" opacity="0.45"/>'
        '<circle cx="272" cy="125" r="22" fill="#a855f7" opacity="0.45"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#854d0e" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 4 — robot / step-by-step
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#eff6ff" rx="12"/>'
        '<rect x="60" y="100" width="80" height="90" fill="#60a5fa" rx="10"/>'
        '<rect x="80" y="72" width="40" height="36" fill="#3b82f6" rx="8"/>'
        '<circle cx="92" cy="90" r="6" fill="#1e3a8a"/>'
        '<circle cx="108" cy="90" r="6" fill="#1e3a8a"/>'
        '<rect x="150" y="100" width="140" height="24" fill="#bfdbfe" rx="6"/>'
        '<rect x="150" y="134" width="140" height="24" fill="#93c5fd" rx="6"/>'
        '<rect x="150" y="168" width="100" height="24" fill="#60a5fa" rx="6"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#1e40af" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 5 — detective / evidence
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#faf5ff" rx="12"/>'
        '<circle cx="100" cy="68" r="28" fill="#c084fc" opacity="0.7"/>'
        '<line x1="100" y1="96" x2="100" y2="165" stroke="#9333ea" stroke-width="5"/>'
        '<line x1="100" y1="115" x2="148" y2="130" stroke="#9333ea" stroke-width="4"/>'
        '<line x1="100" y1="115" x2="52" y2="130" stroke="#9333ea" stroke-width="4"/>'
        '<rect x="200" y="44" width="170" height="150" fill="#ede9fe" rx="8"/>'
        '<circle cx="220" cy="82" r="6" fill="#7c3aed"/>'
        '<circle cx="248" cy="82" r="6" fill="#7c3aed"/>'
        '<circle cx="276" cy="82" r="6" fill="#a78bfa"/>'
        '<line x1="215" y1="110" x2="355" y2="110" stroke="#9333ea" stroke-width="2"/>'
        '<line x1="215" y1="135" x2="355" y2="135" stroke="#9333ea" stroke-width="2"/>'
        '<line x1="215" y1="160" x2="310" y2="160" stroke="#9333ea" stroke-width="2"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#6b21a8" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 6 — bridge / gap
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#fff1f2" rx="12"/>'
        '<rect x="0" y="185" width="400" height="65" fill="#fecdd3" rx="0"/>'
        '<rect x="0" y="185" width="400" height="4" fill="#fca5a5"/>'
        '<path d="M40,185 Q200,70 360,185" fill="none" stroke="#f43f5e" stroke-width="7"/>'
        '<line x1="40" y1="160" x2="40" y2="185" stroke="#e11d48" stroke-width="5"/>'
        '<line x1="360" y1="160" x2="360" y2="185" stroke="#e11d48" stroke-width="5"/>'
        '<path d="M120,185 L120,145 M200,185 L200,120 M280,185 L280,145" '
        'stroke="#fb7185" stroke-width="3" stroke-dasharray="4,3"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="13" fill="#9f1239" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
    # 7 — lightbulb / insight
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250">'
        '<rect width="400" height="250" fill="#fffbeb" rx="12"/>'
        '<ellipse cx="200" cy="118" rx="55" ry="60" fill="#fde68a" opacity="0.6"/>'
        '<path d="M164,138 Q200,172 236,138" fill="none" stroke="#f59e0b" stroke-width="5" '
        'stroke-linecap="round"/>'
        '<rect x="184" y="160" width="32" height="16" fill="#d97706" rx="3"/>'
        '<line x1="192" y1="92" x2="175" y2="52" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="208" y1="92" x2="225" y2="52" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="200" y1="88" x2="200" y2="44" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="152" y1="105" x2="110" y2="92" stroke="#fcd34d" stroke-width="2.5"/>'
        '<line x1="248" y1="105" x2="290" y2="92" stroke="#fcd34d" stroke-width="2.5"/>'
        '<text x="200" y="215" text-anchor="middle" font-size="13" fill="#92400e" '
        'font-family="system-ui,sans-serif" font-weight="600">{label}</text>'
        '</svg>'
    ),
]


class PlaceholderImageAdapter(ImageAdapter):
    """Generates local SVG placeholder images for each card.

    Fully offline — no external APIs are called.  Each SVG is a
    clean, education-style illustration labelled with the card's
    visual metaphor.
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
        """
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        records: list[dict] = []

        for i, card in enumerate(cards):
            idx = i % len(_SVG_TEMPLATES)
            image_id = f"image_{i + 1:03d}"

            label = card.title[:40] if card.title else f"Card {i + 1}"
            svg = _SVG_TEMPLATES[idx].format(label=label)

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
                    "Generated locally as SVG placeholder",
                    "No external API calls",
                ],
            })

        return records
