# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## v0.1.0-alpha — 2026-06-04

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
- pytest test suite (33 tests)
- Open source documentation: README, LICENSE (MIT), CONTRIBUTING, SECURITY, ROADMAP
- Release audit report

### Not Included (Phase 2+)

- PDF parsing
- LLM integration (OpenAI / local models)
- Real image generation (Stable Diffusion / DALL-E)
- Web UI
- Long-form export (PPT, video)
