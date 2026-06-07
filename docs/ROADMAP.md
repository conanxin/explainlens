# ExplainLens Roadmap

## Phase 1: Local Text-to-Explainer Cards ✅

**Status: Complete (MVP)**

- [x] Text/Markdown parsing
- [x] Paragraph-based chunking with character offsets
- [x] Heuristic keyword-based content analysis
- [x] 8-step fixed teaching plan generation
- [x] Visual metaphor matching
- [x] Image prompt generation (English)
- [x] SVG placeholder images
- [x] HTML card preview (browser-openable)
- [x] JSON / Markdown / HTML export
- [x] CLI interface
- [x] pytest test suite

## Phase 2: PDF Parsing

**Status: Complete**

- [x] Add PyMuPDF dependency
- [x] Extract text with page numbers (searchable PDFs only)
- [x] Page-aware chunking
- [x] Source page references in HTML/Markdown exports
- [x] Sample PDF generation script
- [x] CLI auto-detects input type
- [x] No OCR — scanned PDFs produce clear error

## Phase 2.1: Source Citations & Quality

**Status: Complete**

- [x] `source_index.json` output with chunk/page/card cross-references
- [x] Clickable source citations in HTML (link to Source Appendix)
- [x] Source Appendix in HTML and Markdown exports
- [x] Source quality metadata in `run_summary.json`
- [x] Improved PDF chunk cleanup (whitespace normalization, short chunk merging)
- [x] Bibliography/references section detection
- [x] Source label formatter (`format_source_label`)
- [x] Card-source link builder (`build_card_source_links`)
- [x] Renderer uses explicit data structures (no Pydantic attribute hacks)

## Phase 3.1: Provider Contract Hardening + Disabled OpenAI Draft

**Status: Complete**

- [x] `contract.py` — `ProviderCapabilities` model + `validate_provider_output()`
- [x] `openai_draft.py` — disabled OpenAI provider (raises `RuntimeError`)
- [x] Provider registry upgraded (`DISABLED_PROVIDERS`, `get_provider_capabilities()`, `is_provider_available()`)
- [x] `providers` CLI subcommand (lists available + disabled providers)
- [x] `provider_manifest.json` output (safety + capabilities disclosure)
- [x] CLI `--provider openai` fails closed (no partial output)
- [x] Provider contract validation in `validate_provider_output()`
- [x] 4 new test files: `test_provider_contract.py`, `test_provider_manifest.py`, `test_disabled_openai_provider.py`, `test_provider_listing_cli.py`
- [x] Release audit updated (Phase 3.1 checks)
- [x] CI updated (provider listing + manifest checks)

## Phase 3.2A: Local Fixture Provider ✅

**Status: Complete**

- [x] local-fixture provider (experimental, offline)
- [x] Provider prompt contract (structured prompt packs)
- [x] Provider response contract (structured response validation)
- [x] Offline fixture transport (simulated model response layer)
- [x] Optional provider prompt dump (--dump-provider-prompt)

## Phase 3.2B: Local HTTP Provider Draft ✅

**Status: Complete**

- [x] `local-http` provider (experimental, loopback-only)
- [x] Local HTTP transport with loopback endpoint validation
- [x] Support for `fixture`, `ollama-chat`, `openai-compatible-chat` protocols
- [x] Fail-closed network policy (requires `--allow-local-http`)
- [x] `is_local_endpoint()` — strict loopback-only validation
- [x] `build_local_http_payload()` — protocol-specific payload builders
- [x] `call_local_http_provider()` — HTTP client with safety checks
- [x] `extract_structured_response_from_chat_json()` — response parsing
- [x] Network disclosure block in `provider_manifest.json`
- [x] Fake local server tests in `test_local_http_transport.py`
- [x] CLI arguments: `--local-http-endpoint`, `--local-http-model`, `--local-http-protocol`, `--allow-local-http`, `--local-http-timeout`
- [x] 5 new test files: `test_local_http_transport.py`, `test_local_http_provider.py`, `test_local_http_cli.py`

## Phase 3.2C: Local Provider UX Polish ✅

**Status: Complete**

- [x] `doctor` CLI command (offline diagnostics, no network calls)
- [x] `validate-endpoint` CLI command (static loopback validation, no network calls)
- [x] Enhanced `local-http` error messages (fail-closed UX improvement)
- [x] Configuration templates in `examples/configs/`
  - `local-http-ollama.example.json`
  - `local-http-lmstudio.example.json`
  - `local-http-llamacpp.example.json`
- [x] `docs/LOCAL_PROVIDERS.md` — comprehensive local provider guide
- [x] Updated `README.md` — added Local providers section
- [x] Updated `docs/PROVIDERS.md` — link to LOCAL_PROVIDERS.md
- [x] Updated `docs/SECURITY.md` — doctor/validate-endpoint security notes
- [x] Updated `docs/FAQ.md` — 4 new FAQs
- [x] Updated `docs/ROADMAP.md` — Phase 3.2C marked complete
- [x] Updated `CHANGELOG.md` — Added and Changed entries
- [x] New test files: `test_doctor_cli.py`, `test_endpoint_validation_cli.py`, `test_local_provider_docs.py`
- [x] Updated `scripts/release_audit.py` — 10 new Phase 3.2C checks
- [x] Updated `.github/workflows/ci.yml` — doctor + validate-endpoint checks

## Phase 3.3: OpenAI Opt-in Provider ✅

**Status: Complete**

