"""Run manager for ExplainLens Web UI.

Manages analysis runs: listing, creating, status tracking,
and artifact access without shell execution.
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

from explainlens.cli import cmd_analyze


OUTPUTS_DIR = Path("outputs")


def _slugify(name: str) -> str:
    """Create a safe directory slug from an input name."""
    import re
    slug = Path(name).stem.lower()
    slug = re.sub(r"[^a-z0-9_-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:40]


def generate_run_id(input_path: str) -> str:
    """Generate a unique run ID: YYYYMMDD-HHMMSS-slug."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(input_path)
    return f"{ts}-{slug}"


def list_runs() -> list[dict[str, Any]]:
    """List all runs in the outputs/ directory.

    Returns a list of run summaries sorted by creation time (newest first).
    """
    runs: list[dict[str, Any]] = []
    if not OUTPUTS_DIR.exists():
        return runs

    for run_dir in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        status_path = run_dir / "status.json"
        if status_path.exists():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
                runs.append(status)
            except (json.JSONDecodeError, OSError):
                # Skip corrupt status files
                continue
        else:
            # Legacy run without status.json — try run_summary.json
            summary_path = run_dir / "run_summary.json"
            if summary_path.exists():
                try:
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                    runs.append({
                        "run_id": run_dir.name,
                        "status": "success",
                        "input": summary.get("input_file", "unknown"),
                        "provider": summary.get("provider", "unknown"),
                        "image_adapter": summary.get("image_adapter", "none"),
                        "output_dir": str(run_dir.resolve()),
                        "cards_html": "cards.html",
                        "created_at": None,
                        "completed_at": None,
                    })
                except (json.JSONDecodeError, OSError):
                    continue

    return runs


def get_run(run_id: str) -> dict[str, Any] | None:
    """Get run status and metadata."""
    run_dir = OUTPUTS_DIR / run_id
    if not run_dir.exists():
        return None
    status_path = run_dir / "status.json"
    if status_path.exists():
        try:
            return json.loads(status_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return None


def read_artifact(run_id: str, filename: str) -> tuple[bytes | None, str | None]:
    """Read an artifact file from a run directory.

    Returns (content_bytes, mime_type) or (None, None) if not found.
    """
    run_dir = OUTPUTS_DIR / run_id
    file_path = run_dir / filename

    # Security: prevent path traversal
    resolved = file_path.resolve()
    if not str(resolved).startswith(str(run_dir.resolve())):
        return None, None

    if not resolved.is_file():
        return None, None

    content = resolved.read_bytes()

    # Determine MIME type
    suffix = resolved.suffix.lower()
    mime_map = {
        ".html": "text/html; charset=utf-8",
        ".json": "application/json",
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    mime = mime_map.get(suffix, "application/octet-stream")
    return content, mime


def list_artifacts(run_id: str) -> list[dict[str, Any]]:
    """List all artifact files in a run directory, including images/ subdirectory."""
    run_dir = OUTPUTS_DIR / run_id
    if not run_dir.exists():
        return []

    artifacts: list[dict[str, Any]] = []
    # Top-level files
    for f in sorted(run_dir.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            artifacts.append({
                "name": f.name,
                "size": size,
                "size_human": _format_size(size),
            })

    # Recurse into images/ subdirectory
    images_dir = run_dir / "images"
    if images_dir.is_dir():
        for f in sorted(images_dir.iterdir()):
            if f.is_file():
                size = f.stat().st_size
                artifacts.append({
                    "name": f"images/{f.name}",
                    "size": size,
                    "size_human": _format_size(size),
                })

    return artifacts


def _format_size(size: int) -> str:
    """Format file size in human-readable form."""
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def create_run(
    input_path: str,
    provider: str = "rule-based",
    image_adapter: str = "placeholder",
    image_style: str = "clean-cartoon-explainer",
    skip_images: bool = False,
) -> dict[str, Any]:
    """Create a new analysis run and start it in a background thread.

    Returns the run_id and initial status immediately.
    The analysis runs asynchronously.
    """
    # Validate input path
    input_file = Path(input_path)
    if not input_file.is_absolute():
        input_file = Path.cwd() / input_file
    if not input_file.exists():
        raise ValueError(f"Input file not found: {input_file}")

    run_id = generate_run_id(str(input_file))
    output_dir = OUTPUTS_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    status = {
        "run_id": run_id,
        "status": "running",
        "input": str(input_file),
        "provider": provider,
        "image_adapter": image_adapter,
        "image_style": image_style if not skip_images else None,
        "skip_images": skip_images,
        "output_dir": str(output_dir.resolve()),
        "cards_html": "cards.html",
        "created_at": datetime.datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
    }
    write_status(output_dir, status)

    # Start analysis in background thread
    config = {
        "input": str(input_file),
        "provider": provider,
        "image_adapter": image_adapter,
        "image_style": image_style,
        "skip_images": skip_images,
    }
    thread = threading.Thread(
        target=_run_analysis_thread,
        args=(run_id, output_dir, config),
        daemon=True,
    )
    thread.start()

    return status


def write_status(output_dir: Path, status: dict[str, Any]) -> None:
    """Write run status.json."""
    status_path = output_dir / "status.json"
    status_path.write_text(
        json.dumps(status, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _run_analysis_thread(
    run_id: str,
    output_dir: Path,
    config: dict[str, Any],
) -> None:
    """Run the analysis pipeline in a background thread.

    Captures stdout/stderr to logs.txt and updates status.json.
    """
    status = {
        "run_id": run_id,
        "status": "running",
        "input": config["input"],
        "provider": config["provider"],
        "image_adapter": config["image_adapter"],
        "image_style": config["image_style"] if not config.get("skip_images") else None,
        "skip_images": config.get("skip_images", False),
        "output_dir": str(output_dir.resolve()),
        "cards_html": "cards.html",
        "created_at": datetime.datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
    }

    # Capture stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    log_buffer = io.StringIO()

    try:
        sys.stdout = log_buffer
        sys.stderr = log_buffer

        # Build argparse.Namespace matching CLI analyze command
        args = argparse.Namespace()
        args.input = config["input"]
        args.output = str(output_dir)
        args.provider = config["provider"]
        args.image_adapter = config.get("image_adapter", "placeholder")
        args.image_style = config.get("image_style", "clean-cartoon-explainer")
        args.skip_images = config.get("skip_images", False)
        args.allow_external_api = False
        args.allow_external_images = False
        args.allow_local_http = False
        args.local_http_endpoint = None
        args.local_http_model = "local-model"
        args.local_http_protocol = "fixture"
        args.local_http_timeout = 30.0
        args.openai_model = "gpt-5.5"
        args.openai_timeout = 60.0
        args.dump_provider_prompt = False

        exit_code = cmd_analyze(args)

        if exit_code == 0:
            status["status"] = "success"
        else:
            status["status"] = "failed"
            status["error"] = f"Analysis exited with code {exit_code}"

    except Exception as e:
        status["status"] = "failed"
        status["error"] = str(e)

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # Write logs
        log_path = output_dir / "logs.txt"
        log_path.write_text(log_buffer.getvalue(), encoding="utf-8")

        status["completed_at"] = datetime.datetime.now().isoformat()
        write_status(output_dir, status)


def summarize_run(run_dir: Path) -> dict[str, Any] | None:
    """Read run_summary.json from a run directory."""
    summary_path = run_dir / "run_summary.json"
    if not summary_path.exists():
        return None
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
