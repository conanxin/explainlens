# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** file a public issue.
Instead, email the maintainers directly.

## Best Practices for Users

### Never Commit API Keys

- Use `.env` files (see `.env.example`)
- Never hardcode API keys in source code
- The `.gitignore` is configured to exclude `.env` files

### Never Upload Sensitive Documents

- Do not upload confidential papers or private documents as examples
- The `examples/` directory should only contain public-domain or permissively licensed content
- Review your output files before sharing them publicly

### Image API Integration (Future Phases)

When future phases add real image generation API support:

- Always use environment variables for API keys
- Never log or display API keys in output
- Use `.env.example` as a template, never commit your actual `.env`
- Rotate keys if accidentally committed

### Image Adapter Safety (Phase 4A/4B)

**Status:** local-only — no external image APIs are called.

**Current image adapters:**

| Adapter | Status | External API | API key | Description |
|---------|--------|-------------|---------|-------------|
| placeholder | available | no | no | Generates local SVG placeholder images with style presets |
| fixture | experimental | no | no | Deterministic SVG for CI/testing with style presets |

**Image style presets (Phase 4B):**

| Style | Description |
|-------|-------------|
| clean-cartoon-explainer | Clean cartoon-style, blue palette (default) |
| whiteboard | Whiteboard sketch, dark marker accents |
| storybook | Warm storybook, amber palette |
| technical-diagram | Precise diagram, green palette |

**Safety guarantees:**

1. **Current image adapters are local SVG renderers.**
   - `placeholder` and `fixture` generate SVG files purely locally.
   - No network requests, no API keys, no external services.

2. **Future real image adapters must fail closed.**
   - Any future adapter that calls external image APIs (DALL-E, Stable Diffusion, etc.) must require explicit opt-in.
   - Must require `--allow-external-image-api` or equivalent flag.
   - Must validate API keys before creating any output directory.

3. **Image prompts should not include secrets.**
   - Image prompts are derived from card titles and visual metaphors.
   - No API keys, passwords, or environment variables appear in prompts.
   - Prompt content is always safe for display in HTML/Markdown output.

4. **Transparent manifest.**
   - `image_manifest.json` discloses `style`, `generated_locally`, and `external_image_api`.
   - Every image record includes `safety_notes` confirming local-only generation.

5. **No real images.**
   - Phase 4B does NOT call DALL-E, Stable Diffusion, or any other image generation API.
   - Generated SVGs are educational illustrations — no photorealistic content.

6. **No document upload.**
   - Image adapters only consume card metadata (title, prompt) — source text is never sent to external services.
   - Prompt content is limited to card titles and visual metaphor descriptions.<｜end▁of▁thinking｜>

## Provider Safety

### External API providers must be opt-in

- Providers that make network requests must NOT be enabled by default
- The `openai` provider is fail-closed — requires `--allow-external-api` + `OPENAI_API_KEY`
- Disabled providers must fail closed (no partial output)
- Attempting to use a disabled provider must produce a clear error message

### OpenAI Provider Security (Phase 3.3)

**Status:** experimental — requires explicit opt-in.

**Safety rules:**

1. **API key via environment variable only.**
   - Uses `OPENAI_API_KEY` env var — no hardcoded keys in source
   - Key is validated BEFORE any output directory is created (fail-closed ordering)

2. **No SDK dependency.**
   - Uses direct HTTP (`urllib.request`) to `api.openai.com`
   - No `import openai` — avoids SDK code risk surface
   - No API key appears in payload, headers, or error messages

3. **Mock-only testing.**
   - All 81 OpenAI tests (4 test files) use `unittest.mock` — zero real API calls
   - CI fail-closed tests run without any `OPENAI_API_KEY` set

4. **Provider manifest disclosure.**
   - `uses_external_api: true`, `requires_api_key: true`
   - `safety.uploads_documents: true` (documents are sent to OpenAI API)
   - Manifest is regenerated on every run

### Provider manifest must disclose external API usage

Every analysis run produces a `provider_manifest.json` file that discloses:
- `uses_external_api`: whether network requests were made
- `requires_api_key`: whether an API key is needed
- `safety.uploads_documents`: whether documents are sent to external servers
- `safety.reads_api_key`: whether the provider reads API keys from environment
- `safety.writes_secrets`: whether the provider writes secrets to output files

### Disabled providers must fail closed