- [x] `openai_transport.py` — direct HTTP transport for OpenAI Responses API
- [x] `openai_draft.py` — `OpenAIProvider` class (no `import openai` SDK dependency)
- [x] `openai` moved from `DISABLED_PROVIDERS` to `AVAILABLE_PROVIDERS`
- [x] `openai` status in contract.py: `"experimental"`
- [x] Fail-closed by default — requires `--allow-external-api` + `OPENAI_API_KEY`
- [x] CLI pre-validation: API key checked BEFORE `output_dir.mkdir()` (fail-closed ordering)
- [x] Provider manifest: `uses_external_api: true`, `requires_api_key: true`
- [x] 4 new test files (81 tests, all mock-based — zero real API calls):
  - `test_openai_transport.py` (31 tests)
  - `test_openai_provider.py` (15 tests)
  - `test_openai_cli.py` (9 tests)
  - `test_openai_security.py` (16 tests)
- [x] Legacy test migration (7 tests updated from "disabled" to "experimental")
- [x] CI updated — fail-closed tests + providers listing check
- [x] Release audit updated — 11 new Phase 3.3 checks
- [x] Documentation updated — PROVIDERS.md, SECURITY.md, FAQ.md, ROADMAP.md

## Phase 3.4: v0.2.0-alpha Release Hardening 🔄

**Status: In Progress**

- [x] pyproject.toml version → `0.2.0a0` (PEP 440)
- [x] Release notes: `docs/releases/v0.2.0-alpha.md`
- [x] `prepare_release.py` — updated for v0.2.0-alpha tag mapping
- [x] `release_audit.py` — 12 new Phase 3.4 checks
- [x] CHANGELOG.md — archived entries under `[v0.2.0-alpha]`
- [x] README.md — updated version, roadmap, architecture, limitations
- [x] Document consistency pass — QUICKSTART.md, DEMO.md, ROADMAP.md, OPEN_SOURCE_RELEASE_CHECKLIST.md
- [x] CI verification — all providers smoke tests pass
- [x] Full local validation (pytest + smoke + audit)

### Remaining for Phase 3.x

- [ ] `custom` provider — user-defined API endpoint
- [ ] Provider configuration via environment variables (`EXPLAINLENS_PROVIDER`)
- [ ] Structured output mode for OpenAI provider

## Phase 4A: Image Adapter Interface (Local)

**Complete**

- [x] Image adapter abstract interface (`src/explainlens/images/base.py`)
- [x] `placeholder` image adapter — generates local SVG placeholder images
- [x] `fixture` image adapter — deterministic SVG for CI/testing
- [x] Image adapter registry (`get_image_adapter`, `list_image_adapters`)
- [x] `image_jobs.json` output
- [x] `image_manifest.json` output (safety declarations)
- [x] `--image-adapter`, `--image-style`, `--skip-images` CLI options
- [x] `image-adapters` CLI command
- [x] Image references in HTML and Markdown exports
- [x] Doctor command includes image adapter status
- [x] Release audit checks for image adapters

**Constraints:**
- No external image APIs called
- No real image generation (DALL-E / Stable Diffusion)
- All image adapters are local-only
- Default adapter: placeholder

## Phase 4B: Visual Polish & Export Quality

**In Progress**

- [x] Image style presets (`clean-cartoon-explainer`, `whiteboard`, `storybook`, `technical-diagram`)
- [x] `image-styles` CLI command
- [x] Enhanced SVG rendering (unified 16:9 canvas, style-aware)
- [x] Enhanced HTML card layout (Hero, Image Manifest, safety boundary)
- [x] Enhanced Markdown card export (visual metaphor, collapsible sections)
- [x] Demo gallery documentation (`docs/GALLERY.md`)
- [x] Updated demo preview SVG (v0.2.x architecture)
- [x] Image manifest style metadata
- [x] Release audit updated for Phase 4B
- [x] CI updated for style smoke tests

**Constraints:**
- No real image generation APIs
- No localhost image services
- Pure visual polish and export quality
- All images remain local SVG renderers

## Phase 4: Real Image Generation Adapter

**Planned**

- [ ] Abstract image generation interface
- [ ] DALL-E adapter
- [ ] Stable Diffusion adapter (local or API)
- [ ] Replace SVG placeholders with real generated images (future)
- [ ] Image caching to avoid re-generation (future)

## Phase 4C: OpenAI Image Adapter (Opt-in)

**Experimental (opt-in) — code complete, fail-closed by default.**

- [x] `openai-image` adapter (fail-closed, opt-in via `--allow-external-images`)
- [x] `openai_image_transport.py` — HTTP transport using `urllib.request`
- [x] Mock transport (`run_mock_openai_image_transport`)
- [x] CLI `--allow-external-images` flag
- [x] Manifest disclosure (`uses_external_api: true`)
- [x] Doctor shows `openai-image: experimental`
- [x] Phase 4C release audit checks
- [x] CI fail-closed checks for openai-image
- [ ] Image caching to avoid re-generation (future)
- [ ] Progress callback for image download (future)

## Phase 5: Web UI

**Planned**

- [ ] FastAPI backend
- [ ] Simple web frontend (no heavy framework)
- [ ] File upload
- [ ] Real-time progress display
- [ ] Interactive card editing

## Phase 6: Advanced Export

**Planned**

- [ ] Long image / infographic export
- [ ] PowerPoint export
- [ ] Video slideshow export
- [ ] PDF report export
