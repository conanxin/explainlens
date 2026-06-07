# ExplainLens — Development Handoff

> **Date**: 2026-06-07
> **Version**: v0.3.0-alpha (development)
> **Status**: Active development, main branch stable
> **Repository**: https://github.com/conanxin/explainlens

---

## 1. Project Overview

ExplainLens is an open-source AI teaching director that turns complex texts (papers, articles, documentation) into visual explainer cards with cartoon storyboards.

**Core principles:**
- Local-first (no external API calls by default)
- MIT License
- Python 3.10+
- Provider-based architecture (pluggable backends)

---

## 2. Current Capabilities (as of 2026-06-07)

### ✅ Completed Features

| Feature | Status | Notes |
|---------|--------|-------|
| PDF parsing (searchable PDF) | ✅ | PyMuPDF, page-aware chunking |
| Source Index & Appendix | ✅ | Clickable citations, cross-references |
| Provider system (5 providers) | ✅ | rule-based, mock-llm, local-fixture, local-http, openai |
| Image adapter system | ✅ | placeholder, fixture, http, openai-image |
| Local Web UI (Codex-style) | ✅ | 3-column dashboard, Chinese UI |
| Web UI preview state management | ✅ | Fixed flicker issue (Phase 5A-UI-polish-hotfix) |
| Image assets in preview | ✅ | Fixed nested path serving (Phase 5A-UI-polish-hotfix-2) |
| Chinese localization | ✅ | Full UI i18n |
| SVG placeholder images | ✅ | No external API dependency |
| Fail-closed for external APIs | ✅ | openai/openai-image require opt-in |
| 778 tests, all passing | ✅ | CI on Python 3.10/3.11/3.12 |
| Release audit (101 checks) | ✅ | All pass |

---

## 3. Repository Information

- **GitHub**: https://github.com/conanxin/explainlens
- **Branch**: `main`
- **Latest commit**: `718180b` — Phase 5A-UI-polish-hotfix-2: Fix image assets not loading in Web UI preview
- **CI**: GitHub Actions (`.github/workflows/ci.yml`)

---

## 4. Latest Release

- **Latest tag**: `v0.2.0-alpha`
- **Next suggested tag**: `v0.3.0-alpha`
- **Release notes**: `docs/releases/v0.3.0-alpha.md` (already exists)

---

## 5. Local Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/conanxin/explainlens.git
cd explainlens

# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate
# Activate (Windows)
.venv\Scripts\activate

# Install in dev mode
pip install -e ".[dev]"
```

---

## 6. Web UI Startup

```bash
python -m explainlens.web --host 127.0.0.1 --port 8765
```

Then open: http://127.0.0.1:8765

### Web UI Features

- **Left sidebar**: Run history (click to preview)
- **Center workspace**: New run form (input path, provider, image adapter, style)
- **Right preview**: Cards HTML preview (stable, no flicker)
- **Example shortcuts**: One-click fill for sample article / sample PDF
- **Safety**: openai/openai-image blocked by default (403)

---

## 7. Common CLI Commands

### Run analysis (CLI)

```bash
# Create sample PDF
python scripts/create_sample_pdf.py

# Analyze sample article (rule-based, no API)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/sample_run

# Analyze sample PDF
python -m explainlens.cli analyze \
  --input examples/sample_paper.pdf \
  --output outputs/pdf_demo

# Use mock-llm provider
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/mock_run \
  --provider mock-llm

# List providers
python -m explainlens.cli providers

# Doctor diagnostics (offline)
python -m explainlens.cli doctor
```

### Run tests

```bash
# Quick test run
python -m pytest -q

# Run specific test file
python -m pytest tests/test_web_app.py -v

# Run all web UI tests
python -m pytest tests/test_web_app.py tests/test_web_run_manager.py tests/test_web_safety.py tests/test_web_i18n.py tests/test_web_ui_polish.py tests/test_web_preview_state.py tests/test_web_artifact_assets.py -q
```

### Release checks

```bash
# Full release audit (101 checks)
python scripts/release_audit.py

