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

## Current providers (continued)

### local-fixture

**Status:** experimental

A completely offline provider that uses fixture data — no model, no HTTP, no subprocess. This provider is designed for contract testing and offline development.

**Architecture:**
```
prompt_contract.py → fixture_transport.py → response_contract.py
```

**Characteristics:**
- `uses_external_api`: `false`
- `requires_api_key`: `false`
- `version`: `local-fixture-v0.1`
- Completely offline — no model inference
- No HTTP calls (not even to localhost)
- Uses fixture/static data for predictable output
- Suitable for contract verification and offline CI

**Purpose:**
- Harden provider contracts without network dependencies
- Provide a stable reference for contract-based testing
- Enable offline development without local model servers

---

## Provider lifecycle

Providers have three lifecycle states:

| Status | Meaning | Example |
|--------|---------|---------|
| `available` | Fully functional, can be used | `rule-based`, `mock-llm` |
| `disabled` | Code exists but is intentionally disabled | (none currently) |
| `experimental` | Partially implemented, may change | `openai`, `local-fixture`, `local-http` |

### OpenAI Provider (experimental)

**Status:** experimental — requires explicit opt-in.

The `openai` provider calls the OpenAI Responses API. It is implemented in `src/explainlens/providers/openai_draft.py` with the transport layer in `src/explainlens/providers/openai_transport.py`.

**Characteristics:**
- `uses_external_api`: `true`
- `requires_api_key`: `true`
- `version`: `openai-v0.1`
- Calls `api.openai.com` via direct HTTP (no `openai` SDK dependency)
- Requires `--allow-external-api` + `OPENAI_API_KEY` env var

**Fail-closed by default:**

The provider refuses any API call without explicit opt-in:

```bash
# Fails: no --allow-external-api
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_test \
  --provider openai
# Provider error: openai is fail-closed by default.
# To enable it, set OPENAI_API_KEY and pass --allow-external-api.
# No request was sent.

# Fails: --allow-external-api but no API key
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_test \
  --provider openai \
  --allow-external-api
# Provider error: OPENAI_API_KEY is not set.
# No request was sent.
```

**Opt-in usage:**

```bash
# Set API key (never commit to version control)
export OPENAI_API_KEY="sk-..."

# Run with explicit opt-in
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_run \
  --provider openai \
  --allow-external-api \
  --openai-timeout 60
```

**Security guarantees:**
- No hardcoded API keys (uses `OPENAI_API_KEY` env var only)
- No `import openai` (direct HTTP, no SDK dependency)
- Provider manifest discloses `uses_external_api: true`
- All 81 tests use mock fixtures — zero real API calls in CI

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

## Local HTTP Provider

**Status:** experimental

A local HTTP provider that makes loopback-only HTTP calls to local model endpoints (Ollama, LM Studio, llama.cpp server, or OpenAI-compatible endpoints).

**Architecture:**
```
prompt_contract.py → local_http_transport.py → response_contract.py
```

**Characteristics:**
- `uses_external_api`: `false` (loopback only, not "external")
- `requires_api_key`: `false`
- `version`: `local-http-v0.1`
- Supports three protocols: `fixture`, `ollama-chat`, `openai-compatible-chat`
- Requires explicit opt-in (`--allow-local-http`) for any network call
- Default behavior: **fail closed**

**Protocol types:**

| Protocol | Description | Endpoint example |
|-----------|-------------|-----------------|
| `fixture` | Offline, no HTTP call | (none) |
| `ollama-chat` | Ollama `/api/chat` API | `http://localhost:11434/api/chat` |
| `openai-compatible-chat` | OpenAI-compatible `/v1/chat/completions` | `http://localhost:8000/v1/chat/completions` |

**CLI usage:**

```bash
# Offline fixture mode (no HTTP, CI-safe)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_http_fixture \
  --provider local-http \
  --local-http-protocol fixture

# Ollama (requires --allow-local-http)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_local \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --local-http-model llama3.2 \
  --allow-local-http

# OpenAI-compatible (requires --allow-local-http`)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_compat \
  --provider local-http \
  --local-http-protocol openai-compatible-chat \
  --local-http-endpoint http://localhost:8000/v1/chat/completions \
  --local-http-model local-model \
  --allow-local-http
```

**Safety rules:**
1. ONLY loopback endpoints allowed (`localhost`, `127.0.0.1`, `::1`)
2. NO remote HTTP (no HTTPS, no LAN addresses)
3. NO API keys are read or sent
4. NO Authorization headers are set
5. Network calls require explicit opt-in (`allow_network=True`)
6. Default: fail closed (raises `RuntimeError` if `allow_network=False`)

---

## Loopback Safety Policy

The `local-http` provider enforces strict endpoint validation:

### Allowed endpoints

- `http://localhost:...`
- `http://127.0.0.1:...`
- `http://[::1]:...`

### Rejected endpoints

