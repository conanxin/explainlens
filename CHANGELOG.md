# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Provider adapter interface (`ExplainProvider` base class).
- `rule-based` provider wrapping existing heuristic pipeline.
- `mock-llm` provider for local testing of the provider interface.
- `--provider` CLI option (choices: `rule-based`, `mock-llm`).
- Provider metadata in `run_summary.json` (`provider`, `provider_version`, `uses_external_api`).
- Provider registry with clear error messages for unknown providers.
- `docs/PROVIDERS.md` — complete provider documentation.
- `.env.example` — environment variable template (no real keys).
- 3 new test files: `test_providers.py`, `test_mock_llm_provider.py`, `test_provider_cli.py`.
- Mock provider smoke tests in CI (text + PDF).
- `local-fixture` provider for offline provider protocol testing.
- Provider prompt contract (`prompt_contract.py`): structured prompt packs with safety rules and output contracts.
- Provider response contract (`response_contract.py`): structured response validation with Pydantic.
- Offline fixture transport (`fixture_transport.py`): simulated local model response layer, fully offline.
- Optional `--dump-provider-prompt` CLI flag for debugging provider prompts.

### Security

- Providers default to local execution — no external AI APIs are called.
- `.env.example` contains only placeholder comments, no real credentials.
- Provider contract requires `uses_external_api` to be set correctly.
- Source traceability preserved across all providers.
- `local-fixture` does not call localhost, subprocesses, or external APIs.
- Provider prompt dumps must not include secrets (verified by CLI safety check).

### Added (Phase 3.1)

- Provider capability metadata (`ProviderCapabilities` in `contract.py`).
- `provider_manifest.json` output for each analysis run.
- `providers` CLI subcommand (list all known providers).
- Disabled OpenAI provider draft (`openai_draft.py`).
- Provider output contract validation (`validate_provider_output()`).
- Provider registry upgraded (`list_provider_capabilities()`, `get_provider_capabilities()`, `is_provider_available()`).
- CLI `--provider` now accepts `openai` (disabled, fails closed).
- `provider_manifest.json` CI checks added.
- Disabled provider fails closed (no partial output).
- 4 new test files: `test_provider_contract.py`, `test_provider_manifest.py`, `test_disabled_openai_provider.py`, `test_provider_listing_cli.py` (68 new tests).

### Security (Phase 3.1)

- Disabled external providers fail closed.
- Provider manifest discloses external API usage.
- Provider contract requires source chunk traceability.
- `.env.example` updated with `EXPLAINLENS_PROVIDER` (documentation only).

### Added

- Searchable PDF input support with PyMuPDF (fitz).
- Page-aware chunking: chunks preserve page boundaries.
- `source_pages.json` output with per-page text and offsets.
- `source_index.json` output with chunk/page/card cross-references.
- Clickable source citations in HTML exports (link to Source Appendix).
- Source Appendix in HTML and Markdown exports.
- Source quality warnings in `run_summary.json` (empty pages, short/long chunks).
- `scripts/create_sample_pdf.py` — generates a 3-page fictional demo PDF.
- Page references in HTML (Source Excerpt & page N) and Markdown exports.
- `input_type`, `page_count`, and `extraction_method` fields in RunSummary.
- `source_quality` field in RunSummary.
- CLI auto-detects input type (.txt, .md, .pdf).
- `format_source_label` and `build_card_source_links` helpers in source_index module.
- Bibliography/references section detection in PDF chunks.
- 33 new tests (source_index, citation_rendering, source_quality).

### Changed

- Improved PDF chunk cleanup: whitespace normalization, short paragraph merging.
- Renderer uses explicit data structures for source info (no Pydantic attribute hacks).
- Markdown export includes Source Appendix with chunk excerpts.

### Limitations

- No OCR — scanned PDFs produce clear error message.
- Tables, figures, and formulas are not deeply parsed.
- Multi-column layouts may produce out-of-order text.
- Source citations link to HTML appendix, not original PDF pages.

---

## v0.1.0-alpha — 2026-06-05 (Release)

### Added

- Initial local MVP release
- Text parsing for `.txt` and `.md` files
- Paragraph-based text chunking with character offset tracking
- Heuristic keyword analysis: core problem, key concepts, claims, methods, evidence, limitations
- 8-step fixed teaching plan generation
- 8-panel cartoon storyboard generation with visual metaphors (maze, magnifying glass, detective board, knowledge tree, etc.)
- English image prompt generation for downstream image models
- SVG placeholder illustrations (no real image generation)
- Jinja2-based HTML card renderer
- Multi-format export: JSON, Markdown, HTML
- CLI entry point: `python -m explainlens.cli analyze`
- pytest test suite (44 tests including release gate tests)
- Open source documentation: README, LICENSE (MIT), CONTRIBUTING, SECURITY, ROADMAP, FAQ, QUICKSTART, DEMO
- GitHub Actions CI (Python 3.10 / 3.11 / 3.12)
- Release audit script: `scripts/release_audit.py` (28 checks)
- Release preparation script: `scripts/prepare_release.py`
- Demo preview SVG: `docs/assets/demo-preview.svg`
- Release notes: `docs/releases/v0.1.0-alpha.md`
- AI research note example: `examples/sample_ai_research_note.txt`
- Improved HTML renderer: Hero section, run summary, collapsible panels

### Not Included (Phase 2+)

- PDF parsing
- LLM integration (OpenAI / local models)
- Real image generation (Stable Diffusion / DALL-E)
- Web UI
- Long-form export (PPT, video)
