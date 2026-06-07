"""FastAPI application for ExplainLens Local Web UI.

Codex-style three-column dashboard for running analyses,
browsing results, and previewing visual explainer cards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from explainlens.images import list_image_adapters, get_style, list_styles
from explainlens.providers import list_providers, list_provider_capabilities
from explainlens.web.run_manager import (
    create_run,
    get_run,
    list_artifacts,
    list_runs,
    read_artifact,
)

# ── Template Engine ────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(name: str, **kwargs: Any) -> str:
    """Render a Jinja2 template."""
    template = jinja_env.get_template(name)
    return template.render(**kwargs)


# ── Safety Constants ────────────────────────────────────────────

SAFE_PROVIDERS = {"rule-based", "mock-llm", "local-fixture", "local-http"}
BLOCKED_PROVIDERS = {"openai"}
SAFE_IMAGE_ADAPTERS = {"placeholder", "fixture"}
BLOCKED_IMAGE_ADAPTERS = {"openai-image"}


# ── App Factory ─────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ExplainLens Web UI",
        description="Local-first Visual Explainer — no external APIs by default",
        version="0.1.0",
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ── Page Routes ─────────────────────────────────────

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard with runs list, new run form, and preview."""
        runs = list_runs()
        providers = _get_provider_list()
        image_adapters = _get_image_adapter_list()
        image_styles = _get_image_style_list()
        return render_template(
            "dashboard.html",
            request=request,
            runs=runs,
            providers=providers,
            image_adapters=image_adapters,
            image_styles=image_styles,
        )

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    async def run_detail(request: Request, run_id: str):
        """View details of a specific run."""
        run = get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        artifacts = list_artifacts(run_id)
        return render_template(
            "run_detail.html",
            request=request,
            run=run,
            run_id=run_id,
            artifacts=artifacts,
        )

    # ── API Routes ──────────────────────────────────────

    @app.post("/api/analyze")
    async def api_analyze(request: Request):
        """Start a new analysis run.

        Rejects external API providers and image adapters.
        """
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        input_path = body.get("input", "").strip()
        provider = body.get("provider", "rule-based").strip()
        image_adapter = body.get("image_adapter", "placeholder").strip()
        image_style = body.get("image_style", "clean-cartoon-explainer").strip()
        skip_images = body.get("skip_images", False)

        # Validate input
        if not input_path:
            raise HTTPException(status_code=400, detail="Input path is required")

        input_file = Path(input_path)
        if not input_file.is_absolute():
            input_file = Path.cwd() / input_file
        if not input_file.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {input_file}")

        # Security: reject external API providers
        if provider in BLOCKED_PROVIDERS:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"External API provider '{provider}' is disabled in this local UI. "
                    f"Use CLI with --allow-external-api to enable it."
                ),
            )

        # Security: reject external image APIs
        if image_adapter in BLOCKED_IMAGE_ADAPTERS:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"External image API '{image_adapter}' is disabled in this local UI. "
                    f"Use CLI with --allow-external-images to enable it."
                ),
            )

        try:
            status = create_run(
                input_path=str(input_file),
                provider=provider,
                image_adapter=image_adapter,
                image_style=image_style,
                skip_images=skip_images,
            )
            return JSONResponse(content=status, status_code=201)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/runs")
    async def api_list_runs():
        """List all runs (JSON)."""
        return JSONResponse(content=list_runs())

    @app.get("/api/runs/{run_id}")
    async def api_get_run(run_id: str):
        """Get run status (JSON)."""
        run = get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return JSONResponse(content=run)

    @app.get("/api/runs/{run_id}/artifact/{filename:path}")
    async def api_get_artifact(run_id: str, filename: str):
        """Serve an artifact file from a run directory."""
        content, mime = read_artifact(run_id, filename)
        if content is None:
            raise HTTPException(status_code=404, detail="Artifact not found")

        # Inline rendering for text-based artifacts
        if mime and "json" in mime:
            # Pretty-print JSON
            try:
                parsed = json.loads(content.decode("utf-8"))
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                return Response(
                    content=pretty,
                    media_type="application/json",
                    headers={"Content-Disposition": f"inline; filename={filename}"},
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        return Response(
            content=content,
            media_type=mime or "application/octet-stream",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )

    @app.get("/api/artifacts/{run_id}")
    async def api_list_artifacts(run_id: str):
        """List all artifact files in a run directory."""
        run = get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return JSONResponse(content=list_artifacts(run_id))

    @app.get("/api/doctor")
    async def api_doctor():
        """System diagnostic information."""
        from explainlens import __version__

        providers = list_providers()
        image_adapters = list_image_adapters()
        styles = list_styles()

        return JSONResponse(content={
            "explainlens_version": __version__,
            "python_version": __import__("sys").version,
            "outputs_dir": str((Path.cwd() / "outputs").resolve()),
            "providers": [
                {
                    "name": p["name"],
                    "status": p.get("status", "unknown"),
                    "uses_external_api": p.get("uses_external_api", False),
                }
                for p in providers
            ],
            "image_adapters": [
                {
                    "name": a["name"],
                    "status": a.get("status", "unknown"),
                    "uses_external_api": a.get("uses_external_api", False),
                }
                for a in image_adapters
            ],
            "image_styles": [
                {"name": s["name"], "display_name": _image_style_display_name(s["name"])}
                for s in styles
            ],
            "safety": {
                "external_api_providers_disabled_in_ui": True,
                "external_image_adapters_disabled_in_ui": True,
                "bind_address": "127.0.0.1",
                "local_first": True,
            },
        })

    @app.get("/api/providers")
    async def api_providers():
        """List available providers."""
        providers = list_providers()
        result = []
        for p in providers:
            result.append({
                "name": p["name"],
                "display_name": _provider_display_name(p["name"]),
                "status": p.get("status", "unknown"),
                "version": p.get("version", ""),
                "uses_external_api": p.get("uses_external_api", False),
                "requires_api_key": p.get("requires_api_key", False),
                "description": p.get("description", ""),
                "blocked_in_ui": p["name"] in BLOCKED_PROVIDERS,
            })
        return JSONResponse(content=result)

    @app.get("/api/image-adapters")
    async def api_image_adapters():
        """List available image adapters."""
        adapters = list_image_adapters()
        result = []
        for a in adapters:
            result.append({
                "name": a["name"],
                "display_name": _image_adapter_display_name(a["name"]),
                "status": a.get("status", "unknown"),
                "version": a.get("version", ""),
                "uses_external_api": a.get("uses_external_api", False),
                "requires_api_key": a.get("requires_api_key", False),
                "description": a.get("description", ""),
                "blocked_in_ui": a["name"] in BLOCKED_IMAGE_ADAPTERS,
            })
        return JSONResponse(content=result)

    @app.get("/api/image-styles")
    async def api_image_styles():
        """List available image styles."""
        styles = list_styles()
        result = []
        for s in styles:
            result.append({
                "name": s["name"],
                "display_name": _image_style_display_name(s["name"]),
                "description": s.get("description", ""),
            })
        return JSONResponse(content=result)

    @app.get("/api/health")
    async def api_health():
        """Health check endpoint."""
        return JSONResponse(content={"status": "ok"})

    return app


# ── Helpers ─────────────────────────────────────────────────────


def _get_provider_list() -> list[dict[str, Any]]:
    """Get provider list for template rendering."""
    providers = list_providers()
    result = []
    for p in providers:
        result.append({
            "name": p["name"],
            "status": p.get("status", "unknown"),
            "uses_external_api": p.get("uses_external_api", False),
            "blocked_in_ui": p["name"] in BLOCKED_PROVIDERS,
            "label": _format_provider_label(p),
            "display_name": _provider_display_name(p["name"]),
        })
    return result


def _get_image_adapter_list() -> list[dict[str, Any]]:
    """Get image adapter list for template rendering."""
    adapters = list_image_adapters()
    result = []
    for a in adapters:
        result.append({
            "name": a["name"],
            "status": a.get("status", "unknown"),
            "uses_external_api": a.get("uses_external_api", False),
            "blocked_in_ui": a["name"] in BLOCKED_IMAGE_ADAPTERS,
            "display_name": _image_adapter_display_name(a["name"]),
        })
    return result


def _get_image_style_list() -> list[dict[str, str]]:
    """Get image style list for template rendering."""
    styles = list_styles()
    result = []
    for s in styles:
        result.append({
            "name": s["name"],
            "display_name": _image_style_display_name(s["name"]),
        })
    return result


# ── Chinese Display Name Helpers ───────────────────────────

def _provider_display_name(name: str) -> str:
    """Return Chinese display name for a provider."""
    mapping = {
        "rule-based": "规则拆解",
        "mock-llm": "本地模拟 LLM",
        "local-fixture": "本地协议测试",
        "local-http": "本地 HTTP 模型",
        "openai": "OpenAI 外部模型",
    }
    return mapping.get(name, name)


def _image_adapter_display_name(name: str) -> str:
    """Return Chinese display name for an image adapter."""
    mapping = {
        "placeholder": "本地 SVG 占位图",
        "fixture": "本地 SVG Fixture",
        "openai-image": "OpenAI 图片",
    }
    return mapping.get(name, name)


def _image_style_display_name(name: str) -> str:
    """Return Chinese display name for an image style."""
    mapping = {
        "clean-cartoon-explainer": "清爽卡通讲解",
        "whiteboard": "白板图解",
        "storybook": "绘本风",
        "technical-diagram": "技术图示",
    }
    return mapping.get(name, name)


def _format_provider_label(p: dict[str, Any]) -> str:
    """Format a provider label for display."""
    name = p["name"]
    display = _provider_display_name(name)
    parts = [f"{display} {name}"]
    if p.get("status") == "experimental":
        parts.append("[实验性]")
    if p.get("uses_external_api", False):
        parts.append("[外部 API]")
    return " ".join(parts)
