# ExplainLens Demo Guide

This guide shows you how to run the two included demo examples and interpret the output.

---

## What the Demo Shows

ExplainLens reads a text document, extracts key concepts using heuristic rules,
generates an 8-step teaching plan, produces a cartoon-style storyboard,
and renders all of this as a set of visual explainer cards in HTML, Markdown, and JSON.

The demo runs **entirely locally** — no external API calls, no internet required.

---

## Demo 1 — General Article

**Input**: `examples/sample_article.txt`
A fictional article about systems thinking and complex problem solving.

**Run**:

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/demo_article
```

**Open the result**:

```
outputs/demo_article/cards.html
```

Open `cards.html` directly in any browser (no server needed).

---

## Demo 2 — AI Research Note

**Input**: `examples/sample_ai_research_note.txt`
A structured overview of Retrieval-Augmented Generation (RAG) — a fictional research note
covering the problem, old approach, RAG mechanism, evidence, limitations, and why it matters.

This example is designed to showcase ExplainLens on a technical AI topic.

**Run**:

```bash
python -m explainlens.cli analyze \
  --input examples/sample_ai_research_note.txt \
  --output outputs/demo_ai
```

**Open the result**:

```
outputs/demo_ai/cards.html
```

---

## Output Files

Each demo run produces the following files in the output directory:

| File | Description |
|------|-------------|
| `source_chunks.json` | Text split into chunks with character offsets |
| `concept_map.json` | Extracted core problem, concepts, methods, evidence, limitations |
| `teaching_plan.json` | 8-step teaching plan with goals and visual metaphors |
| `storyboard.json` | 8 storyboard panels with scene descriptions |
| `image_prompts.json` | English image prompts for each panel (for future image generation) |
| `cards.json` | Final card data as structured JSON |
| `cards.md` | Markdown version of all 8 cards |
| `cards.html` | Standalone HTML page — open in browser |
| `run_summary.json` | Run metadata: chunk count, card count, timestamp |

---

## How to Open cards.html

Double-click `cards.html` in your file manager,
or open it from the command line:

```bash
# macOS
open outputs/demo_article/cards.html

# Linux
xdg-open outputs/demo_article/cards.html

# Windows
start outputs/demo_article/cards.html
```

The page shows:
- A hero section with the ExplainLens branding
- A run summary (input file, card count, chunk count, timestamp)
- 8 explainer cards, each with:
  - A title
  - An SVG placeholder illustration
  - A plain-language explanation
  - A takeaway callout
  - A collapsible image prompt (for future use with image generation APIs)
  - A collapsible source excerpt (tracing back to the original text)

---

## Current Demo Limitations

| Limitation | Detail |
|------------|--------|
| No PDF support | Only `.txt` and `.md` files are supported |
| No LLM calls | Concepts are extracted using keyword heuristics, not a language model |
| No real images | Image areas show SVG geometric placeholders |
| SVG is illustrative | The SVG diagrams represent conceptual metaphors, not AI-generated art |
| Fixed 8-card structure | Always produces exactly 8 cards per run |

---

## How to Extend the Demo Later

**Add PDF support (Phase 2)**:
Install PyMuPDF and add a `parse_pdf()` function to `src/explainlens/parser.py`.

**Plug in an LLM (Phase 3)**:
Replace `analyzer.py` and `planner.py` with API calls to OpenAI, Anthropic, or a local
model via Ollama. The schemas in `schemas.py` are already designed to be LLM-output compatible.

**Generate real images (Phase 4)**:
Add an `image_generator.py` adapter that sends each `image_prompt` to
Stable Diffusion, DALL-E, or Midjourney. Replace the SVG placeholder in each card with
the generated image URL or base64 data.

**Launch a Web UI (Phase 5)**:
Wrap the CLI pipeline in a FastAPI endpoint and build a React or plain-HTML frontend
that displays the cards interactively.

---

## See Also

- [QUICKSTART.md](QUICKSTART.md) — full installation and first-run guide
- [FAQ.md](FAQ.md) — common questions
- [ROADMAP.md](ROADMAP.md) — planned phases
