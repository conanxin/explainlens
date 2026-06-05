"""Tests for local_http.py provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from explainlens.providers.base import ExplainProvider
from explainlens.providers.local_http import LocalHttpProvider
from explainlens.schemas import ConceptMap, ImageCard, SourceChunk


# ── Fixtures ─────────────────────────────────────────────

def _make_chunks(count: int = 4) -> List[SourceChunk]:
    return [
        SourceChunk(
            chunk_id=f"chunk_{i:03d}",
            text=f"Test content for chunk {i}. " * 20,
            start_char=i * 100,
            end_char=(i + 1) * 100,
            source_type="txt",
        )
        for i in range(count)
    ]


def _make_provider(
    protocol: str = "fixture",
    allow_network: bool = False,
    endpoint: str = None,
    model: str = "test-model",
    timeout: float = 30.0,
) -> LocalHttpProvider:
    provider = LocalHttpProvider()
    provider.protocol = protocol  # type: ignore
    provider.allow_network = allow_network
    provider.endpoint = endpoint
    provider.model = model
    provider.timeout_seconds = timeout
    return provider


# ── Provider metadata tests ───────────────────────────────

class TestLocalHttpProviderMetadata:
    """Tests for provider metadata."""

    def test_provider_name(self):
        provider = _make_provider()
        assert provider.name == "local-http"

    def test_provider_version(self):
        provider = _make_provider()
        assert provider.version == "local-http-v0.1"

    def test_provider_uses_external_api_false(self):
        provider = _make_provider()
        assert provider.uses_external_api is False

    def test_provider_is_explain_provider(self):
        provider = _make_provider()
        assert isinstance(provider, ExplainProvider)


# ── Fixture protocol tests ──────────────────────────────

class TestLocalHttpProviderFixtureMode:
    """Tests for fixture protocol (offline, no HTTP)."""

    def test_fixture_mode_generates_8_cards(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
        cards = provider.build_cards(storyboard)
        assert len(cards) == 8

    def test_fixture_mode_preserves_source_chunk_ids(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
        cards = provider.build_cards(storyboard)
        for card in cards:
            assert card.source_chunk_ids, f"Card '{card.title}' has empty source_chunk_ids"

    def test_fixture_mode_generates_concept_map(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        assert isinstance(concept_map, ConceptMap)
        assert concept_map.core_problem

    def test_fixture_mode_teaching_plan_has_8_steps(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        assert len(teaching_plan.steps) == 8

    def test_fixture_mode_storyboard_has_8_panels(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
        assert len(storyboard.panels) == 8

    def test_fixture_mode_cards_have_required_fields(self):
        provider = _make_provider(protocol="fixture")
        chunks = _make_chunks(4)
        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
        cards = provider.build_cards(storyboard)
        for card in cards:
            assert card.title
            assert card.explanation
            assert card.takeaway


# ── Network manifest tests ──────────────────────────────

class TestLocalHttpProviderNetworkManifest:
    """Tests for network manifest block."""

    def test_get_network_manifest_fixture_protocol(self):
        provider = _make_provider(protocol="fixture", allow_network=False)
        manifest = provider.get_network_manifest()
        assert manifest["uses_local_http"] is False
        assert manifest["allows_remote_http"] is False
        assert manifest["endpoint"] is None
        assert manifest["protocol"] == "fixture"

    def test_get_network_manifest_non_fixture_protocol_not_allowed(self):
        provider = _make_provider(protocol="ollama-chat", allow_network=False)
        manifest = provider.get_network_manifest()
        assert manifest["uses_local_http"] is False  # allow_network=False
        assert manifest["protocol"] == "ollama-chat"

    def test_get_network_manifest_non_fixture_protocol_allowed(self):
        provider = _make_provider(
            protocol="ollama-chat", allow_network=True, endpoint="http://localhost:11434/api/chat"
        )
        manifest = provider.get_network_manifest()
        assert manifest["uses_local_http"] is True
        assert manifest["endpoint"] == "http://localhost:11434/api/chat"

    def test_get_network_manifest_timeout_default(self):
        provider = _make_provider()
        manifest = provider.get_network_manifest()
        assert manifest["timeout_seconds"] == 30.0


# ── CLI integration tests ────────────────────────────────

class TestLocalHttpProviderCLI:
    """Tests for CLI integration (via output files)."""

    def test_provider_manifest_includes_network_block(self, tmp_path: Path):
        from explainlens.cli import _write_provider_manifest

        provider = _make_provider(protocol="fixture")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Write provider_manifest
        _write_provider_manifest(output_dir, provider)

        # Read and check
        manifest_path = output_dir / "provider_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["provider"] == "local-http"
        assert manifest["uses_external_api"] is False
        assert "network" in manifest
        assert manifest["network"]["uses_local_http"] is False
        assert manifest["network"]["allows_remote_http"] is False
        assert manifest["network"]["protocol"] == "fixture"

    def test_provider_manifest_uses_external_api_false(self, tmp_path: Path):
        from explainlens.cli import _write_provider_manifest

        provider = _make_provider()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        _write_provider_manifest(output_dir, provider)

        manifest_path = output_dir / "provider_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["uses_external_api"] is False
        assert manifest["requires_api_key"] is False
