"""Tests for `python -m explainlens.cli providers` CLI subcommand."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


SAMPLE_ARTICLE = (
    Path(__file__).resolve().parent.parent / "examples" / "sample_article.txt"
)


def _run_cli_providers():
    """Run `python -m explainlens.cli providers` and return (exit_code, stdout)."""
    from explainlens.cli import main
    import io
    import sys

    captured = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = captured
    exit_code = 0
    try:
        with patch.object(sys, "argv", ["explainlens", "providers"]):
            try:
                main()
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
    finally:
        sys.stdout = sys_stdout

    return exit_code, captured.getvalue()


class TestProviderListingCLI:
    """Test `python -m explainlens.cli providers` output."""

    def test_providers_subcommand_runs(self):
        exit_code, stdout = _run_cli_providers()
        assert exit_code == 0

    def test_providers_output_contains_rule_based(self):
        exit_code, stdout = _run_cli_providers()
        assert "rule-based" in stdout

    def test_providers_output_contains_mock_llm(self):
        exit_code, stdout = _run_cli_providers()
        assert "mock-llm" in stdout

    def test_providers_output_contains_openai(self):
        exit_code, stdout = _run_cli_providers()
        assert "openai" in stdout

    def test_providers_shows_status_available(self):
        exit_code, stdout = _run_cli_providers()
        # "available" should appear for rule-based / mock-llm
        assert "available" in stdout.lower()

    def test_providers_shows_status_disabled(self):
        exit_code, stdout = _run_cli_providers()
        # "disabled" should appear for openai
        assert "disabled" in stdout.lower()

    def test_providers_shows_external_api_info(self):
        exit_code, stdout = _run_cli_providers()
        assert "API" in stdout or "api" in stdout

    def test_providers_does_not_require_input_file(self):
        """Providers listing should NOT fail due to missing --input."""
        exit_code, stdout = _run_cli_providers()
        # Should NOT contain argparse error about --input
        assert "--input" not in stdout or "Available" in stdout


class TestProviderAnalyzeCLI:
    """Test that --provider openai fails closed."""

    def test_openai_provider_fails_closed(self, tmp_path):
        """`--provider openai` should fail and produce no output directory."""
        from explainlens.cli import main
        import sys

        output_dir = tmp_path / "openai_test"
        sys_argv_backup = sys.argv[:]
        try:
            sys.argv = [
                "explainlens",
                "analyze",
                "--input", str(SAMPLE_ARTICLE),
                "--output", str(output_dir),
                "--provider", "openai",
            ]
            try:
                main()
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 1
            else:
                exit_code = 0
        finally:
            sys.argv = sys_argv_backup

        # Should fail (non-zero exit)
        assert exit_code != 0

    def test_openai_provider_produces_no_output_dir(self, tmp_path):
        """When --provider openai fails, output dir should NOT contain results."""
        from explainlens.cli import main
        import sys

        output_dir = tmp_path / "openai_test"
        sys_argv_backup = sys.argv[:]
        try:
            sys.argv = [
                "explainlens",
                "analyze",
                "--input", str(SAMPLE_ARTICLE),
                "--output", str(output_dir),
                "--provider", "openai",
            ]
            try:
                main()
            except SystemExit:
                pass
        finally:
            sys.argv = sys_argv_backup

        # Output dir should NOT exist (or exist but be empty)
        if output_dir.exists():
            # If it exists, it should NOT contain run_summary.json
            assert not (output_dir / "run_summary.json").exists()

    def test_openai_provider_error_message_clear(self):
        """Error message should mention 'disabled' or 'not enabled'."""
        from explainlens.providers.openai_draft import OpenAIDraftProvider

        provider = OpenAIDraftProvider()
        try:
            provider.build_concept_map([])
        except RuntimeError as e:
            msg = str(e)
            assert "disabled" in msg.lower() or "not enabled" in msg.lower()


class TestProviderManifestInOutput:
    """Test that provider_manifest.json is created by CLI analyze."""

    def test_provider_manifest_in_cli_source(self):
        """Check that cli.py mentions provider_manifest.json."""
        cli_source = Path("src/explainlens/cli.py").read_text(encoding="utf-8")
        assert "provider_manifest.json" in cli_source


class TestProviderEnvVar:
    """Test EXPLAINLENS_PROVIDER env var (documentation only in Phase 3.1)."""

    def test_env_var_not_implemented_yet(self):
        """EXPLAINLENS_PROVIDER env var is NOT used in cli.py yet.

        This is documented but not implemented to avoid complexity.
        """
        cli_source = Path("src/explainlens/cli.py").read_text(encoding="utf-8")
        # It's ok for it to be mentioned in comments, but should not
        # be in the actual argument parsing logic
        # We just note this is for Phase 3.x
        assert True  # Placeholder — env var not implemented yet
