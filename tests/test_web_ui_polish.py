"""Tests for Web UI polish features.

Covers Phase 5A-UI-polish requirements 8-10, 14-15,
and additional UI polish verification.
"""

import pytest
from explainlens.web.app import create_app, BLOCKED_PROVIDERS, BLOCKED_IMAGE_ADAPTERS


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Create test app."""
    return create_app()


@pytest.fixture()
def client(app):
    """Create test client."""
    from starlette.testclient import TestClient
    return TestClient(app)


# ── Provider Dropdown Chinese Labels ───────────────────────

def test_provider_dropdown_contains_chinese_rule_based(client):
    """Test 8a: provider 下拉包含「规则拆解」（rule-based）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "规则拆解" in resp.text


def test_provider_dropdown_contains_chinese_mock_llm(client):
    """Test 8b: provider 下拉包含「本地模拟 LLM」（mock-llm）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地模拟 LLM" in resp.text


def test_provider_dropdown_contains_chinese_local_fixture(client):
    """Test 8c: provider 下拉包含「本地协议测试」（local-fixture）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地协议测试" in resp.text


def test_provider_dropdown_contains_chinese_local_http(client):
    """Test 8d: provider 下拉包含「本地 HTTP 模型」（local-http）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地 HTTP" in resp.text


# ── Image Adapter Dropdown Chinese Labels ─────────────────

def test_image_adapter_dropdown_contains_chinese_placeholder(client):
    """Test 9a: image adapter 下拉包含「本地 SVG 占位图」（placeholder）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地 SVG" in resp.text


def test_image_adapter_dropdown_contains_chinese_fixture(client):
    """Test 9b: image adapter 下拉包含「本地 SVG Fixture」（fixture）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地 SVG Fixture" in resp.text


# ── Image Style Dropdown Chinese Labels ───────────────────

def test_image_style_dropdown_contains_chinese_clean_cartoon(client):
    """Test 10a: image style 下拉包含「清爽卡通讲解」（clean-cartoon-explainer）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "清爽卡通讲解" in resp.text


def test_image_style_dropdown_contains_chinese_whiteboard(client):
    """Test 10b: image style 下拉包含「白板图解」（whiteboard）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "白板图解" in resp.text


def test_image_style_dropdown_contains_chinese_storybook(client):
    """Test 10c: image style 下拉包含「绘本风」（storybook）"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "绘本风" in resp.text


# ── External Provider Blocked in UI ───────────────────────

def test_openai_provider_rejected_by_api(client):
    """Test 14: openai provider 仍然被 UI API 拒绝"""
    resp = client.post(
        "/api/analyze",
        json={
            "input": "examples/sample_article.txt",
            "provider": "openai",
            "image_adapter": "placeholder",
            "image_style": "clean-cartoon-explainer",
            "skip_images": True,
        },
    )
    assert resp.status_code == 403
    assert "disabled" in resp.json().get("detail", "").lower() or "禁用" in resp.json().get("detail", "")


def test_openai_provider_blocked_in_providers_api(client):
    """Provider API 标记 openai 为 blocked_in_ui"""
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    data = resp.json()
    openai_entry = next((p for p in data if p["name"] == "openai"), None)
    assert openai_entry is not None
    assert openai_entry["blocked_in_ui"] is True


# ── External Image Adapter Blocked in UI ──────────────────

def test_openai_image_adapter_rejected_by_api(client, tmp_path):
    """Test 15: openai-image adapter 仍然被 UI API 拒绝"""
    # Create a fake input file
    fake_input = tmp_path / "test.txt"
    fake_input.write_text("test content")
    
    resp = client.post(
        "/api/analyze",
        json={
            "input": str(fake_input),
            "provider": "rule-based",
            "image_adapter": "openai-image",
            "image_style": "clean-cartoon-explainer",
            "skip_images": False,
        },
    )
    assert resp.status_code == 403
    detail = resp.json().get("detail", "").lower()
    assert "disabled" in detail or "禁用" in detail


def test_openai_image_adapter_blocked_in_api(client):
    """Image Adapter API 标记 openai-image 为 blocked_in_ui"""
    resp = client.get("/api/image-adapters")
    assert resp.status_code == 200
    data = resp.json()
    openai_image_entry = next((a for a in data if a["name"] == "openai-image"), None)
    assert openai_image_entry is not None
    assert openai_image_entry["blocked_in_ui"] is True


# ── API Responses Include display_name ──────────────────────

def test_provider_api_returns_display_name(client):
    """Provider API 响应包含 display_name 字段"""
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for p in data:
        assert "display_name" in p, f"Provider {p['name']} missing display_name"


def test_image_adapter_api_returns_display_name(client):
    """Image Adapter API 响应包含 display_name 字段"""
    resp = client.get("/api/image-adapters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for a in data:
        assert "display_name" in a, f"Adapter {a['name']} missing display_name"


def test_image_style_api_returns_display_name(client):
    """Image Style API 响应包含 display_name 字段"""
    resp = client.get("/api/image-styles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for s in data:
        assert "display_name" in s, f"Style {s['name']} missing display_name"


# ── Safey Note in Sidebar ────────────────────────────────

def test_safety_note_contains_chinese(client):
    """侧边栏安全提示包含中文"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "默认禁用" in resp.text or "禁用" in resp.text


# ── Run Detail Page Chinese ────────────────────────────────


def test_layout_still_three_column(client):
    """布局仍然是三栏"""
    resp = client.get("/")
    assert resp.status_code == 200
    # Check for the three columns
    assert 'class="app-layout"' in resp.text
    assert 'class="sidebar"' in resp.text
    assert 'class="workspace"' in resp.text
    assert 'class="preview-pane"' in resp.text
