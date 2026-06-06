"""Image manifest — build and write image_manifest.json."""

from __future__ import annotations

import json
from pathlib import Path


def build_image_manifest(
    image_records: list[dict],
    *,
    adapter: str = "placeholder",
    adapter_version: str = "placeholder-v0.1",
    uses_external_api: bool = False,
    requires_api_key: bool = False,
) -> dict:
    """Build the image_manifest payload.

    Args:
        image_records: List of image record dicts from the adapter.
        adapter: Name of the image adapter.
        adapter_version: Version of the image adapter.
        uses_external_api: Whether external APIs were used.
        requires_api_key: Whether API keys were required.

    Returns:
        Dict suitable for writing to image_manifest.json.
    """
    return {
        "adapter": adapter,
        "adapter_version": adapter_version,
        "uses_external_api": uses_external_api,
        "requires_api_key": requires_api_key,
        "image_count": len(image_records),
        "images": image_records,
    }


def write_image_manifest(
    image_records: list[dict],
    output_dir: Path,
    *,
    adapter: str = "placeholder",
    adapter_version: str = "placeholder-v0.1",
    uses_external_api: bool = False,
    requires_api_key: bool = False,
) -> dict:
    """Build image_manifest payload and write it to output_dir/image_manifest.json.

    Args:
        image_records: List of image record dicts.
        output_dir: Directory to write image_manifest.json into.
        adapter: Name of the image adapter.
        adapter_version: Version of the image adapter.
        uses_external_api: Whether external APIs were used.
        requires_api_key: Whether API keys were required.

    Returns:
        The image_manifest dict that was written.
    """
    manifest = build_image_manifest(
        image_records,
        adapter=adapter,
        adapter_version=adapter_version,
        uses_external_api=uses_external_api,
        requires_api_key=requires_api_key,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "image_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest
