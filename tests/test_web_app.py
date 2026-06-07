"""Tests for ExplainLens Web UI FastAPI application.

Tests for API endpoints, template rendering, and route behavior.
Uses FastAPI TestClient for HTTP-level testing.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from explainlens.web.app import create_app
from explainlens.web.run_manager import OUTPUTS_DIR


@pytest.fixture
def client():
    """Create a test client for the web app."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestWebApp:
    """Basic web app tests."""

    def test_app_creates(self):
        """App factory creates a FastAPI app."""
        app = create_app()
        assert app is not None
        assert app.title == "ExplainLens Web UI"

    def test_get_root_returns_200(self, client):
        """GET / returns dashboard HTML."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_get_root_contains_layout(self, client):
        """Dashboard HTML contains Codex-style layout markers."""
        resp = client.get("/")
        html = resp.text.lower()
        assert "sidebar" in html, "Dashboard must contain sidebar element"
        assert "workspace" in html, "Dashboard must contain workspace element"
        assert "preview" in html, "Dashboard must contain preview pane element"

    def test_get_root_contains_new_run_form(self, client):
        """Dashboard has the New Run form."""
        resp = client.get("/")
        html = resp.text
        assert "new-run-form" in html
        assert "开始生成" in html

    def test_api_health(self, client):
        """Health check returns OK."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestAPIProviders:
    """API endpoint tests for providers."""

    def test_api_providers_returns_list(self, client):
        """GET /api/providers returns provider list."""
        resp = client.get("/api/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_api_providers_has_rule_based(self, client):
        """Provider list includes rule-based."""
        resp = client.get("/api/providers")
        data = resp.json()
        names = [p["name"] for p in data]
        assert "rule-based" in names

    def test_api_providers_has_mock_llm(self, client):
        """Provider list includes mock-llm."""
        resp = client.get("/api/providers")
        data = resp.json()
        names = [p["name"] for p in data]
        assert "mock-llm" in names

    def test_api_providers_openai_blocked(self, client):
        """openai provider is marked as blocked_in_ui."""
        resp = client.get("/api/providers")
        data = resp.json()
        for p in data:
            if p["name"] == "openai":
                assert p["blocked_in_ui"] is True, "openai must be blocked in UI"

    def test_provider_format_has_fields(self, client):
        """Each provider entry has required fields."""
        resp = client.get("/api/providers")
        data = resp.json()
        for p in data:
            assert "name" in p
            assert "status" in p
            assert "uses_external_api" in p
            assert "blocked_in_ui" in p


class TestAPIImageAdapters:
    """API endpoint tests for image adapters."""

    def test_api_image_adapters_returns_list(self, client):
        """GET /api/image-adapters returns adapter list."""
        resp = client.get("/api/image-adapters")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_api_image_adapters_has_placeholder(self, client):
        """Image adapter list includes placeholder."""
        resp = client.get("/api/image-adapters")
        data = resp.json()
        names = [a["name"] for a in data]
        assert "placeholder" in names

    def test_api_image_adapters_has_fixture(self, client):
        """Image adapter list includes fixture."""
        resp = client.get("/api/image-adapters")
        data = resp.json()
        names = [a["name"] for a in data]
        assert "fixture" in names

    def test_api_image_adapters_openai_image_blocked(self, client):
        """openai-image adapter is marked as blocked_in_ui."""
        resp = client.get("/api/image-adapters")
        data = resp.json()
        for a in data:
            if a["name"] == "openai-image":
                assert a["blocked_in_ui"] is True


class TestAPIImageStyles:
    """API endpoint tests for image styles."""

    def test_api_image_styles_returns_list(self, client):
        """GET /api/image-styles returns style list."""
        resp = client.get("/api/image-styles")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_api_image_styles_has_clean_cartoon(self, client):
        """Style list includes clean-cartoon-explainer."""
        resp = client.get("/api/image-styles")
        data = resp.json()
        names = [s["name"] for s in data]
        assert "clean-cartoon-explainer" in names


class TestAPIDoctor:
    """API endpoint tests for doctor."""

    def test_api_doctor_returns_200(self, client):
        """GET /api/doctor returns 200."""
        resp = client.get("/api/doctor")
        assert resp.status_code == 200

    def test_api_doctor_has_safety_info(self, client):
        """Doctor includes safety information."""
        resp = client.get("/api/doctor")
        data = resp.json()
        assert "safety" in data
        assert data["safety"]["local_first"] is True
        assert "127.0.0.1" in data["safety"]["bind_address"]


class TestAPIRuns:
    """API tests for run management."""

    def test_api_runs_list(self, client):
        """GET /api/runs returns a list."""
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_api_runs_nonexistent(self, client):
        """GET /api/runs/nonexistent returns 404."""
        resp = client.get("/api/runs/nonexistent-run-99999")
        assert resp.status_code == 404

    def test_api_runs_artifact_nonexistent(self, client):
        """GET artifact for non-existent run returns 404."""
        resp = client.get("/api/runs/nonexistent-run-99999/artifact/cards.html")
        assert resp.status_code == 404


class TestAPIAnalyze:
    """API tests for the analyze endpoint."""

    def test_analyze_rejects_openai_provider(self, client):
        """POST /api/analyze rejects openai provider."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "openai",
            "image_adapter": "placeholder",
        })
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_analyze_rejects_openai_image_adapter(self, client):
        """POST /api/analyze rejects openai-image adapter."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "rule-based",
            "image_adapter": "openai-image",
        })
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_analyze_accepts_safe_config(self, client):
        """POST /api/analyze accepts mock-llm + placeholder."""
        # Clean up any previous test run
        import shutil
        for d in Path("outputs").iterdir():
            if d.is_dir() and "test_web" in d.name:
                shutil.rmtree(d, ignore_errors=True)

        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "mock-llm",
            "image_adapter": "placeholder",
            "image_style": "clean-cartoon-explainer",
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["status"] == "running"
        assert "run_id" in data

        run_id = data["run_id"]
        # Wait for analysis to complete
        for _ in range(60):
            time.sleep(0.5)
            status_resp = client.get(f"/api/runs/{run_id}")
            if status_resp.status_code == 200:
                s = status_resp.json()
                if s["status"] in ("success", "failed"):
                    break

        # Verify status
        final_resp = client.get(f"/api/runs/{run_id}")
        assert final_resp.status_code == 200
        final = final_resp.json()
        assert final["status"] == "success", f"Run failed: {final.get('error', 'unknown')}"

        # Verify status.json exists
        status_path = Path(final["output_dir"]) / "status.json"
        assert status_path.exists()

        # Verify cards.html exists
        cards_path = Path(final["output_dir"]) / "cards.html"
        assert cards_path.exists(), f"cards.html not found at {cards_path}"

        # Cleanup
        shutil.rmtree(Path(final["output_dir"]), ignore_errors=True)

    def test_analyze_creates_cards_html(self, client):
        """Running analyze with mock-llm + placeholder creates cards.html."""
        import shutil

        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "mock-llm",
            "image_adapter": "placeholder",
        })
        assert resp.status_code == 201
        run_id = resp.json()["run_id"]

        # Wait for completion
        for _ in range(60):
            time.sleep(0.5)
            s_resp = client.get(f"/api/runs/{run_id}")
            if s_resp.status_code == 200 and s_resp.json()["status"] != "running":
                break

        final = client.get(f"/api/runs/{run_id}").json()
        assert final["status"] == "success"

        # Verify artifact is accessible
        art_resp = client.get(f"/api/runs/{run_id}/artifact/cards.html")
        assert art_resp.status_code == 200
        assert "text/html" in art_resp.headers["content-type"]

        # Cleanup
        shutil.rmtree(Path(final["output_dir"]), ignore_errors=True)

    def test_analyze_rejects_missing_input(self, client):
        """POST /api/analyze rejects empty input."""
        resp = client.post("/api/analyze", json={
            "input": "",
            "provider": "rule-based",
        })
        assert resp.status_code == 400

    def test_analyze_rejects_nonexistent_file(self, client):
        """POST /api/analyze rejects non-existent file."""
        resp = client.post("/api/analyze", json={
            "input": "nonexistent_file_xyz.txt",
            "provider": "rule-based",
        })
        assert resp.status_code == 400


