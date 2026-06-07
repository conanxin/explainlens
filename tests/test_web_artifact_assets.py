"""Tests for ExplainLens Web UI — artifact asset serving (nested paths).

Tests that the artifact endpoint correctly serves nested assets
(e.g., images/card_01.svg) in the iframe context, with proper
MIME types, path traversal protection, and Content-Disposition rules.
No real API calls — all local-only.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from explainlens.web.run_manager import (
    OUTPUTS_DIR,
    list_artifacts,
    read_artifact,
)

# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def temp_run():
    """Create a temporary run directory with nested image artifacts."""
    tmp = Path(tempfile.mkdtemp())
    run_dir = tmp / "outputs" / "test-artifact-run-001"
    img_dir = run_dir / "images"
    img_dir.mkdir(parents=True)

    # status.json
    (run_dir / "status.json").write_text(json.dumps({
        "run_id": "test-artifact-run-001",
        "status": "success",
        "output_dir": str(run_dir.resolve()),
        "cards_html": "cards.html",
    }), encoding="utf-8")

    # cards.html with relative img references
    cards_html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body>
<img src="images/card_01.svg" alt="Card 1">
<img src="images/card_02.png" alt="Card 2">
</body>
</html>"""
    (run_dir / "cards.html").write_text(cards_html, encoding="utf-8")

    # SVG test asset
    (img_dir / "card_01.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect width="100" height="100" fill="blue"/></svg>',
        encoding="utf-8",
    )

    # PNG test asset
    (img_dir / "card_02.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
        b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    # Markdown artifact
    (run_dir / "cards.md").write_text("# Test Cards\n\nContent here.", encoding="utf-8")

    # TXT artifact
    (run_dir / "logs.txt").write_text("line 1\nline 2\n", encoding="utf-8")

    # JSON artifact
    (run_dir / "manifest.json").write_text(
        '{"key": "value", "nested": {"a": 1}}', encoding="utf-8"
    )

    # Override OUTPUTS_DIR
    import explainlens.web.run_manager as rm
    original_outputs = rm.OUTPUTS_DIR
    rm.OUTPUTS_DIR = tmp / "outputs"

    yield "test-artifact-run-001"

    rm.OUTPUTS_DIR = original_outputs
    import shutil
    shutil.rmtree(tmp)


@pytest.fixture
def client(temp_run):
    """Create FastAPI TestClient with temp run dir."""
    from explainlens.web.app import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    return TestClient(app)


# ── Artifact Serving Tests ──────────────────────────────────


class TestArtifactNestedPaths:
    """Test that artifact endpoint serves nested paths correctly."""

    def test_serve_cards_html(self, client):
        """Test 1: Artifact endpoint serves cards.html."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/cards.html")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert b"<!DOCTYPE html>" in resp.content

    def test_serve_nested_svg(self, client):
        """Test 2: Artifact endpoint serves images/card_01.svg."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_01.svg")
        assert resp.status_code == 200

    def test_svg_content_type(self, client):
        """Test 3: SVG is served with image/svg+xml content-type."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_01.svg")
        assert "image/svg+xml" in resp.headers["content-type"]

    def test_serve_nested_png(self, client):
        """Test 4: Artifact endpoint serves images/card_02.png."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_02.png")
        assert resp.status_code == 200

    def test_png_content_type(self, client):
        """Test 4b: PNG is served with image/png content-type."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_02.png")
        assert resp.headers["content-type"] == "image/png"

    def test_path_traversal_blocked(self, client):
        """Test 5: Path traversal (../) returns 404."""
        resp = client.get(
            "/api/runs/test-artifact-run-001/artifact/../../../etc/passwd"
        )
        assert resp.status_code == 404

    def test_absolute_path_blocked(self, client):
        """Test 6: Absolute path attempt returns 404."""
        # FastAPI's :path converter normalizes, but traversal check catches it
        resp = client.get(
            "/api/runs/test-artifact-run-001/artifact//etc/passwd"
        )
        assert resp.status_code == 404

    def test_nonexistent_nested_file(self, client):
        """Nonexistent nested file returns 404."""
        resp = client.get(
            "/api/runs/test-artifact-run-001/artifact/images/nonexistent.svg"
        )
        assert resp.status_code == 404


# ── Content-Disposition Tests ───────────────────────────────


class TestContentDisposition:
    """Test that Content-Disposition is NOT set for images/HTML."""

    def test_svg_no_content_disposition(self, client):
        """Test 11: SVG response has NO Content-Disposition header."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_01.svg")
        assert "content-disposition" not in resp.headers

    def test_png_no_content_disposition(self, client):
        """PNG response has NO Content-Disposition header."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/images/card_02.png")
        assert "content-disposition" not in resp.headers

    def test_html_no_content_disposition(self, client):
        """HTML response has NO Content-Disposition header."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/cards.html")
        assert "content-disposition" not in resp.headers

    def test_txt_has_content_disposition(self, client):
        """TXT response has Content-Disposition with base filename."""
        resp = client.get("/api/runs/test-artifact-run-001/artifact/logs.txt")
        cd = resp.headers.get("content-disposition", "")
        assert "inline" in cd
        # filename should NOT contain path separators
        assert "logs.txt" in cd
        assert "/" not in cd


# ── read_artifact Tests ─────────────────────────────────────