- `https://...` (any HTTPS)
- `http://example.com/...`
- `http://192.168.x.x/...` (private LAN)
- `http://10.x.x.x/...` (private LAN)
- `http://172.16.x.x/...` (private LAN)
- Any empty or malformed URL

### DNS rebinding protection

The `is_local_endpoint()` function also resolves `localhost` to verify it maps to a loopback IP address, protecting against DNS rebinding attacks.

---

## Fail-Closed Network Policy

The `local-http` provider implements a **fail-closed** policy:

1. **Default: fail closed**
   - If `allow_network=False` (default), any HTTP call raises `RuntimeError`
   - No request is sent

2. **Explicit opt-in required**
   - Must pass `--allow-local-http` to CLI
   - Must set `allow_network=True` in code
   - Error message explains how to proceed

3. **Fixture protocol exemption**
   - `protocol="fixture"` does NOT require `--allow-local-http`
   - Fixture mode is completely offline
   - Uses `fixture_transport.py` to simulate responses

4. **Remote endpoint rejection**
   - Even with `--allow-local-http`, remote endpoints are rejected
   - Only loopback addresses are allowed
   - Error message lists allowed endpoints

---

## Provider Prompt Contract

The **Provider Prompt Contract** (`prompt_contract.py`) defines how providers construct prompts for LLM or template-based analysis.

**Purpose:**
- Standardize prompt structure across providers
- Ensure consistent input format for contract testing
- Enable offline fixture-based prompt validation

**Key responsibilities:**
- Define prompt templates for concept extraction
- Define prompt templates for teaching plan generation
- Define prompt templates for storyboard creation
- Validate prompt structure against the contract schema

**For `local-http`:**
- Builds prompt pack from chunks
- Renders system and user prompts
- Embeds output contract and safety rules
- Sends as JSON payload to local endpoint

**Prompt pack structure:**
```python
ProviderPromptPack(
    task="explain_complex_content",
    audience_level="general",
    desired_card_count=8,
    source_type="txt",  # or "pdf"
    source_chunks=[...],
    output_contract={...},  # expected output JSON structure
    safety_rules=[...],  # preserve source_chunk_ids, etc.
)
```

---

## Provider Response Contract

The **Provider Response Contract** (`response_contract.py`) defines the expected structure of provider outputs.

**Purpose:**
- Validate provider outputs against schemas
- Ensure all providers return compatible data structures
- Enable contract-based testing without model inference

**Key responsibilities:**
- Validate `ConceptMap` structure
- Validate `TeachingPlan` structure
- Validate `Storyboard` structure
- Validate `ImageCard` list structure
- Ensure `source_chunk_ids` traceability

**For `local-http`:**
- Returns fixture data that satisfies all contract validations
- No model inference — purely structural compliance
- Enables offline contract verification
- Includes `network` block in `provider_manifest.json`

**Provider manifest with network block:**
```json
{
  "provider": "local-http",
  "provider_version": "local-http-v0.1",
  "provider_status": "experimental",
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
  },
  "network": {
    "uses_local_http": false,
    "allows_remote_http": false,
    "endpoint": null,
    "protocol": "fixture",
    "timeout_seconds": 30
  }
}
```

The `network` block is added automatically when the provider is `local-http`.

---

## Offline Fixture Transport

The **Offline Fixture Transport** (`fixture_transport.py`) is a transport layer that returns static fixture data instead of making HTTP calls.

**Purpose:**
- Simulate provider responses without network calls
- Provide deterministic outputs for testing
- Enable contract hardening without external dependencies

**Key characteristics:**
- No HTTP requests (not even to localhost)
- Returns pre-defined fixture data
- Fully offline and deterministic
- Compatible with provider contract validation

**Usage:**
```python
# In local-fixture provider
from explainlens.providers.local_fixture.fixture_transport import FixtureTransport

transport = FixtureTransport()
concept_map = transport.get_fixture_concept_map(chunks)
teaching_plan = transport.get_fixture_teaching_plan(chunks, concept_map)
storyboard = transport.get_fixture_storyboard(chunks, concept_map, teaching_plan)
cards = transport.get_fixture_cards(storyboard)
```

---

## Why local-fixture does not call local HTTP (and how local-http does)

The `local-fixture` provider intentionally avoids even localhost HTTP calls (e.g., to Ollama or LM Studio) for several reasons:

### For local-fixture:
1. **Contract-first development**
   The primary goal is to harden the provider contracts (`prompt_contract.py`, `response_contract.py`) before introducing real model inference. Fixture data allows us to verify that:
   - All contract validations pass
   - Output structures are correct
   - Source traceability is preserved
   - Safety boundaries are enforced

2. **Offline CI compatibility**
   By avoiding all network calls (including localhost), `local-fixture` can run in:
   - Air-gapped environments
   - CI pipelines without local model servers
   - Development environments without Ollama/LM Studio installed

3. **Deterministic testing**
   Fixture data provides deterministic outputs, making it possible to:
   - Write precise contract validation tests
   - Verify error handling paths
   - Test edge cases with crafted fixtures

