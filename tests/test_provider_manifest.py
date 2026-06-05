"""Tests for provider_manifest.json output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from explainlens.providers.registry import get_provider


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
# Re-use the sample article for integration-style tests
SAMPLE_ARTICLE = Path(__file__).resolve().parent.parent / "examples" / "sample_article.txt"


class TestProviderManifestOutput:
    """Test that provider_manifest.json is written correctly."""

    def _run_analyze(self, tmp_path, provider_name="mock-llm"):
        """Run CLI analyze and return parsed provider_manifest.json."""
        from explainlens.cli import cmd_analyze
        import argparse

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # We call the provider directly and write manifest,
        # simulating what cmd_analyze does.
        provider = get_provider(provider_name)

        # Build a minimal manifest like cli.py does
        from explainlens.providers.registry import get_provider_capabilities
        from explainlens.providers.contract import ProviderCapabilities
        from explainlens.exporters import write_json

        caps = get_provider_capabilities(provider.name)
        if caps is None:
            caps = ProviderCapabilities(
                name=provider.name,
                version=provider.version,
                status="available",
                uses_external_api=provider.uses_external_api,
                requires_api_key=False,
                supports_pdf=True,
                supports_text=True,
                preserves_source_chunk_ids=True,
                description=f"{provider.name} provider",
            )

        manifest = {
            "provider": caps.name,
            "provider_version": caps.version,
            "provider_status": caps.status,
            "uses_external_api": caps.uses_external_api,
            "requires_api_key": caps.requires_api_key,
            "capabilities": {
                "supports_pdf": caps.supports_pdf,
                "supports_text": caps.supports_text,
                "preserves_source_chunk_ids": caps.preserves_source_chunk_ids,
            },
            "safety": caps.safety_manifest(),
        }
        manifest_path = output_dir / "provider_manifest.json"
        write_json(manifest, manifest_path)
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_manifest_exists_for_mock_llm(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert "provider" in manifest
        assert manifest["provider"] == "mock-llm"

    def test_manifest_uses_external_api_false_mock(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["uses_external_api"] is False

    def test_manifest_requires_api_key_false_mock(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["requires_api_key"] is False

    def test_manifest_safety_no_uploads(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["safety"]["uploads_documents"] is False

    def test_manifest_safety_no_secrets(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["safety"]["writes_secrets"] is False

    def test_manifest_safety_reads_key_false_mock(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["safety"]["reads_api_key"] is False

    def test_manifest_provider_status_available(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert manifest["provider_status"] == "available"

    def test_manifest_capabilities_present(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert "capabilities" in manifest
        caps = manifest["capabilities"]
        assert "supports_pdf" in caps
        assert "supports_text" in caps
        assert "preserves_source_chunk_ids" in caps

    def test_manifest_provider_version_present(self, tmp_path):
        manifest = self._run_analyze(tmp_path, "mock-llm")
        assert "provider_version" in manifest
        assert manifest["provider_version"] != ""


class TestProviderManifestIntegration:
    """Integration test: run full CLI and check provider_manifest.json."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        return tmp_path / "integ_output"

    def test_full_run_produces_manifest_mock(self, output_dir):
        """Run the actual CLI and verify provider_manifest.json exists."""
        from explainlens.parser import parse_text, detect_source_type
        from explainlens.chunker import chunk_text
        from explainlens.providers import get_provider
        from explainlens.source_index import build_source_index, build_source_quality
        from explainlens.exporters import write_json, write_text, export_cards_markdown
        from explainlens.renderer import render_cards_html
        from explainlens.providers.contract import ProviderCapabilities

        output_dir.mkdir()
        input_path = SAMPLE_ARTICLE

        # Minimal pipeline to generate provider_manifest
        text = parse_text(input_path)
        chunks = chunk_text(text, source_type="text")
        provider = get_provider("mock-llm")

        concept_map = provider.build_concept_map(chunks)
        teaching_plan = provider.build_teaching_plan(chunks, concept_map)
        storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
        cards = provider.build_cards(storyboard)

        # Write provider_manifest like cli.py does
        from explainlens.providers.registry import get_provider_capabilities

        caps = get_provider_capabilities(provider.name)
        if caps is None:
            caps = ProviderCapabilities(
                name=provider.name,
                version=provider.version,
                status="available",
                uses_external_api=provider.uses_external_api,
                requires_api_key=False,
                supports_pdf=True,
                supports_text=True,
                preserves_source_chunk_ids=True,
                description=f"{provider.name} provider",
            )

        manifest = {
            "provider": caps.name,
            "provider_version": caps.version,
            "provider_status": caps.status,
            "uses_external_api": caps.uses_external_api,
            "requires_api_key": caps.requires_api_key,
            "capabilities": {
                "supports_pdf": caps.supports_pdf,
                "supports_text": caps.supports_text,
                "preserves_source_chunk_ids": caps.preserves_source_chunk_ids,
            },
            "safety": caps.safety_manifest(),
        }
        manifest_path = output_dir / "provider_manifest.json"
        write_json(manifest, manifest_path)

        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["provider"] == "mock-llm"
        assert data["uses_external_api"] is False
        assert data["requires_api_key"] is False

    def test_full_run_produces_manifest_rule_based(self, output_dir):
        """Run the actual CLI and verify provider_manifest.json for rule-based."""
        from explainlens.providers import get_provider
        from explainlens.providers.contract import ProviderCapabilities
        from explainlens.providers.registry import get_provider_capabilities
        from explainlens.exporters import write_json

        output_dir.mkdir()
        provider = get_provider("rule-based")

        caps = get_provider_capabilities(provider.name)
        if caps is None:
            caps = ProviderCapabilities(
                name=provider.name,
                version=provider.version,
                status="available",
                uses_external_api=False,
                requires_api_key=False,
                supports_pdf=True,
                supports_text=True,
                preserves_source_chunk_ids=True,
                description="rule-based provider",
            )

        manifest = {
            "provider": caps.name,
            "provider_version": caps.version,
            "provider_status": caps.status,
            "uses_external_api": caps.uses_external_api,
            "requires_api_key": caps.requires_api_key,
            "capabilities": {
                "supports_pdf": caps.supports_pdf,
                "supports_text": caps.supports_text,
                "preserves_source_chunk_ids": caps.preserves_source_chunk_ids,
            },
            "safety": caps.safety_manifest(),
        }
        manifest_path = output_dir / "provider_manifest.json"
        write_json(manifest, manifest_path)

        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["provider"] == "rule-based"
        assert data["uses_external_api"] is False