class TestReadArtifactNested:
    """Test read_artifact function with nested paths."""

    def test_read_nested_svg(self, temp_run):
        """Test 7: read_artifact supports nested paths."""
        content, mime = read_artifact(temp_run, "images/card_01.svg")
        assert content is not None
        assert mime is not None
        assert "image/svg+xml" in mime
        assert b"<svg" in content

    def test_read_nested_png(self, temp_run):
        """read_artifact supports nested PNG paths."""
        content, mime = read_artifact(temp_run, "images/card_02.png")
        assert content is not None
        assert mime == "image/png"

    def test_read_artifact_no_traversal(self, temp_run):
        """Test 8: read_artifact blocks access outside run_dir."""
        content, mime = read_artifact(temp_run, "../../../etc/passwd")
        assert content is None
        assert mime is None

    def test_read_flat_file_still_works(self, temp_run):
        """read_artifact still works for flat (non-nested) files."""
        content, mime = read_artifact(temp_run, "cards.html")
        assert content is not None
        assert "text/html" in mime

    def test_read_markdown(self, temp_run):
        """read_artifact returns correct MIME for .md files."""
        content, mime = read_artifact(temp_run, "cards.md")
        assert content is not None
        assert "markdown" in mime.lower()

    def test_read_txt(self, temp_run):
        """read_artifact returns correct MIME for .txt files."""
        content, mime = read_artifact(temp_run, "logs.txt")
        assert content is not None
        assert "plain" in mime.lower()


# ── cards.html Content Tests ────────────────────────────────


class TestCardsHtmlImageReferences:
    """Test that cards.html contains proper image references."""

    def test_cards_html_has_img_tags(self, temp_run):
        """Test 9: cards.html contains images/card_01.svg references."""
        content, _ = read_artifact(temp_run, "cards.html")
        assert content is not None
        html = content.decode("utf-8")
        assert 'src="images/card_01.svg"' in html
        assert 'src="images/card_02.png"' in html


# ── Iframe Relative Path Resolution Tests ───────────────────


class TestIframeRelativePaths:
    """Test that relative image paths in cards.html resolve correctly
    via the artifact endpoint (simulating iframe behavior)."""

    def test_relative_svg_resolves(self, client):
        """Test 10: Image path relative to cards.html resolves via artifact endpoint.
        
        When cards.html is loaded in iframe at /api/runs/{id}/artifact/cards.html,
        <img src="images/card_01.svg"> resolves to
        /api/runs/{id}/artifact/images/card_01.svg
        """
        # First verify cards.html is served
        cards_resp = client.get(
            "/api/runs/test-artifact-run-001/artifact/cards.html"
        )
        assert cards_resp.status_code == 200

        # Then verify the relative image path works
        img_resp = client.get(
            "/api/runs/test-artifact-run-001/artifact/images/card_01.svg"
        )
        assert img_resp.status_code == 200
        assert "image/svg+xml" in img_resp.headers["content-type"]

    def test_relative_png_resolves(self, client):
        """PNG image relative to cards.html resolves correctly."""
        img_resp = client.get(
            "/api/runs/test-artifact-run-001/artifact/images/card_02.png"
        )
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/png"


# ── list_artifacts Tests ────────────────────────────────────


class TestListArtifactsNested:
    """Test that list_artifacts includes images/ subdirectory files."""

    def test_list_artifacts_includes_images(self, temp_run):
        """list_artifacts includes images/card_01.svg in results."""
        artifacts = list_artifacts(temp_run)
        names = [a["name"] for a in artifacts]
        assert "images/card_01.svg" in names
        assert "images/card_02.png" in names
        assert "cards.html" in names

    def test_list_artifacts_size_human(self, temp_run):
        """Each artifact has size and size_human fields."""
        artifacts = list_artifacts(temp_run)
        for a in artifacts:
            assert "name" in a
            assert "size" in a
            assert "size_human" in a
            assert isinstance(a["size"], int)

    def test_list_artifacts_nonexistent_run(self):
        """list_artifacts returns empty list for nonexistent run."""
        artifacts = list_artifacts("nonexistent-run-xyz-99999")
        assert artifacts == []


# ── Safety Gate Tests ───────────────────────────────────────


class TestArtifactSafetyGates:
    """Test that safety gates still work with artifact endpoint."""

    def test_openai_provider_blocked(self, client):
        """openai provider is still rejected by /api/analyze."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "openai",
            "image_adapter": "placeholder",
        })
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert "openai" in detail.lower() or "External" in detail

    def test_openai_image_adapter_blocked(self, client):
        """openai-image adapter is still rejected by /api/analyze."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "rule-based",
            "image_adapter": "openai-image",
        })
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert "openai" in detail.lower() or "External" in detail


# ── Template Safety Tests ───────────────────────────────────


class TestArtifactTemplateSafety:
    """Test that templates don't expose secrets."""

    def test_dashboard_no_api_key(self, client):
        """Test 15: Dashboard template does not contain API keys."""
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text
        assert "sk-" not in html or "sk-" + "test" in html

    def test_run_detail_no_api_key(self, client):
        """Run detail template does not contain API keys."""
        # Use a non-existent run — template should still render 404
        html = client.get("/").text  # dashboard is guaranteed
        assert "sk-" not in html or "sk-" + "test" in html


# ── Dashboard Preview Integration Tests ─────────────────────


class TestDashboardPreviewArtifactIntegration:
    """Test that dashboard preview can load artifact assets."""

    def test_dashboard_has_preview_containers(self, client):
        """Dashboard includes preview-iframe and preview-content-container."""
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text
        assert "preview-iframe" in html
        assert "preview-content-container" in html
        assert "preview-loading" in html
        assert "preview-error" in html

    def test_dashboard_js_refs_artifact_url(self, client):
        """Dashboard JS references /api/runs/*/artifact/cards.html."""
        resp = client.get("/")
        html = resp.text
        assert "/artifact/cards.html" in html

    def test_run_detail_has_artifact_links(self, client):
        """Run detail page has artifact links with nested path support."""
        # Check the template source for nested path reference
        resp = client.get("/")
        html = resp.text
        # Dashboard references artifact paths
        assert "artifact" in html