class TestUILayout:
    """Tests for UI layout and template content."""

    def test_dashboard_three_column_layout(self, client):
        """Dashboard has three-column layout markers."""
        resp = client.get("/")
        html = resp.text
        assert 'class="sidebar"' in html
        assert 'class="workspace"' in html
        assert 'class="preview-pane"' in html

    def test_dashboard_has_new_run_button(self, client):
        """Dashboard has Start Run button."""
        resp = client.get("/")
        assert "开始生成" in resp.text

    def test_dashboard_has_provider_dropdown(self, client):
        """Dashboard has provider select dropdown."""
        resp = client.get("/")
        html = resp.text
        assert 'id="provider"' in html
        assert 'rule-based' in html

    def test_dashboard_has_image_adapter_dropdown(self, client):
        """Dashboard has image adapter select dropdown."""
        resp = client.get("/")
        html = resp.text
        assert 'id="image-adapter"' in html
        assert 'placeholder' in html

    def test_dashboard_has_style_dropdown(self, client):
        """Dashboard has image style select dropdown."""
        resp = client.get("/")
        html = resp.text
        assert 'id="image-style"' in html

    def test_no_api_key_in_html(self, client):
        """Rendered HTML contains no API keys."""
        resp = client.get("/")
        html = resp.text
        import re
        # Look for sk- patterns that look like real keys
        matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', html)
        assert len(matches) == 0, f"Found potential API keys in HTML: {matches}"


class TestAppBinding:
    """Tests for app binding defaults."""

    def test_app_name(self):
        """App is named ExplainLens Web UI."""
        app = create_app()
        assert "ExplainLens" in app.title

    def test_default_bind_host_is_localhost(self, client):
        """Doctor endpoint confirms localhost binding."""
        resp = client.get("/api/doctor")
        data = resp.json()
        assert "127.0.0.1" in data["safety"]["bind_address"]
        assert data["safety"]["external_api_providers_disabled_in_ui"] is True
        assert data["safety"]["external_image_adapters_disabled_in_ui"] is True
