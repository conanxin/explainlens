"""OpenAI Images adapter — opt-in, fail-closed.

This adapter calls the OpenAI Images API (DALL-E) to generate
real images for explainer cards. By default it is FAIL-CLOSED:
no external API calls happen unless the user explicitly opts in
with --allow-external-images AND OPENAI_API_KEY is set.

Usage:
    --image-adapter openai-image --allow-external-images

Safety rules:
- API key is NEVER printed, logged, or written to any file.
- Image prompts are NOT written to logs.
- Full API responses are NOT written to logs.
- Source excerpts are NEVER sent to the image API.
- The adapter is experimental.
- No OpenAI SDK is imported or required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Sequence

from explainlens.images.base import ImageAdapter
from explainlens.images.styles import get_style, ImageStyle

# ── SVG placeholder for mock / fallback ────────────

_OPENAI_IMAGE_PLACEHOLDER_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">
  <rect width="960" height="540" fill="{bg}" rx="12"/>
  <text x="480" y="180" text-anchor="middle" font-family="sans-serif"
        font-size="28" fill="{text_primary}" font-weight="bold">
    OpenAI Image Adapter
  </text>
  <text x="480" y="230" text-anchor="middle" font-family="sans-serif"
        font-size="16" fill="{text_primary}" opacity="0.7">
    External image generation (experimental)
  </text>
  <rect x="280" y="280" width="400" height="120" rx="8"
        fill="{accent}" opacity="0.15" stroke="{accent}" stroke-width="2"/>
  <text x="480" y="320" text-anchor="middle" font-family="sans-serif"
        font-size="20" fill="{text_primary}" font-weight="bold">
    Card: {card_id}
  </text>
  <text x="480" y="355" text-anchor="middle" font-family="sans-serif"
        font-size="14" fill="{text_primary}" opacity="0.8">
    {prompt_preview}
  </text>
  <text x="480" y="450" text-anchor="middle" font-family="sans-serif"
        font-size="12" fill="{text_primary}" opacity="0.5">
    mock openai-image transport — no real API call was made
  </text>
  <rect x="820" y="12" width="128" height="28" rx="14"
        fill="{accent}" opacity="0.8"/>
  <text x="884" y="32" text-anchor="middle" font-family="sans-serif"
        font-size="11" fill="#fff" font-weight="bold">
    experimental
  </text>
</svg>"""


# ── Adapter ──────────────────────────────────────


