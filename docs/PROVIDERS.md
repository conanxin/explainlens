# Providers

ExplainLens supports provider-based analysis. A **provider** is a pluggable
backend that performs the core analysis pipeline: extracting concepts, building
a teaching plan, and generating a visual storyboard.

---

## What is a provider?

The provider interface defines four methods:

```python
class ExplainProvider(ABC):
    def build_concept_map(self, chunks) -> ConceptMap: ...
    def build_teaching_plan(self, chunks, concept_map) -> TeachingPlan: ...
    def build_storyboard(self, chunks, concept_map, teaching_plan) -> Storyboard: ...
    def build_cards(self, storyboard) -> List[ImageCard]: ...
```

Each provider implements these methods differently. The rest of the pipeline
(chunking, rendering, exporting) remains identical regardless of provider.

---

## Current providers

### rule-based

The default provider. Uses heuristic keyword matching and fixed templates:

- Keyword-based concept extraction (problem/claim/method/evidence/limitation)
- Fixed 8-step teaching plan with pre-written templates
- Fixed 8-panel storyboard with visual metaphor catalog

**Characteristics:**
- No external API calls
- Deterministic output (same input → same output)
- Fast, offline, zero-cost
- Suitable for rapid prototyping

### mock-llm

A local mock provider that simulates future LLM output:

- Uses the same chunks as input but produces more conversational, narrative language
- Output sounds like a language model wrote it, but is still template-based
- Teaching metaphors are explicitly marked with `⚠ Teaching metaphor:` prefix
- Every card is linked to real source chunks (no fabrication)

**Characteristics:**
- No external API calls
- No real AI model
- Conversational language style
- Serves as a test harness for the provider interface
- Useful for validating that the full pipeline works with different backends

---

## Provider lifecycle

Providers have three lifecycle states:

| Status | Meaning | Example |
|--------|---------|---------|
| `available` | Fully functional, can be used | `rule-based`, `mock-llm` |
| `disabled` | Code exists but is intentionally disabled | `openai` |
| `experimental` | Partially implemented, may change | (none yet) |

### Why is OpenAI disabled?

The `openai` provider is a **draft adapter** — the code skeleton exists
in `src/explainlens/providers/openai_draft.py`, but it is intentionally
disabled and will NOT run any analysis.

**Why disabled?**
- Phase 3.1 focuses on contract hardening and safety boundaries
- Real external API providers will be enabled in Phase 3.x
- The draft exists as documentation and a contract placeholder

**What happens if I try `--provider openai`?**

```
Provider error: Provider 'openai' is currently disabled. Real external API providers are not enabled in this release.

Available providers:
  - rule-based  (default, local heuristic)
  - mock-llm    (mock LLM, no API calls)

The OpenAI provider will be enabled in a future Phase 3.x release. For more details, see docs/PROVIDERS.md.
```

No output files are created. The command fails closed.

---

## Provider contract

When implementing a new provider, follow this contract:

### Required provider contract

1. **Subclass `ExplainProvider`.** All providers must inherit from
   `explainlens.providers.base.ExplainProvider`.

2. **Implement all four abstract methods.** `build_concept_map`,
   `build_teaching_plan`, `build_storyboard`, and `build_cards`.

3. **Set provider metadata.** `name`, `version`, and `uses_external_api`
   must be set correctly.

4. **Preserve source traceability.** Every card must have non-empty
   `source_chunk_ids` linking back to the original source.

5. **Do not fabricate content.** Never invent facts, data, citations,
   or conclusions that are not in the source material.

6. **Mark teaching metaphors.** When using analogies or simplifications,
   clearly mark them as teaching metaphors rather than source claims.

7. **Set `uses_external_api` correctly.** This flag must be `True` if
   the provider makes any network requests.

8. **Never write secrets to outputs.** API keys, tokens, or credentials
   must never appear in output files.

9. **Register in `AVAILABLE_PROVIDERS` (or `DISABLED_PROVIDERS`).**
   Add the new provider to the appropriate registry in
   `explainlens/providers/registry.py`.

### Provider capabilities

Each provider declares its capabilities via `ProviderCapabilities`:

```python
caps = ProviderCapabilities(
    name="my-provider",
    version="my-provider-v0.1",
    status="available",           # or "disabled", "experimental"
    uses_external_api=False,       # True if it makes network requests
    requires_api_key=False,        # True if an API key must be configured
    supports_pdf=True,
    supports_text=True,
    preserves_source_chunk_ids=True,
    description="...",
)
```

The `provider_manifest.json` output file includes a `safety` section:

```json
{
  "provider": "mock-llm",
  "provider_version": "mock-llm-v0.1",
  "provider_status": "available",
  "uses_external_api": false,
  "requires_api_key": false,
  "capabilities": {
    "supports_pdf": true,
    "supports_text": true,
    "preserves_source_chunk_ids": true
  },
  "safety": {
    "uploads_documents": false,
    "reads_api_key": false,
    "writes_secrets": false
  }
}
```

---

## Provider manifest

Every analysis run produces a `provider_manifest.json` file in the output directory.

**Purpose:**
- Documents which provider was used
- Discloses external API usage
- Lists safety guarantees
- Used by release audit and CI

**Contents:**
- `provider` — provider name
- `provider_version` — provider version string
- `provider_status` — `available` / `disabled` / `experimental`
- `uses_external_api` — whether external API calls were made
- `requires_api_key` — whether an API key is needed
- `capabilities` — supported input types and contract compliance
- `safety` — safety disclosures (document uploads, API key reads, secret writes)

**CI checks:**
```bash
test -f outputs/ci_mock_smoke_test/provider_manifest.json
grep -q '"uses_external_api": false' outputs/ci_mock_smoke_test/provider_manifest.json
grep -q '"requires_api_key": false' outputs/ci_mock_smoke_test/provider_manifest.json
```

---

## Providers not yet implemented

The following providers are planned for future releases:

| Provider | Description | Phase |
|----------|-------------|-------|
| `openai` | OpenAI GPT API (GPT-4, GPT-4o) | Phase 3.x (draft disabled) |
| `local` | Local models via Ollama, llama.cpp | Phase 3.x |
| `custom` | User-defined external API endpoint | Phase 3.x |
| `anthropic` | Anthropic Claude API | Future |
| `deepseek` | DeepSeek API | Future |

---

## Safety boundary

ExplainLens enforces the following safety guarantees for all providers:

1. **No external API calls by default.** The default `rule-based` provider
   and the `mock-llm` provider never make network requests.

2. **No document upload.** Input files are processed locally and never sent
   to external servers.

3. **No API key required.** The current version does not read any API keys
   from environment variables.

4. **Source traceability preserved.** Every card's `source_chunk_ids` links
   back to the original document text.

5. **No fabrication.** Providers must not invent data, claims, or conclusions
   that do not exist in the source material.

6. **Disabled providers fail closed.** Attempting to use a disabled provider
   produces a clear error and NO output files.

7. **Provider manifest discloses external API usage.** The `provider_manifest.json`
   file always documents whether external APIs were called.

---

## How to run mock provider

```bash
# Analyze a text file with mock-llm provider
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/mock_run \
  --provider mock-llm

# Analyze a PDF with mock-llm provider
python -m explainlens.cli analyze \
  --input examples/sample_paper.pdf \
  --output outputs/mock_pdf_run \
  --provider mock-llm
```

Open `outputs/mock_run/cards.html` in your browser to see the results.

---

## How to list all providers

```bash
python -m explainlens.cli providers
```

Output:
```
Available providers:

  - rule-based
    Status:       available
    External API: no
    Requires API key: no

  - mock-llm
    Status:       available
    External API: no
    Requires API key: no

Disabled providers:

  - openai
    Status:       disabled
    External API: yes
    Requires API key: yes
```

---

## How future provider adapters should be implemented

### Example skeleton

```python
from explainlens.providers.base import ExplainProvider
from explainlens.schemas import ConceptMap, SourceChunk, TeachingPlan, Storyboard

class MyProvider(ExplainProvider):
    name = "my-provider"
    version = "my-provider-v0.1"
    uses_external_api = True  # Set to True if it calls an API

    def build_concept_map(self, chunks):
        # Your implementation here
        ...

    def build_teaching_plan(self, chunks, concept_map):
        ...

    def build_storyboard(self, chunks, concept_map, teaching_plan):
        ...

    def build_cards(self, storyboard):
        ...
```

### Register the provider

```python
# In explainlens/providers/registry.py
from explainlens.providers.my_provider import MyProvider

AVAILABLE_PROVIDERS["my-provider"] = MyProvider
```

### For disabled providers (drafts)

```python
# In explainlens/providers/registry.py
from explainlens.providers.openai_draft import OpenAIDraftProvider

DISABLED_PROVIDERS["openai"] = OpenAIDraftProvider
```

The `get_provider()` function will raise `RuntimeError` with a clear message.

---

## See also

- [FAQ](FAQ.md) — Common questions about providers and AI integration
- [SECURITY](SECURITY.md) — Security policy and provider safety
- [ROADMAP](ROADMAP.md) — Planned provider implementations
- [ARCHITECTURE](ARCHITECTURE.md) — System architecture overview