# Prepare release (version, file checks)
python scripts/prepare_release.py
```

---

## 8. Current Providers

| Provider | Status | External API | API Key |
|----------|---------|--------------|---------|
| `rule-based` | Available | No | No |
| `mock-llm` | Available | No | No |
| `local-fixture` | Experimental | No | No |
| `local-http` | Experimental | Local only | No |
| `openai` | Experimental | Yes | Yes (opt-in) |

**OpenAI opt-in requires:**
- `--allow-external-api` flag
- `OPENAI_API_KEY` environment variable

---

## 9. Current Image Adapters

| Adapter | Status | External API | Notes |
|---------|---------|--------------|-------|
| `placeholder` | Available | No | SVG placeholders |
| `fixture` | Experimental | No | Test fixtures |
| `http` | Experimental | Local only | Ollama, etc. |
| `openai-image` | Experimental | Yes | DALL-E (opt-in) |

**OpenAI Image opt-in requires:**
- `--allow-external-api` flag
- `OPENAI_API_KEY` environment variable

---

## 10. Security Boundaries

- ✅ No external API calls by default
- ✅ `openai` provider fails closed (requires `--allow-external-api`)
- ✅ `openai-image` adapter fails closed (requires `--allow-external-api`)
- ✅ Web UI blocks `openai`/`openai-image` selection (403 response)
- ✅ No API keys in source code (verified by `release_audit.py`)
- ✅ Path traversal protection on artifact endpoint
- ✅ `.env` file in `.gitignore`

---

## 11. Known Limitations

1. **PDF**: No OCR support (scanned PDFs not supported)
2. **PDF**: Limited table/formula parsing
3. **Web UI**: No WebSocket live updates (polling-based)
4. **Web UI**: No real-time log streaming
5. **Images**: SVG placeholders only (no real image generation without OpenAI opt-in)
6. **Export**: cards.html is the primary output; no PDF export yet
7. **Providers**: `openai` provider is experimental, not fully tested
8. **Localization**: Chinese UI only (no i18n framework for other languages)

---

## 12. Next Steps (Suggested)

### Phase 5B (not started)
- WebSocket live updates for run status
- Real-time log streaming in Web UI
- Export enhancements (PDF export, Markdown export)

### Phase 6 (future)
- Real image generation integration (optional, opt-in)
- More provider support (Anthropic, local LLMs)
- Improved PDF parsing (tables, formulas)

### Immediate tasks
- [ ] Create GitHub Release for v0.3.0-alpha
- [ ] Update screenshots in `docs/assets/`
- [ ] Add more example outputs
- [ ] Write user documentation (docs/USER_GUIDE.md)

---

## 13. Project Structure

```
explainlens/
├── src/explainlens/
│   ├── cli.py              # CLI entry point
│   ├── web/                # Web UI (FastAPI)
│   │   ├── app.py          # FastAPI application
│   │   ├── run_manager.py  # Run management
│   │   ├── static/         # CSS, JS
│   │   └── templates/      # Jinja2 templates
│   ├── providers/          # Provider system
│   ├── images/             # Image adapter system
│   └── analysis/           # Core analysis logic
├── tests/                  # Test suite (778 tests)
├── docs/                   # Documentation
├── examples/               # Sample inputs
├── scripts/                # Utility scripts
└── outputs/                # Run outputs (gitignored)
```

---

## 14. Testing Strategy

- **Unit tests**: All provider/image adapter logic
- **Integration tests**: CLI commands, Web UI endpoints
- **Safety tests**: API key leakage, openai blocking
- **UI tests**: Chinese localization, preview state management
- **Release tests**: 101 audit checks

### Test coverage

```bash
# Run all tests
python -m pytest -q
# Expected: 778 passed

# Run with coverage
python -m pytest --cov=explainlens --cov-report=html
```

---

## 15. Contributing

1. Create a feature branch from `main`
2. Make changes with tests
3. Run `python scripts/release_audit.py` (must pass)
4. Run `python -m pytest -q` (must pass)
5. Submit PR to `main`

### Commit message format

```
Phase X.X: description
```

Example: `Phase 5A-UI-polish: Chinese localization & UI polish for Web UI`

---

## 16. Contact & Support

- **Issues**: https://github.com/conanxin/explainlens/issues
- **Discussions**: https://github.com/conanxin/explainlens/discussions

---

*Last updated: 2026-06-07*