- Must NOT produce partial output files
- Must NOT create output directories (or must clean them up on failure)
- Must raise `RuntimeError` with a clear message
- Must list available providers in the error message

### Provider contract requires source traceability

- Every card must have non-empty `source_chunk_ids`
- `uses_external_api` must be set correctly
- No fabrication of data, claims, or conclusions

### Local-Fixture Provider

- Fully offline: no network calls, no subprocess spawning, no environment variable reads
- Safe for development and testing without any external dependencies
- Serves as the reference implementation for local provider safety

### Local HTTP Provider (local-http)

**Status:** experimental — requires explicit opt-in.

**Safety rules:**

1. **Only loopback endpoints allowed**
   - Allowed: `http://localhost:...`, `http://127.0.0.1:...`, `http://[::1]:...`
   - Rejected: any HTTPS, any remote HTTP, any LAN address (`192.168.x.x`, `10.x.x.x`, `172.16.x.x`)

2. **No Authorization headers**
   - The provider does NOT send `Authorization` headers
   - No API keys are read or attached

3. **No remote HTTP**
   - All requests must go to loopback addresses only
   - DNS rebinding protection: `localhost` is resolved to verify it maps to `127.0.0.1`

4. **`--allow-local-http` required**
   - Default behavior: **fail closed**
   - Must pass `--allow-local-http` to CLI for any HTTP call to proceed
   - Fixture protocol (`--local-http-protocol fixture`) does NOT require this flag

5. **Prompt content should not be logged**
   - The provider does NOT print full prompts to stdout/stderr
   - This avoids accidental exposure of document content in logs

**Provider manifest disclosure:**

The `provider_manifest.json` for `local-http` includes a `network` block:
```json
{
  "network": {
    "uses_local_http": false,
    "allows_remote_http": false,
    "endpoint": null,
    "protocol": "fixture",
    "timeout_seconds": 30
  }
}
```

When `uses_local_http` is `true`, the `endpoint` field will show the actual endpoint.

---

## Local Provider Security

### Local-Fixture Does Not Call Localhost

The `local-fixture` provider is explicitly designed to be fully offline:
- It does not make any network requests, including to localhost
- It does not spawn subprocesses
- It does not read environment variables
- All responses are generated locally from static data

### Future Local Providers Must Clearly Disclose Network Calls

Any future local provider that makes network calls (including to localhost) must:
- Explicitly disclose this behavior in its documentation
- Set `uses_external_api: true` in the provider manifest
- Be disabled by default if it makes external network requests

### Provider Prompt Dumps Must Not Include Secrets

When debugging or logging provider prompts:
- Never include API keys, tokens, or other secrets in prompt dumps
- Sanitize all output to remove sensitive information
- Use placeholder values (e.g., `sk-...`) when demonstrating prompt structures

---

## Phase 3.2C Security Updates

### `doctor` command does not call network

The `doctor` command is completely offline:
- No network requests
- No DNS resolution
- No subprocess spawning
- No file modifications
- Exit code 0 on success

```bash
python -m explainlens.cli doctor
```

### `validate-endpoint` does not call network

The `validate-endpoint` command performs **static validation only**:
- No HTTP requests
- No DNS resolution
- No network traffic of any kind
- Parses URL structure and validates against loopback-only policy

```bash
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
# Static check only — no network call

python -m explainlens.cli validate-endpoint https://api.openai.com/v1/chat/completions
# Static check only — rejects immediately, no network call
```

### Local provider configs are examples only

The files in `examples/configs/` are **reference templates**:
- They are NOT automatically loaded by ExplainLens
- They serve as documentation for users to understand the expected JSON structure
- Users must manually configure their own setup
- No secrets are included in these example files

### No Authorization headers

The `local-http` provider **never** sends `Authorization` headers:
- No API keys are read from environment variables
- No Bearer tokens are attached to requests
- No authentication credentials are sent
- This is by design — local model servers (Ollama, LM Studio, llama.cpp) typically don't require auth

**Verification:**
```bash
# Check provider manifest for safety disclosures
cat outputs/ci_local_http_fixture/provider_manifest.json | grep -A10 '"safety"'
```

Output should include:
```json
"safety": {
  "uploads_documents": false,
  "reads_api_key": false,
  "writes_secrets": false
}
```

---

## Dependency Security

- Keep dependencies updated
- We use only well-maintained, widely-used packages
- Current dependencies: `jinja2`, `pydantic`, `pytest` (dev)
