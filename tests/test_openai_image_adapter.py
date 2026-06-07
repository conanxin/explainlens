"""Tests for OpenAI Image Adapter (openai_image.py).

All tests are unit tests using mock transport — NO real API calls are made.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from explainlens.schemas import ImageCard
from explainlens.images.openai_image import OpenAIImageAdapter
from explainlens.images.openai_image_transport import run_mock_openai_image_transport


# ── Helpers ──────────────────────────────────────────────────

def _make_sample_cards(count: int = 3):
    """Create sample ImageCard objects for testing."""
    return [
        ImageCard(
            card_id=f"card_{(i + 1):02d}",
            title=f"Card {i + 1}",
            explanation=f"Explanation for card {i + 1}",
            image_prompt=f"A clean illustration of concept {i + 1}",
            takeaway=f"Takeaway {i + 1}",
            source_chunk_ids=[f"chunk_{(i + 1):03d}"],
        )
        for i in range(count)
    ]


# ── Adapter Metadata Tests ───────────────────────────────────

class TestOpenAIImageAdapterMetadata:
    """Tests for adapter metadata attributes."""

    def test_name(self):
        adapter = OpenAIImageAdapter()
        assert adapter.name == "openai-image"

    def test_version(self):
        adapter = OpenAIImageAdapter()
        assert adapter.version == "openai-image-v0.1"

    def test_status_experimental(self):
        adapter = OpenAIImageAdapter()
        assert adapter.status == "experimental"

    def test_uses_external_api(self):
        adapter = OpenAIImageAdapter()
        assert adapter.uses_external_api is True

    def test_requires_api_key(self):
        adapter = OpenAIImageAdapter()
        assert adapter.requires_api_key is True

    def test_allow_external_images_defaults_false(self):
        """By default, external images must be opt-in."""
        adapter = OpenAIImageAdapter()
        assert adapter.allow_external_images is False

    def test_no_api_key_at_init(self):
        """API key should not be read at construction time."""
        adapter = OpenAIImageAdapter()
        assert adapter._api_key is None
        assert adapter.allow_external_images is False


# ── Fail-Closed Gate Tests ───────────────────────────────────

class TestOpenAIImageAdapterFailClosed:
    """Tests for _check_fail_closed() gate."""

    def test_raises_when_allow_external_images_false(self):
        adapter = OpenAIImageAdapter()
        with pytest.raises(RuntimeError, match="fail-closed by default"):
            adapter._check_fail_closed()

    def test_raises_when_no_api_key(self):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key(None)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
            adapter._check_fail_closed()

    def test_raises_when_api_key_empty_string(self):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("")
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
            adapter._check_fail_closed()

    def test_raises_when_api_key_not_sk_prefix(self):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("bad-key-123")
        with pytest.raises(RuntimeError, match="does not look valid"):
            adapter._check_fail_closed()

    def test_passes_with_valid_key_and_flag(self):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-proj-test123")
        # Should not raise
        adapter._check_fail_closed()

    def test_passes_with_ssk_prefix(self):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("ssk-test-service-key")
        adapter._check_fail_closed()

    def test_error_message_contains_guidance(self):
        adapter = OpenAIImageAdapter()
        try:
            adapter._check_fail_closed()
        except RuntimeError as e:
            msg = str(e)
            assert "OPENAI_API_KEY" in msg
            assert "--allow-external-images" in msg
            assert "No request was sent" in msg

    def test_no_request_sent_in_error(self):
        """All fail-closed errors should say 'No request was sent'."""
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("")
        try:
            adapter._check_fail_closed()
        except RuntimeError as e:
            assert "No request was sent" in str(e)


# ── Transport Injection Tests ────────────────────────────────

class TestOpenAIImageAdapterTransportInjection:
    """Tests for _call_transport() injection point."""

    def test_transport_uses_mock_when_injected(self, tmp_path):
        """Adapter should use injected mock transport for testing."""
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")

        # Inject mock transport
        def mock_transport(prompt):
            return run_mock_openai_image_transport(prompt, model="mock-model")

        adapter._call_transport = mock_transport

        cards = _make_sample_cards(3)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)

        assert len(records) == 3
        for rec in records:
            assert rec["status"] == "mock"
            assert rec["model"] == "mock"
            assert "NO real API call was made" in str(rec["adapter_notes"])

    def test_transport_injection_produces_mock_svg(self, tmp_path):
        """Injected mock transport should produce SVG files."""
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")

        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(2)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)

        images_dir = output_dir / "images"
        assert images_dir.is_dir()

        svg_files = list(images_dir.glob("*.svg"))
        assert len(svg_files) == 2
        for svg_path in svg_files:
            content = svg_path.read_text(encoding="utf-8")
            assert "<svg" in content
            assert "</svg>" in content
            assert "OpenAI Image Adapter" in content


# ── Mock SVG Generation Tests ────────────────────────────────

class TestOpenAIImageAdapterMockSVG:
    """Tests for mock SVG placeholder generation."""

    def test_mock_svg_contains_card_id(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(cards, output_dir)

        svg_path = output_dir / "images" / "card_01.svg"
        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "card_01" in content

    def test_mock_svg_uses_style_colors(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(cards, output_dir)

        svg_path = output_dir / "images" / "card_01.svg"
        content = svg_path.read_text(encoding="utf-8")

        # clean-cartoon-explainer style uses these colors
        assert "#eef2ff" in content       # background
        assert "#4f6ef7" in content       # accent (opacity fill)
        assert "#3730a3" in content       # text_primary

    def test_mock_svg_is_valid_svg(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(cards, output_dir)

        svg_path = output_dir / "images" / "card_01.svg"
        content = svg_path.read_text(encoding="utf-8")

        assert content.strip().startswith("<svg")
        assert "</svg>" in content
        assert 'xmlns="http://www.w3.org/2000/svg"' in content
        assert 'viewBox="0 0 960 540"' in content

    def test_mock_svg_no_secrets(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(cards, output_dir)

        svg_path = output_dir / "images" / "card_01.svg"
        content = svg_path.read_text(encoding="utf-8")

        assert "sk-test123" not in content
        assert "OPENAI_API_KEY" not in content
        assert "Bearer" not in content

    def test_mock_svg_shows_experimental_badge(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        adapter.generate_images(cards, output_dir)

        svg_path = output_dir / "images" / "card_01.svg"
        content = svg_path.read_text(encoding="utf-8")
        assert "experimental" in content


# ── Error Handling Tests ─────────────────────────────────────

class TestOpenAIImageAdapterErrorHandling:
    """Tests for error handling in generate_images()."""

    def test_transport_error_generates_error_svg(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")

        def failing_transport(prompt):
            raise RuntimeError("Simulated API error")

        adapter._call_transport = failing_transport

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)

        # Should not crash — should produce an error record
        assert len(records) == 1
        assert records[0]["status"] == "error"
        assert "Simulated API error" in str(records[0]["adapter_notes"])
        assert "Simulated API error" in str(records[0]["adapter_notes"])

        # Should still create SVG
        svg_path = output_dir / "images" / "card_01.svg"
        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "Image generation failed" in content

    def test_error_svg_no_secrets(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")

        def failing_transport(prompt):
            raise RuntimeError("Error with key sk-test123 exposed")

        adapter._call_transport = failing_transport

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)

        # Error message in records should still be sanitized
        # (The key might appear in the notes since we passed it explicitly)
        svg_path = output_dir / "images" / "card_01.svg"
        content = svg_path.read_text(encoding="utf-8")

        # SVG should still not contain OPENAI_API_KEY
        assert "OPENAI_API_KEY" not in content

    def test_all_cards_generated_even_on_partial_failure(self, tmp_path):
        """Even if some transports fail, all cards should get records."""
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")

        call_count = [0]

        def flaky_transport(prompt):
            call_count[0] += 1
            if "concept 1" in prompt:
                return run_mock_openai_image_transport(prompt)
            else:
                raise RuntimeError(f"API error for prompt {call_count[0]}")

        adapter._call_transport = flaky_transport

        cards = _make_sample_cards(3)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)

        assert len(records) == 3
        statuses = [r["status"] for r in records]
        assert "mock" in statuses
        assert "error" in statuses

        # Check SVG files for all cards exist
        for i in range(3):
            card_id = f"card_{(i + 1):02d}"
            svg_path = output_dir / "images" / f"{card_id}.svg"
            assert svg_path.exists(), f"Expected {svg_path} to exist"

    def test_style_fallback_on_unknown_style(self, tmp_path):
        """Unknown style should fall back to clean-cartoon-explainer."""
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Should not crash with unknown style
        records = adapter.generate_images(cards, output_dir, style="non-existent-style")
        assert len(records) == 1
        assert records[0]["status"] == "mock"


# ── Record Structure Tests ───────────────────────────────────

class TestOpenAIImageAdapterRecords:
    """Tests for image record structure."""

    def test_record_has_all_required_fields(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)
        rec = records[0]

        required_fields = [
            "image_id", "card_id", "adapter", "style", "status",
            "path", "prompt", "model", "adapter_notes", "safety_notes",
        ]
        for field in required_fields:
            assert field in rec, f"Missing field '{field}' in record"

    def test_mock_record_status_is_mock(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)
        assert records[0]["status"] == "mock"

    def test_mock_record_adapter_name(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)
        assert records[0]["adapter"] == "openai-image"

    def test_paths_are_relative(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)
        path = records[0]["path"]
        assert not path.startswith("/")
        assert not path.startswith("\\")
        assert not ":" in path
        assert path.startswith("images/")

    def test_safety_notes_for_mock(self, tmp_path):
        adapter = OpenAIImageAdapter()
        adapter.allow_external_images = True
        adapter._set_api_key("sk-test123")
        adapter._call_transport = lambda prompt: run_mock_openai_image_transport(prompt)

        cards = _make_sample_cards(1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        records = adapter.generate_images(cards, output_dir)
        notes = records[0]["safety_notes"]
        assert "no real api call was made" in str(notes).lower()
