"""Tests for Web UI Chinese localization (i18n).

Covers Phase 5A-UI-polish requirements 1-7, 11-12, 16-17.
"""

import pytest
from explainlens.web.app import create_app


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Create test app with fresh templates."""
    return create_app()


@pytest.fixture()
def client(app):
    """Create test client."""
    from starlette.testclient import TestClient
    return TestClient(app)


# ── Dashboard Chinese Text ──────────────────────────────────

def test_dashboard_contains_new_run_title(client):
    """Test 1: dashboard 页面包含「新建图解任务」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "新建图解任务" in resp.text


def test_dashboard_contains_input_file_label(client):
    """Test 2: dashboard 页面包含「输入文件」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "输入文件" in resp.text


def test_dashboard_contains_provider_label(client):
    """Test 3: dashboard 页面包含「内容理解方式」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "内容理解方式" in resp.text


def test_dashboard_contains_image_adapter_label(client):
    """Test 4: dashboard 页面包含「图片生成方式」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "图片生成方式" in resp.text


def test_dashboard_contains_start_button(client):
    """Test 5: dashboard 页面包含「开始生成」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "开始生成" in resp.text


def test_dashboard_contains_tagline(client):
    """Test 6: dashboard 页面包含「本地优先的论文图解工作台」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "本地优先" in resp.text


def test_dashboard_contains_safety_heading(client):
    """Test 7: dashboard 页面包含「安全边界」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "安全边界" in resp.text


# ── Right Panel Empty State ───────────────────────────────

def test_empty_state_contains_cards_label(client):
    """Test 11: 右侧 empty state 包含「图解卡片」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "图解卡片" in resp.text


def test_empty_state_contains_source_appendix(client):
    """Test 12: 右侧 empty state 包含「Source Appendix」"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Source Appendix" in resp.text


# ── Example Buttons ───────────────────────────────────────

def test_example_article_button_exists(client):
    """Test 13a: 示例按钮「使用示例文章」存在"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "使用示例文章" in resp.text


def test_example_pdf_button_exists(client):
    """Test 13b: 示例按钮「使用示例 PDF」存在"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "使用示例 PDF" in resp.text


def test_example_clear_button_exists(client):
    """Test 13c: 示例按钮「清空」存在"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "清空" in resp.text


# ── Templates Do Not Contain API Keys ───────────────────

def test_templates_do_not_contain_api_key(client):
    """Test 16: 模板不包含 API key"""
    resp = client.get("/")
    assert resp.status_code == 200
    # Check for common API key patterns
    assert "sk-" not in resp.text.lower()
    assert "api_key" not in resp.text.lower()
    assert "api-key" not in resp.text.lower()


def test_run_detail_template_no_api_key():
    """Test 16b: run_detail.html 不包含 API key"""
    import pathlib
    template_dir = pathlib.Path("src/explainlens/web/templates")
    for f in template_dir.glob("*.html"):
        content = f.read_text(encoding="utf-8")
        assert "sk-" not in content, f"Found 'sk-' in {f.name}"
        assert "api_key" not in content.lower(), f"Found 'api_key' in {f.name}"


# ── Layout Markers Still Present ────────────────────────

def test_page_contains_sidebar_marker(client):
    """Test 17a: 页面仍包含 sidebar marker"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'class="sidebar"' in resp.text


def test_page_contains_workspace_marker(client):
    """Test 17b: 页面仍包含 workspace marker"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'class="workspace"' in resp.text


def test_page_contains_preview_pane_marker(client):
    """Test 17c: 页面仍包含 preview pane marker"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'class="preview-pane"' in resp.text


# ── Chinese Display Names in API ────────────────────────

def test_providers_api_includes_display_name(client):
    """Provider API 响应包含 display_name（中文）"""
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    # At least one provider should have a Chinese display_name
    has_chinese = any(any('\u4e00' <= c <= '\u9fff' for c in p.get("display_name", "")) for p in data)
    assert has_chinese, "No provider with Chinese display_name found"


def test_image_adapters_api_includes_display_name(client):
    """Image Adapter API 响应包含 display_name（中文）"""
    resp = client.get("/api/image-adapters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    has_chinese = any(any('\u4e00' <= c <= '\u9fff' for c in a.get("display_name", "")) for a in data)
    assert has_chinese, "No image adapter with Chinese display_name found"


def test_image_styles_api_includes_display_name(client):
    """Image Style API 响应包含 display_name（中文）"""
    resp = client.get("/api/image-styles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    has_chinese = any(any('\u4e00' <= c <= '\u9fff' for c in s.get("display_name", "")) for s in data)
    assert has_chinese, "No image style with Chinese display_name found"


# ── Doctor Endpoint Contains Chinese ─────────────────────

def test_doctor_contains_chinese_style_names(client):
    """Doctor API 返回的图片风格包含中文名称"""
    resp = client.get("/api/doctor")
    assert resp.status_code == 200
    data = resp.json()
    styles = data.get("image_styles", [])
    assert len(styles) > 0
    has_chinese = any(
        any('\u4e00' <= c <= '\u9fff' for c in s.get("display_name", ""))
        for s in styles
    )
    assert has_chinese, "No image style with Chinese display_name in doctor response"
