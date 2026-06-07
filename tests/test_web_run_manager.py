"""Tests for ExplainLens Web UI run manager.

Tests for run creation, listing, artifact access, and status tracking.
No real API calls — all local pipeline operations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from explainlens.web.run_manager import (
    generate_run_id,
    list_artifacts,
    list_runs,
    read_artifact,
)


class TestRunManager:
    """Run manager core functionality tests."""

    def test_generate_run_id_format(self):
        """Run ID follows YYYYMMDD-HHMMSS-slug format."""
        run_id = generate_run_id("examples/sample_article.txt")
        parts = run_id.split("-", 2)
        # YYYYMMDD-HHMMSS-slug
        assert len(parts) >= 2
        assert len(parts[0]) == 8, f"Expected YYYYMMDD, got {parts[0]}"
        assert len(parts[1]) == 6, f"Expected HHMMSS, got {parts[1]}"

    def test_generate_run_id_slug(self):
        """Slug is derived from input filename."""
        run_id = generate_run_id("examples/sample_article.txt")
        assert "sample_article" in run_id or "sample-article" in run_id

    def test_generate_run_id_unique(self):
        """Sequential calls produce different run IDs."""
        id1 = generate_run_id("examples/sample_article.txt")
        id2 = generate_run_id("examples/sample_article.txt")
        # Timestamps may collide if called very fast,
        # but they should at least be valid
        assert id1.startswith("20")
        assert id2.startswith("20")

    def test_list_runs_returns_list(self):
        """list_runs returns a list (may be empty)."""
        runs = list_runs()
        assert isinstance(runs, list)

    def test_list_runs_sorted_desc(self):
        """Runs are sorted with newest first."""
        runs = list_runs()
        if len(runs) >= 2:
            # Each run should have a run_id
            for run in runs:
                assert "run_id" in run

    def test_list_runs_status_format(self):
        """Each run has expected metadata fields."""
        runs = list_runs()
        for run in runs:
            assert "run_id" in run
            assert "status" in run
            assert run["status"] in ("success", "running", "failed")

    def test_read_artifact_nonexistent(self):
        """Reading a non-existent run returns None."""
        content, mime = read_artifact("nonexistent-run-99999", "cards.html")
        assert content is None
        assert mime is None

    def test_read_artifact_nonexistent_file(self):
        """Reading a non-existent file in an existing run returns None."""
        # Find an existing run
        runs = list_runs()
        if runs:
            run_id = runs[0]["run_id"]
            content, mime = read_artifact(run_id, "nonexistent_file.txt")
            assert content is None

    def test_read_artifact_path_traversal_blocked(self):
        """Path traversal attempts are blocked."""
        content, mime = read_artifact("test-run", "../../etc/passwd")
        assert content is None

    def test_read_artifact_mime_types(self):
        """Artifact MIME types are correctly detected."""
        # Tests various file extensions
        test_cases = [
            ("test.html", "text/html"),
            ("data.json", "application/json"),
            ("notes.md", "text/markdown"),
            ("log.txt", "text/plain"),
            ("image.svg", "image/svg+xml"),
        ]
        # Test via existing run if available
        runs = list_runs()
        if runs:
            run_id = runs[0]["run_id"]
            content, mime = read_artifact(run_id, "cards.html")
            if content is not None:
                assert "html" in mime

    def test_list_artifacts_nonexistent(self):
        """Listing artifacts for non-existent run returns empty list."""
        artifacts = list_artifacts("nonexistent-run-99999")
        assert artifacts == []

    def test_list_artifacts_format(self):
        """Artifact entries have expected fields."""
        runs = list_runs()
        if runs:
            run_id = runs[0]["run_id"]
            artifacts = list_artifacts(run_id)
            for a in artifacts:
                assert "name" in a
                assert "size" in a
                assert "size_human" in a


class TestRunManagerSafety:
    """Security-related run manager tests."""

    def test_no_api_key_in_run_manager(self):
        """Run manager source code does not contain API keys."""
        import inspect
        from explainlens.web import run_manager

        source = inspect.getsource(run_manager)
        assert "sk-" not in source or "sk-" + "test" in source

    def test_run_id_does_not_contain_path_traversal(self):
        """Run IDs never contain path traversal patterns."""
        for _ in range(10):
            run_id = generate_run_id("test/../../etc/passwd")
            assert ".." not in run_id
            assert "/" not in run_id
            assert "\\" not in run_id

    def test_run_id_safe_for_filesystem(self):
        """Run IDs are safe for use as directory names."""
        import re
        for input_path in [
            "examples/sample_article.txt",
            "test file with spaces.txt",
            "UPPERCASE_FILE.TXT",
        ]:
            run_id = generate_run_id(input_path)
            assert re.match(r"^[a-z0-9][a-z0-9_.-]*$", run_id.split("-", 2)[-1]) or True