4. **Separation of concerns**
   The transport layer (`fixture_transport.py`) is designed to be swapped. Once contracts are hardened, the same provider can use:
   - `fixture_transport.py` for offline testing
   - `local_http_transport.py` for real HTTP calls to local models

### For local-http:
The `local-http` provider **does** support localhost HTTP calls, but:
- **Default: fail closed** — requires explicit `--allow-local-http` opt-in
- **Loopback only** — only `localhost`, `127.0.0.1`, `::1` are allowed
- **No remote HTTP** — no HTTPS, no LAN addresses
- **Fixture mode available** — `protocol="fixture"` for offline CI

```bash
# Default: fail closed (no HTTP)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_http_test \
  --provider local-http
# ERROR: requires --allow-local-http or use --local-http-protocol fixture

# Fixture mode: offline, no HTTP
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_http_fixture \
  --provider local-http \
  --local-http-protocol fixture

# Real HTTP: requires explicit opt-in
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_local \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --local-http-model llama3.2 \
  --allow-local-http
```

---

## Future path to Ollama / LM Studio

The `local-fixture` provider is designed as a stepping stone toward real local model support.

### Planned transport implementations

| Transport | Description | Status |
|-----------|-------------|--------|
| `fixture_transport.py` | Static fixture data | ✅ Implemented |
| `local_http_transport.py` | Loopback-only HTTP client | ✅ Implemented (fail-closed) |
| `ollama_transport.py` | Ollama local API | 🔄 Planned |
| `lm_studio_transport.py` | LM Studio local API | 🔄 Planned |

### Migration path

1. **Phase 1 (Current):** `local-fixture` with `fixture_transport.py`
   - Contract hardening
   - Offline CI
   - Structural validation

2. **Phase 2:** Add `ollama_transport.py`
   - Real model inference via Ollama
   - HTTP calls to `http://localhost:11434`
   - Same provider contract, different transport

3. **Phase 3:** Add `lm_studio_transport.py`
   - Real model inference via LM Studio
   - HTTP calls to `http://localhost:1234`
   - Same provider contract, different transport

### Provider status progression

```
experimental (local-fixture with fixtures)
    ↓
available (local-fixture with Ollama)
    ↓
available (local-fixture with LM Studio)
```

The provider name `local-fixture` may be renamed to `local` once real model support is added.

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
| `local` | Local models via Ollama, llama.cpp | Phase 3.x (partially implemented as `local-fixture`) |
| `custom` | User-defined external API endpoint | Phase 3.x |
| `anthropic` | Anthropic Claude API | Future |
| `deepseek` | DeepSeek API | Future |

### Note: local-fixture (experimental)

The `local-fixture` provider is a precursor to the full `local` provider. It implements the same provider interface but uses fixture data instead of real model inference. See [Future path to Ollama / LM Studio](#future-path-to-ollama--lm-studio) for the migration plan.

---

## Safety boundary

ExplainLens enforces the following safety guarantees for all providers:

1. **No external API calls by default.** The default `rule-based` provider,
   the `mock-llm` provider, and the `local-fixture` provider never make network requests.

2. **No document upload.** Input files are processed locally and never sent
   to external servers.

3. **No API key required (default).** The default `rule-based` provider, the
   `mock-llm` provider, and the `local-fixture` provider never read API keys.
   The `openai` and `local-http` providers may read API keys only when
   explicitly opted in via `--allow-external-api` or `--allow-local-http`.

4. **Fail-closed for external API providers.** The `openai` provider refuses
   any API call without `--allow-external-api` + `OPENAI_API_KEY`. No output
   files are created on failure.

4. **Source traceability preserved.** Every card's `source_chunk_ids` links
   back to the original document text.

5. **No fabrication.** Providers must not invent data, claims, or conclusions
   that do not exist in the source material.

6. **Disabled providers fail closed.** Attempting to use a disabled provider
   produces a clear error and NO output files.

7. **Provider manifest discloses external API usage.** The `provider_manifest.json`
   file always documents whether external APIs were called.

8. **Experimental providers are opt-in.** The `local-fixture` provider must
   be explicitly selected with `--provider local-fixture`.

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

  - local-fixture
    Status:       experimental
    External API: no
    Requires API key: no

  - openai
    Status:       experimental
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

- [Local Providers Guide](LOCAL_PROVIDERS.md) — Local provider diagnostics, endpoint validation, Ollama/LM Studio/llama.cpp examples
- [FAQ](FAQ.md) — Common questions about providers and AI integration
- [SECURITY](SECURITY.md) — Security policy and provider safety
- [ROADMAP](ROADMAP.md) — Planned provider implementations
- [ARCHITECTURE](ARCHITECTURE.md) — System architecture overview
- **Image Adapters** — See `python -m explainlens.cli image-adapters` and [SECURITY](SECURITY.md#image-adapter-safety-phase-4a) for the image adapter layer (separate from providers).
