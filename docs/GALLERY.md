# Visual Export Gallery

This document shows how ExplainLens visual exports look with different
image adapters and style presets.

**All default images are local SVG placeholders — no external image APIs are called.**
**The `openai-image` adapter is opt-in only (`--allow-external-images` + `OPENAI_API_KEY`).**

---

## How the Gallery is Generated

The gallery images are produced by running the ExplainLens CLI with different
combinations of `--image-adapter` and `--image-style` options:

```bash
# placeholder default (clean-cartoon-explainer)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_clean \
  --image-adapter placeholder \
  --image-style clean-cartoon-explainer

# fixture (deterministic)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_fixture \
  --image-adapter fixture \
  --image-style storybook

# skip images
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_skip \
  --skip-images
```

---

## Image Adapters

### placeholder (default)

The `placeholder` adapter generates clean, education-style SVG illustrations
with visual metaphors (maze, magnifier, tree, robot, etc.). Each card gets a
unique visual while maintaining a consistent look.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_placeholder \
  --image-adapter placeholder
```

Output: `outputs/gallery_placeholder/images/*.svg`, `cards.html`, `cards.md`

### fixture

The `fixture` adapter generates deterministic SVG files — identical output
on every run. Designed for CI and testing.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_fixture \
  --image-adapter fixture
```

Output: `outputs/gallery_fixture/images/*.svg`, `cards.html`, `cards.md`

### skip-images

When `--skip-images` is passed, no SVGs are generated. HTML cards fall back
to inline SVG placeholders (embedded in the HTML). Markdown explicitly
states that image generation was skipped.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_skip \
  --skip-images
```

Output: `outputs/gallery_skip/cards.html`, `outputs/gallery_skip/cards.md`
(no `images/` directory, no `image_manifest.json`)

---

## Image Style Presets

All 4 styles can be used with both the `placeholder` and `fixture` adapters.

### clean-cartoon-explainer (default)

Clean, education-style illustrations with simple geometric shapes and a
blue-indigo palette. Best for scientific and technical concepts.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_clean \
  --image-adapter placeholder \
  --image-style clean-cartoon-explainer
```

### whiteboard

Whiteboard sketch style with a light background and dark marker-style
accents. Gives a hand-drawn, workshop feel.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_whiteboard \
  --image-adapter placeholder \
  --image-style whiteboard
```

### storybook

Warm, inviting storybook illustration style with amber/orange palette and
character scenes. Good for narrative explanations.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_storybook \
  --image-adapter placeholder \
  --image-style storybook
```

### technical-diagram

Precise technical diagram style with green palette, structured layouts,
boxes, and arrows. Best for method descriptions and architecture diagrams.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_tech \
  --image-adapter placeholder \
  --image-style technical-diagram
```

### Listing Available Styles

```bash
python -m explainlens.cli image-styles
```

Output:

```
Available image styles:

  - clean-cartoon-explainer
    Clean cartoon-style illustrations for scientific and technical concepts.

  - whiteboard
    Whiteboard sketch style — hand-drawn feel with marker-style lines.

  - storybook
    Storybook illustration style — warm, inviting, with character scenes.

  - technical-diagram
    Precise technical diagram style — nodes, connectors, and structured layouts.
```

---

## Output Files

After running with `--image-adapter placeholder`, the output directory
contains:

```
outputs/gallery_clean/
├── cards.html              # Standalone HTML with cards, appendix, and image manifest
├── cards.md                # Markdown export with image references
├── cards.json              # JSON card data
├── image_jobs.json         # Job descriptions for each image
├── image_manifest.json     # Manifest with adapter info and safety declarations
├── run_summary.json        # Summary of the analysis run
├── source_index.json       # Cross-reference between chunks and cards
├── provider_manifest.json  # Provider capabilities and safety disclosure
└── images/
    ├── card_01.svg
    ├── card_02.svg
    ├── ...
    └── card_08.svg
```

---

### openai-image (experimental, opt-in)

The `openai-image` adapter calls the OpenAI Images API (DALL-E) to generate
real images. It is **fail-closed by default** — requires explicit opt-in:

```bash
# 1. Set API key (NEVER commit to git)
export OPENAI_API_KEY="sk-..."

# 2. Run with openai-image adapter
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/gallery_openai_image \
  --image-adapter openai-image \
  --allow-external-images
```

**Safety:**
- Default: fail-closed (no `--allow-external-images` = no API call)
- API key is NEVER printed, logged, or written to any file
- Image prompts are NOT written to logs
- Manifest (`image_manifest.json`) discloses `uses_external_api: true`
- CI uses mock transport — zero real API calls

Output: `outputs/gallery_openai_image/images/*.png` (real images), `cards.html`, `cards.md`, `image_manifest.json`

---

## Safety Notes

- **Default: no external image APIs** — All default adapters (`placeholder`, `fixture`) are local SVG renderers.
- **`openai-image` is opt-in only** — requires `--allow-external-images` + `OPENAI_API_KEY`.
- **No document upload** — Source text stays on your machine.
- **No API keys required for default adapters** — `placeholder` and `fixture` are fully offline.
- **Real image generation requires opt-in** — `openai-image` adapter calls OpenAI DALL-E API only when explicitly enabled.
- **Outputs are not committed** — The `outputs/` directory is in `.gitignore`.
- **Manifest transparency** — `image_manifest.json` always discloses `uses_external_api` and `requires_api_key`.

---

## Related Docs

- [README.md](../README.md) — Project overview and quick start
- [docs/PROVIDERS.md](PROVIDERS.md) — Provider system documentation
- [docs/SECURITY.md](SECURITY.md) — Security policy
- [docs/FAQ.md](FAQ.md) — Frequently asked questions
