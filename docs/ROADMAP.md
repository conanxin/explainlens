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

## Phase 3: LLM Adapter Interface with Mock Provider

**Status: Complete**

- [x] Abstract provider base class (`ExplainProvider`)
- [x] `rule-based` provider wrapping existing heuristic pipeline
- [x] `mock-llm` provider simulating future LLM output (no API calls)
- [x] Provider registry with clear error messages
- [x] `--provider` CLI parameter
- [x] Provider metadata in `run_summary.json` (provider, provider_version, uses_external_api)
- [x] Provider documentation (`docs/PROVIDERS.md`)
- [x] All output files preserved across providers
- [x] Source citations preserved across providers
- [x] No external AI SDK dependencies added

### Remaining for Phase 3.x

- [ ] `openai` provider — real OpenAI API adapter
- [ ] `local` provider — Ollama / llama.cpp adapter
- [ ] `custom` provider — user-defined API endpoint
- [ ] Provider configuration via environment variables

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
