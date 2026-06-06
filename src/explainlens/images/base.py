"""Abstract base class for image adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from explainlens.schemas import ImageCard


class ImageAdapter(ABC):
    """Abstract base class for image generation adapters.

    Each adapter generates images from ImageCard objects and writes
    them to an output directory.  Adapters may be local-only or
    delegate to external services (if explicitly opted-in).

    Attributes:
        name: Human-readable adapter name (e.g. "placeholder").
        version: Adapter version string (e.g. "placeholder-v0.1").
        status: Availability status: "available" | "experimental" | "disabled".
        uses_external_api: Whether this adapter calls external image services.
        requires_api_key: Whether this adapter needs an API key.
    """

    name: str
    version: str
    status: str
    uses_external_api: bool
    requires_api_key: bool

    @abstractmethod
    def generate_images(
        self,
        cards: Sequence[ImageCard],
        output_dir: Path,
        *,
        style: str = "clean-cartoon-explainer",
    ) -> list[dict]:
        """Generate images for a sequence of ImageCards.

        Args:
            cards: The ImageCard objects to render.
            output_dir: Directory where image files will be written.
            style: Visual style hint (e.g. "clean-cartoon-explainer").

        Returns:
            A list of image record dicts, each containing at minimum:
                image_id, card_id, adapter, status, path, prompt,
                safety_notes.
        """
        ...
