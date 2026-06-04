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

**Planned**

- [ ] Add PyMuPDF or pdfplumber dependency
- [ ] Extract text with page numbers
- [ ] Preserve section structure where possible
- [ ] Handle multi-column PDF layouts

## Phase 3: LLM Plugin Interface

**Planned**

- [ ] Abstract LLM interface with pluggable backends
- [ ] OpenAI API adapter
- [ ] Local model adapter (ollama, llama.cpp)
- [ ] Improved concept extraction using LLM
- [ ] Better explanation generation
- [ ] Keep rule-based fallback for offline use

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
