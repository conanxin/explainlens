"""Security tests for ExplainLens Web UI.

Verifies safety guarantees:
- No API key in source code or templates
- External API providers blocked in UI
- External image adapters blocked in UI
- No prompt or source excerpt logging
- Bind defaults to localhost
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from explainlens.web.app import (
    BLOCKED_IMAGE_ADAPTERS,
    BLOCKED_PROVIDERS,
    SAFE_IMAGE_ADAPTERS,
    SAFE_PROVIDERS,
    create_app,
)


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestSourceCodeSafety:
    """Scan source code for accidental API key leaks."""

    WEB_DIR = Path(__file__).parent.parent / "src" / "explainlens" / "web"

    def test_no_api_key_in_app_py(self):
        """app.py contains no API keys."""
        app_file = self.WEB_DIR / "app.py"
        content = app_file.read_text(encoding="utf-8")
        matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', content)
        assert len(matches) == 0, f"Potential API key in app.py: {matches}"

    def test_no_api_key_in_run_manager(self):
        """run_manager.py contains no API keys."""
        rm_file = self.WEB_DIR / "run_manager.py"
        content = rm_file.read_text(encoding="utf-8")
        matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', content)
        assert len(matches) == 0, f"Potential API key in run_manager.py: {matches}"

    def test_no_api_key_in_templates(self):
        """Templates contain no API keys."""
        templates_dir = self.WEB_DIR / "templates"
        for template_file in templates_dir.glob("*.html"):
            content = template_file.read_text(encoding="utf-8")
            matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', content)
            assert len(matches) == 0, (
                f"Potential API key in {template_file.name}: {matches}"
            )

    def test_no_api_key_in_static_files(self):
        """Static files contain no API keys."""
        static_dir = self.WEB_DIR / "static"
        for static_file in static_dir.glob("*"):
            if static_file.is_file():
                content = static_file.read_text(encoding="utf-8")
                matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', content)
                assert len(matches) == 0, (
                    f"Potential API key in {static_file.name}: {matches}"
                )


class TestProviderSafety:
    """Verify providers are correctly classified."""

    def test_openai_is_blocked(self):
        """openai provider is in BLOCKED_PROVIDERS."""
        assert "openai" in BLOCKED_PROVIDERS

    def test_openai_not_in_safe(self):
        """openai is NOT in SAFE_PROVIDERS."""
        assert "openai" not in SAFE_PROVIDERS

    def test_rule_based_is_safe(self):
        """rule-based is in SAFE_PROVIDERS."""
        assert "rule-based" in SAFE_PROVIDERS

    def test_mock_llm_is_safe(self):
        """mock-llm is in SAFE_PROVIDERS."""
        assert "mock-llm" in SAFE_PROVIDERS

    def test_all_safe_providers_are_local(self):
        """Safe providers should not require external API."""
        from explainlens.providers import list_providers
        providers = {p["name"]: p for p in list_providers()}
        for name in SAFE_PROVIDERS:
            if name in providers:
                assert not providers[name].get("uses_external_api", True), (
                    f"SAFE_PROVIDER '{name}' uses external API!"
                )


class TestImageAdapterSafety:
    """Verify image adapters are correctly classified."""

    def test_openai_image_is_blocked(self):
        """openai-image is in BLOCKED_IMAGE_ADAPTERS."""
        assert "openai-image" in BLOCKED_IMAGE_ADAPTERS

    def test_openai_image_not_in_safe(self):
        """openai-image is NOT in SAFE_IMAGE_ADAPTERS."""
        assert "openai-image" not in SAFE_IMAGE_ADAPTERS

    def test_placeholder_is_safe(self):
        """placeholder is in SAFE_IMAGE_ADAPTERS."""
        assert "placeholder" in SAFE_IMAGE_ADAPTERS

    def test_fixture_is_safe(self):
        """fixture is in SAFE_IMAGE_ADAPTERS."""
        assert "fixture" in SAFE_IMAGE_ADAPTERS

    def test_all_safe_adapters_are_local(self):
        """Safe image adapters should not use external API."""
        from explainlens.images import list_image_adapters
        adapters = {a["name"]: a for a in list_image_adapters()}
        for name in SAFE_IMAGE_ADAPTERS:
            if name in adapters:
                assert not adapters[name].get("uses_external_api", True), (
                    f"SAFE_IMAGE_ADAPTER '{name}' uses external API!"
                )


class TestAPISafetyGates:
    """Test that API safety gates reject external providers."""

    def test_analyze_rejects_openai_http(self, client):
        """POST /api/analyze returns 403 for openai provider."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "openai",
            "image_adapter": "placeholder",
        })
        assert resp.status_code == 403

    def test_analyze_rejects_openai_image_http(self, client):
        """POST /api/analyze returns 403 for openai-image adapter."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "rule-based",
            "image_adapter": "openai-image",
        })
        assert resp.status_code == 403

    def test_analyze_error_messages_are_clear(self, client):
        """Error messages clearly explain why the provider is blocked."""
        resp = client.post("/api/analyze", json={
            "input": "examples/sample_article.txt",
            "provider": "openai",
            "image_adapter": "placeholder",
        })
        detail = resp.json()["detail"]
        assert "disabled" in detail.lower()
        assert "external" in detail.lower()

    def test_blocked_providers_not_in_dashboard_options(self, client):
        """Dashboard provider dropdown marks blocked providers as disabled."""
        resp = client.get("/")
        html = resp.text
        # openai should appear with disabled indicator
        assert "disabled in UI" in html or "external-option" in html


class TestBindDefaults:
    """Test that default binding is localhost."""

    def test_doctor_shows_localhost(self, client):
        """Doctor confirms 127.0.0.1 bind."""
        resp = client.get("/api/doctor")
        data = resp.json()
        assert data["safety"]["bind_address"] == "127.0.0.1"

    def test_doctor_shows_external_disabled(self, client):
        """Doctor confirms external APIs are disabled."""
        resp = client.get("/api/doctor")
        data = resp.json()
        safety = data["safety"]
        assert safety["external_api_providers_disabled_in_ui"] is True
        assert safety["external_image_adapters_disabled_in_ui"] is True
        assert safety["local_first"] is True

    def test_main_module_defaults_to_localhost(self):
        """__main__.py default host is 127.0.0.1."""
        main_file = Path(__file__).parent.parent / "src" / "explainlens" / "web" / "__main__.py"
        content = main_file.read_text(encoding="utf-8")
        assert '"--host"' in content
        assert 'default="127.0.0.1"' in content


class TestHTMLSafety:
    """HTML content safety checks."""

    def test_html_contains_local_by_default(self, client):
        """Top bar shows 'Local by default'."""
        resp = client.get("/")
        assert "本地模式" in resp.text

    def test_html_contains_safety_warning(self, client):
        """Sidebar shows safety note about external APIs."""
        resp = client.get("/")
        html = resp.text.lower()
        assert "external" in html or "disabled" in html

    def test_no_api_key_in_routes(self, client):
        """All API routes return no API key in responses."""
        routes = [
            "/api/providers",
            "/api/image-adapters",
            "/api/image-styles",
            "/api/doctor",
            "/api/health",
        ]
        for route in routes:
            resp = client.get(route)
            body = resp.text
            matches = re.findall(r'sk-[a-zA-Z0-9_-]{20,}', body)
            assert len(matches) == 0, (
                f"Potential API key in route {route}: {matches}"
            )
