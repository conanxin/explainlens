"""Image adapter registry — discover and instantiate image adapters."""

from __future__ import annotations

from explainlens.images.base import ImageAdapter
from explainlens.images.placeholder import PlaceholderImageAdapter
from explainlens.images.fixture import FixtureImageAdapter

AVAILABLE_IMAGE_ADAPTERS: dict[str, type[ImageAdapter]] = {
    "placeholder": PlaceholderImageAdapter,
    "fixture": FixtureImageAdapter,
}


def get_image_adapter(name: str) -> ImageAdapter:
    """Get an image adapter instance by name.

    Args:
        name: Adapter name (e.g. "placeholder", "fixture").

    Returns:
        An ImageAdapter instance.

    Raises:
        ValueError: If the adapter name is unknown.
    """
    name = name.lower().strip()

    if name not in AVAILABLE_IMAGE_ADAPTERS:
        known = ", ".join(sorted(AVAILABLE_IMAGE_ADAPTERS.keys()))
        raise ValueError(
            f"Unknown image adapter: '{name}'. "
            f"Available adapters: {known}"
        )

    return AVAILABLE_IMAGE_ADAPTERS[name]()


def list_image_adapters() -> list[dict]:
    """List all available image adapters with metadata.

    Returns:
        List of dicts with keys: name, version, status,
        uses_external_api, requires_api_key.
    """
    result = []
    for _name, cls in AVAILABLE_IMAGE_ADAPTERS.items():
        # Instantiate to read class attributes
        adapter = cls()
        result.append({
            "name": adapter.name,
            "version": adapter.version,
            "status": adapter.status,
            "uses_external_api": adapter.uses_external_api,
            "requires_api_key": adapter.requires_api_key,
        })
    return result
