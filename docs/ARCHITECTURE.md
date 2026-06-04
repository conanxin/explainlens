# ExplainLens Architecture

## Overview

ExplainLens is designed as a pipeline of modular, swappable processing stages.

```
Input (.txt/.md) → Parser → Chunker → Analyzer → Planner → Storyboard → Renderer → Output
```

Each stage produces intermediate data that feeds into the next, with all artifacts
serialized to JSON for inspection and reuse.

## Module Responsibilities

### `parser.py`
- Reads `.txt` and `.md` files
- Handles encoding detection
- PDF marked as TODO

### `chunker.py`
- Splits text by paragraph boundaries
- Merges short paragraphs to avoid tiny chunks
- Preserves character offset spans
- Detects Markdown headings for section context

### `analyzer.py`
- Heuristic, keyword-based extraction
- Produces `ConceptMap` with: core_problem, key_concepts, key_claims,
  methods_or_mechanisms, evidence_or_examples, limitations, why_it_matters
- Designed to be replaced by LLM-based analysis in Phase 3

### `prompts.py`
- Image prompt templates (English, cartoon explainer style)
- Visual metaphor catalog (8 metaphors mapped to teaching steps)
- Teaching step definitions

### `planner.py`
- Generates 8-step `TeachingPlan` from `ConceptMap` and chunks
- Each step has: title, goal, explanation, audience level, risk notes
- Assigns relevant source chunks to each step

### `storyboard.py`
- Converts `TeachingPlan` into `Storyboard` with 8 cartoon panels
- Matches metaphors from catalog
- Builds image prompts with style, composition, and safety constraints
- Each panel has: must_include, must_avoid, takeaway, source references

### `renderer.py`
- Creates `ImageCard` objects from storyboard panels
- Generates inline SVG placeholders per metaphor
- Renders complete standalone HTML page with Jinja2

### `exporters.py`
- JSON export with Pydantic serialization
- Markdown export with card formatting
- Plain text export for HTML files

### `schemas.py`
- All Pydantic data models
- `SourceChunk`, `ConceptMap`, `TeachingPlan`, `Storyboard`, `ImageCard`, `RunSummary`

### `cli.py`
- Argparse-based CLI
- Single `analyze` subcommand orchestrating the full pipeline

## Design Principles

1. **Local-first**: No network calls in MVP
2. **Modular**: Each stage is independent; swap analyzers or renderers easily
3. **Observable**: Every intermediate result is saved as JSON
4. **Testable**: Each module tested independently; CLI tested end-to-end
5. **Extensible**: Plugin interfaces planned for LLM and image generation
