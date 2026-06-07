# ExplainLens Local Web UI

A Codex-style three-column local dashboard for running ExplainLens analyses,
browsing results, and previewing visual explainer cards — all without CLI commands.

## Quick Start

```bash
python -m explainlens.web --host 127.0.0.1 --port 8765
```

Then open **http://127.0.0.1:8765** in your browser.

## What the UI Can Do

- **New Analysis Run**: Select input file, provider, image adapter, and image style, then start an analysis with one click
- **Run Dashboard**: View all past runs with status, provider, and timing information
- **Cards Preview**: View generated `cards.html` in an iframe directly in the right pane
- **Artifact Browser**: Browse all output files (JSON, Markdown, HTML, images)
- **Manifest Viewer**: Inspect `provider_manifest.json`, `image_manifest.json`, `run_summary.json`
- **Source Index**: View the source-to-card cross-reference index
- **System Info**: Doctor, providers, image adapters, and image styles via API endpoints
- **Three-Column Layout**: Sidebar (runs + system links), workspace (forms + logs), preview pane (cards + artifacts)

## API Endpoints

| Route | Description |
|-------|-------------|
| `GET /` | Dashboard with runs list and new run form |
| `GET /runs/{run_id}` | Run detail page with artifact browser |
| `POST /api/analyze` | Start a new analysis run |
| `GET /api/runs` | List all runs (JSON) |
| `GET /api/runs/{run_id}` | Get run status (JSON) |
| `GET /api/runs/{run_id}/artifact/{filename}` | Download/view artifact |
| `GET /api/artifacts/{run_id}` | List artifacts in a run |
| `GET /api/doctor` | System diagnostic information |
| `GET /api/providers` | List available providers |
| `GET /api/image-adapters` | List available image adapters |
| `GET /api/image-styles` | List available image styles |
| `GET /api/health` | Health check |

## Current Limitations

- **No external APIs**: `openai` provider and `openai-image` adapter are **disabled** in the UI
- **Local-first only**: Only `rule-based`, `mock-llm`, `local-fixture`, and `local-http` providers are available
- **Local image adapters only**: Only `placeholder` and `fixture` image adapters are available
- **No authentication**: The UI binds to `127.0.0.1` only — not exposed to LAN
- **Single-run at a time**: The first version runs analyses serially in background threads
- **No Electron/Tauri**: This is a pure web UI running in your browser — no desktop packaging

## Why External APIs Are Disabled

The Web UI is designed for **safe, local-first exploration**. External API calls:

1. Could incur costs (OpenAI API billing)
2. Could leak prompts or source excerpts
3. Require API key management that the UI does not handle

**To use external API providers, use the CLI**:

```bash
# OpenAI provider (requires OPENAI_API_KEY)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/my_run \
  --provider openai \
  --allow-external-api

# OpenAI image adapter (requires OPENAI_API_KEY)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/my_run \
  --image-adapter openai-image \
  --allow-external-images
```

## Safety Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| No API key in source code | Code audit — zero `sk-` secrets |
| No API key in HTML templates | Templates contain no key patterns |
| External API providers disabled | `openai` returns 403 from `/api/analyze` |
| External image APIs disabled | `openai-image` returns 403 from `/api/analyze` |
| Binds to localhost only | Default `--host 127.0.0.1` |
| No shell execution | Calls Python pipeline directly — no `subprocess` |
| Path traversal blocked | Artifact serving verifies paths are within run directory |

## Architecture

```text
src/explainlens/web/
  __init__.py        — Package init, exports create_app
  __main__.py        — Entry point: python -m explainlens.web
  app.py             — FastAPI application with all routes
  run_manager.py     — Run lifecycle management (create, list, artifacts)
  templates/
    layout.html      — Base three-column layout
    dashboard.html   — Main dashboard with New Run form
    run_detail.html  — Run detail with full artifact browser
  static/
    app.css          — Dark theme, Codex-style three-column layout
    app.js           — Client-side JavaScript utilities
```

## Screenshots

*Coming soon — run `python -m explainlens.web` and open http://127.0.0.1:8765 to see it live.*
