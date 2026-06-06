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

## Phase 3.3: OpenAI Opt-in Provider

**Status: Remaining**

- [ ] OpenAI opt-in provider

### Remaining for Phase 3.x

- [ ] `custom` provider — user-defined API endpoint
- [ ] Provider configuration via environment variables (`EXPLAINLENS_PROVIDER`)
- [ ] Structured output mode for OpenAI provider

## Phase 4: Real Image Generation Adapter

**Planned**

- [ ] Abstract image generation interface
- [ ] DALL-E adapter
- [ ] Stable Diffusion adapter (local or API)
- [ ] Replace SVG placeholders with real generated images
- [ ] Image caching to avoid re-generation

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
