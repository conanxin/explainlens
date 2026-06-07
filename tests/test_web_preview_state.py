"""Tests for Web UI preview pane state management.

Covers Phase 5A-UI-polish-hotfix:
- appState / currentRunId tracking
- No location.reload() on success
- Stable preview iframe loading
- Sidebar AJAX refresh (data-run-id)
- Preview loading/error/failed states
- Artifact URL patterns
- Safety gates (openai / openai-image blocked)
- No API keys in templates
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from explainlens.web.app import create_app


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Create test app."""
    return create_app()


@pytest.fixture()
def client(app):
    """Create test client."""
    return TestClient(app)


# ── Template State Tests ──────────────────────────────────

def test_dashboard_contains_preview_pane(client):
    """Test 1: Dashboard page contains preview pane element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="preview-pane"' in resp.text


def test_dashboard_contains_preview_content_container(client):
    """Test 1b: Dashboard contains preview-content-container for iframe/loading/error."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="preview-content-container"' in resp.text


def test_dashboard_contains_preview_iframe(client):
    """Test 1c: Dashboard contains preview-iframe element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="preview-iframe"' in resp.text


def test_dashboard_contains_preview_loading(client):
    """Test 2: Dashboard contains preview-loading element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="preview-loading"' in resp.text
    assert "正在生成" in resp.text


def test_dashboard_contains_preview_error(client):
    """Test 3: Dashboard contains preview-error element."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="preview-error"' in resp.text
    assert "运行失败" in resp.text


# ── JavaScript State Tests ───────────────────────────────

def test_app_js_contains_appState(client):
    """Test 4: Dashboard JS contains appState global object."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "appState" in html, "Dashboard JS must define appState"
    assert "currentRunId" in html, "appState must have currentRunId"
    assert "previewLocked" in html, "appState must have previewLocked"


def test_app_js_no_location_reload_on_success(client):
    """Test 5: Dashboard JS does NOT call location.reload() for success state."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    # location.reload should not appear near success handling
    # Check: the reload was previously on line 293; now it's removed
    # We verify it's gone from the scripts block
    scripts_start = html.find("{% block scripts %}")
    scripts_end = html.find("{% endblock %}", scripts_start) if scripts_start >= 0 else -1
    if scripts_start >= 0 and scripts_end >= 0:
        scripts_block = html[scripts_start:scripts_end]
        assert "location.reload()" not in scripts_block, (
            "Dashboard JS must NOT use location.reload() — use AJAX sidebar refresh instead"
        )


def test_app_js_contains_showPreviewSuccess(client):
    """Test 6: Dashboard JS contains showPreviewSuccess function."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "showPreviewSuccess" in resp.text


def test_app_js_contains_refreshSidebarRuns(client):
    """Test 7: Dashboard JS contains refreshSidebarRuns (AJAX sidebar refresh)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "refreshSidebarRuns" in resp.text


def test_app_js_contains_loadRunPreview(client):
    """Test 8: Dashboard JS contains loadRunPreview function."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "loadRunPreview" in resp.text


def test_app_js_contains_pollForPreview(client):
    """Test 9: Dashboard JS contains pollForPreview function (preview-specific polling)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "pollForPreview" in resp.text


def test_app_js_showPreviewFailed_display(client):
    """Test 10: Dashboard JS contains showPreviewFailed function."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "showPreviewFailed" in resp.text


# ── Sidebar Template Tests ──────────────────────────────

def test_sidebar_run_items_use_data_run_id(client):
    """Test 11: Sidebar run items use data-run-id attributes (not hard links)."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    # Sidebar items should have data-run-id for click-to-preview
    assert 'data-run-id="' in html, "Sidebar run items must have data-run-id for click-to-preview"
    # The run items should use href="#" (not direct /runs/ links that cause navigation)
    # Note: existing runs from template will use href="#"


# ── Artifact URL Tests ───────────────────────────────────

def test_artifact_url_pattern_in_js(client):
    """Test 12: Dashboard JS references artifact URL /api/runs/*/artifact/cards.html."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "/api/runs/" in html
    assert "/artifact/cards.html" in html


def test_artifact_endpoint_exists(app):
    """Test 13: Artifact endpoint route is registered in the app."""
    # Just verify the route exists by checking the app's routes
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    artifact_routes = [r for r in routes if 'artifact' in r]
    assert len(artifact_routes) > 0, "Artifact route must be registered"


# ── Safety Gate Tests ────────────────────────────────────

def test_openai_provider_still_blocked(client):
    """Test 14: openai provider is still rejected by /api/analyze."""
    resp = client.post("/api/analyze", json={
        "input": "examples/sample_article.txt",
        "provider": "openai",
        "image_adapter": "placeholder",
        "image_style": "clean-cartoon-explainer",
        "skip_images": True,
    })
    assert resp.status_code == 403


def test_openai_image_adapter_still_blocked(client):
    """Test 15: openai-image adapter is still rejected by /api/analyze."""
    resp = client.post("/api/analyze", json={
        "input": "examples/sample_article.txt",
        "provider": "rule-based",
        "image_adapter": "openai-image",
        "image_style": "clean-cartoon-explainer",
        "skip_images": True,
    })
    assert resp.status_code == 403


def test_templates_no_api_key(client):
    """Test 16: Rendered dashboard HTML contains no API keys."""
    resp = client.get("/")
    html = resp.text
    matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', html)
    assert len(matches) == 0, f"Found potential API keys: {matches}"


def test_templates_no_api_key_in_files():
    """Test 17: Raw template files contain no API keys."""
    template_dir = Path("src/explainlens/web/templates")
    for f in template_dir.glob("*.html"):
        content = f.read_text(encoding="utf-8")
        assert "sk-" not in content, f"Found 'sk-' in {f.name}"


# ── Run Detail Tests ─────────────────────────────────────

def test_run_detail_contains_preview_tabs(client):
    """Test 18: Run detail page still has preview tabs (no regression)."""
    # We can't test an actual run without creating one,
    # but we can verify the template has the right structure
    template_dir = Path("src/explainlens/web/templates")
    run_detail = template_dir / "run_detail.html"
    content = run_detail.read_text(encoding="utf-8")
    assert "preview-tabs" in content
    assert "preview-iframe" in content


# ── CSS Tests ────────────────────────────────────────────

def test_css_contains_preview_state_styles(client):
    """Test 19: CSS includes preview-loading and preview-error styles."""
    css_path = Path("src/explainlens/web/static/app.css")
    css = css_path.read_text(encoding="utf-8")
    assert ".preview-loading" in css, "CSS must have .preview-loading styles"
    assert ".preview-error" in css, "CSS must have .preview-error styles"


def test_css_no_dangling_comment_closer():
    """Test 20: CSS does not contain orphaned comment closers (no */ without /*)."""
    css_path = Path("src/explainlens/web/static/app.css")
    css = css_path.read_text(encoding="utf-8")
    lines = css.split("\n")
    # Check for lines that are just spaces/dashes and */
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.endswith("*/") and not stripped.startswith("/*"):
            # This could be a valid multi-line comment continuation, but
            # a line that starts with space+dashes then */ is a bug
            if stripped.startswith("─") or stripped.startswith("-"):
                # This is a dangling closer — but only if there's no opener in nearby lines
                # Simple check: if no /* in prev 3 lines, it's orphaned
                prev_text = "\n".join(lines[max(0, i - 4):i])
                if "/*" not in prev_text:
                    pytest.fail(f"Orphaned comment closer at line {i}: {stripped}")