class OpenAIImageAdapter(ImageAdapter):
    """Image adapter that calls OpenAI Images API (DALL-E).

    FAIL-CLOSED by default. Requires explicit opt-in:
        --image-adapter openai-image --allow-external-images
        AND OPENAI_API_KEY environment variable.

    Safety:
    - never logs or stores the API key
    - never writes image prompts to logs
    - never sends source excerpts to the API
    - transport is injectable for mock testing
    """

    name = "openai-image"
    version = "openai-image-v0.1"
    status = "experimental"
    uses_external_api = True
    requires_api_key = True

    def __init__(self) -> None:
        """Initialize the adapter with fail-closed defaults.

        No API key is read at construction time.
        Real API calls will fail at generate_images() time
        if not explicitly opted in.
        """
        self.allow_external_images = False
        self._api_key: str | None = None

    # ── Transport injection point (for mock testing) ──

    def _call_transport(self, prompt: str) -> dict:
        """Call the image generation transport.

        This is the injection point for mock testing.
        Production code uses call_openai_images_api().
        Tests can replace this with run_mock_openai_image_transport().
        """
        from explainlens.images.openai_image_transport import (
            call_openai_images_api,
        )

        return call_openai_images_api(
            prompt=prompt,
            api_key=self._get_api_key(),
            allow_external_images=self.allow_external_images,
        )

    # ── Fail-closed gate ──────────────────────────

    def _check_fail_closed(self) -> None:
        """Check that external image API access is allowed.

        If allow_external_images is False (default), raises RuntimeError.
        If OPENAI_API_KEY is not set or invalid, raises RuntimeError.

        Raises:
            RuntimeError: If external API access is not explicitly enabled.
        """
        if not self.allow_external_images:
            raise RuntimeError(
                "OpenAI Images API is fail-closed by default.\n"
                "To enable it, set OPENAI_API_KEY and pass --allow-external-images.\n"
                "No request was sent."
            )

        api_key = self._get_api_key()
        if not api_key or not isinstance(api_key, str):
            raise RuntimeError(
                "OPENAI_API_KEY is not set.\n"
                "No request was sent."
            )
        if not (api_key.startswith("sk-") or api_key.startswith("ssk-")):
            raise RuntimeError(
                "OPENAI_API_KEY does not look valid "
                "(should start with sk- or sk-proj-).\n"
                "No request was sent."
            )

    def _get_api_key(self) -> str | None:
        """Read OPENAI_API_KEY from environment (never cached, never logged)."""
        if self._api_key is not None:
            return self._api_key
        return os.environ.get("OPENAI_API_KEY")

    def _set_api_key(self, key: str | None) -> None:
        """Set the API key directly (ONLY for testing with fake keys).

        In production, the key is ALWAYS read from os.environ.
        """
        self._api_key = key

    # ── Image generation ──────────────────────────

    def generate_images(
        self,
        cards: Sequence[Any],
        output_dir: Path,
        *,
        style: str = "clean-cartoon-explainer",
    ) -> list[dict]:
        """Generate images for each card using OpenAI Images API.

        Args:
            cards: Sequence of ImageCard objects.
            output_dir: Directory to write images into.
            style: Visual style preset (used for metadata only).

        Returns:
            List of image record dicts.
        """
        self._check_fail_closed()

        try:
            style_obj = get_style(style)
        except ValueError:
            # fallback to default style for metadata
            style_obj = get_style("clean-cartoon-explainer")

        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        image_records: list[dict] = []

        for i, card in enumerate(cards):
            image_id = f"image_{i + 1:03d}"
            card_id = getattr(card, "card_id", f"card_{i:02d}")
            prompt = getattr(card, "image_prompt", "") or ""

            # Build a safety-trimmed prompt preview for the record
            prompt_preview = prompt[:120]
            if len(prompt) > 120:
                prompt_preview += "..."

            try:
                result = self._call_transport(prompt)

                image_url = result.get("image_url", "")
                adapter_notes = result.get("adapter_notes", [])

                if image_url:
                    # Real API call succeeded — download and save
                    from explainlens.images.openai_image_transport import (
                        download_image_from_url,
                    )

                    image_bytes = download_image_from_url(image_url)
                    image_path = images_dir / f"{card_id}.png"
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    image_records.append({
                        "image_id": image_id,
                        "card_id": card_id,
                        "adapter": self.name,
                        "style": style,
                        "status": "generated",
                        "path": f"images/{card_id}.png",
                        "prompt": prompt_preview,
                        "model": result.get("model", "dall-e-3"),
                        "adapter_notes": adapter_notes,
                        "safety_notes": [
                            "Generated via OpenAI Images API",
                            "External API call was made",
                        ],
                    })
                else:
                    # Mock transport — generate placeholder SVG
                    self._write_mock_svg(
                        images_dir, card_id, prompt_preview, style_obj, image_id, card,
                        image_records, adapter_notes, style,
                    )

            except Exception as e:
                # On failure, log but continue with a placeholder
                self._write_error_svg(
                    images_dir, card_id, prompt_preview, style_obj, image_id, card,
                    image_records, str(e), style,
                )

        return image_records

    def _write_mock_svg(
        self,
        images_dir: Path,
        card_id: str,
        prompt_preview: str,
        style_obj: ImageStyle,
        image_id: str,
        card: Any,
        image_records: list[dict],
        adapter_notes: list[str],
        style: str,
    ) -> None:
        """Write a mock SVG placeholder (no real API call was made)."""
        svg = _OPENAI_IMAGE_PLACEHOLDER_SVG.format(
            bg=style_obj.background,
            text_primary=style_obj.text_primary,
            accent=style_obj.accent,
            card_id=card_id,
            prompt_preview=prompt_preview,
        )
        svg_path = images_dir / f"{card_id}.svg"
        try:
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)
        except OSError:
            pass

        image_records.append({
            "image_id": image_id,
            "card_id": card_id,
            "adapter": self.name,
            "style": style,
            "status": "mock",
            "path": f"images/{card_id}.svg",
            "prompt": prompt_preview,
            "model": "mock",
            "adapter_notes": adapter_notes,
            "safety_notes": [
                "Mock transport — no real API call was made",
                "Placeholder SVG generated locally",
            ],
        })

    def _write_error_svg(
        self,
        images_dir: Path,
        card_id: str,
        prompt_preview: str,
        style_obj: ImageStyle,
        image_id: str,
        card: Any,
        image_records: list[dict],
        error_msg: str,
        style: str,
    ) -> None:
        """Write an error SVG placeholder on API failure."""
        error_safe = error_msg[:200].replace("<", "&lt;").replace(">", "&gt;")

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">
  <rect width="960" height="540" fill="{style_obj.background}" rx="12"/>
  <text x="480" y="200" text-anchor="middle" font-family="sans-serif"
        font-size="24" fill="#c0392b" font-weight="bold">
    Image generation failed
  </text>
  <text x="480" y="250" text-anchor="middle" font-family="sans-serif"
        font-size="14" fill="{style_obj.text_primary}" opacity="0.7">
    Card: {card_id}
  </text>
  <text x="480" y="310" text-anchor="middle" font-family="monospace"
        font-size="12" fill="{style_obj.text_primary}" opacity="0.6">
    {error_safe}
  </text>
  <text x="480" y="400" text-anchor="middle" font-family="sans-serif"
        font-size="11" fill="{style_obj.text_primary}" opacity="0.4">
    ExplainLens — openai-image adapter
  </text>
</svg>"""

        svg_path = images_dir / f"{card_id}.svg"
        try:
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)
        except OSError:
            pass

        image_records.append({
            "image_id": image_id,
            "card_id": card_id,
            "adapter": self.name,
            "style": style,
            "status": "error",
            "path": f"images/{card_id}.svg",
            "prompt": prompt_preview,
            "model": "dall-e-3",
            "adapter_notes": [f"Error: {error_safe}"],
            "safety_notes": [
                "Image generation failed — placeholder SVG",
                "No external API call completed",
            ],
        })
