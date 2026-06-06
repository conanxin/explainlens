"""Image adapter package for ExplainLens.

Provides a pluggable interface for generating images from ImageCards.
Default adapters are local-only (no external API calls).
"""

from explainlens.images.base import ImageAdapter
from explainlens.images.placeholder import PlaceholderImageAdapter
from explainlens.images.fixture import FixtureImageAdapter
from explainlens.images.registry import (
    AVAILABLE_IMAGE_ADAPTERS,
    get_image_adapter,
    list_image_adapters,
)
from explainlens.images.jobs import build_image_jobs, write_image_jobs
from explainlens.images.manifest import build_image_manifest, write_image_manifest

__all__ = [
    "ImageAdapter",
    "PlaceholderImageAdapter",
    "FixtureImageAdapter",
    "AVAILABLE_IMAGE_ADAPTERS",
    "get_image_adapter",
    "list_image_adapters",
    "build_image_jobs",
    "write_image_jobs",
    "build_image_manifest",
    "write_image_manifest",
]
