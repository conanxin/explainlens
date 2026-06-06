# Local Providers Guide

This guide explains ExplainLens's local provider system — how to use offline fixtures, call local model servers safely, and understand the security model.

---

## 1. What are local providers?

Local providers let ExplainLens generate explainer cards **without any external API calls**. They run entirely on your machine:

| Provider | Network needed? | What it does |
|---|---|---|
| `local-fixture` | No | Returns fixed fixture data (offline, deterministic) |
| `local-http` (fixture protocol) | No | Same fixture data, via the local-http provider interface |
| `local-http` (ollama-chat) | Yes (loopback only) | Calls a local Ollama server at `http://localhost:11434` |
| `local-http` (openai-compatible-chat) | Yes (loopback only) | Calls any OpenAI-compatible local server (LM Studio, llama.cpp, etc.) |

---

## 2. Provider differences

### `local-fixture` (experimental)

- Always offline — never touches the network.
- Returns deterministic fixture data for testing.
- Safe for CI, reproducible,零随机性。
- Use case: CI smoke tests, offline development, contract validation testing.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/fixture_demo \
  --provider local-fixture
```

### `local-http` fixture protocol

- Same offline fixture data, but routed through the `local-http` provider.
- Good for testing the local-http provider interface without a real model server.
- Zero network calls.

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_http_fixture \
  --provider local-http \
  --local-http-protocol fixture
```

### `local-http` ollama-chat protocol

- Calls a **local Ollama server** at `http://localhost:11434/api/chat`.
- Requires `--allow-local-http` flag (fail-closed by default).
- Only loopback endpoints allowed.

```bash
# Start Ollama server first: ollama serve
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_demo \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --local-http-model llama3.2 \
  --allow-local-http
```

### `local-http` openai-compatible-chat protocol

- Calls **any OpenAI-compatible local server** (LM Studio, llama.cpp server, etc.).
- Requires `--allow-local-http` flag.
- Only loopback endpoints allowed.

```bash
# LM Studio: start model server (usually at http://127.0.0.1:1234)
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/lm_studio_demo \
  --provider local-http \
  --local-http-protocol openai-compatible-chat \
  --local-http-endpoint http://127.0.0.1:1234/v1/chat/completions \
  --local-http-model local-model \
  --allow-local-http
```

---

## 3. Safety model

ExplainLens's local provider system is designed **fail-closed** — network access is disabled by default and must be explicitly opted into.

### Default: fail-closed

```bash
# This will FAIL with a clear error:
python -m explainlens.cli analyze \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --input examples/sample_article.txt \
  --output outputs/will_fail
```

Error:
```
local-http is fail-closed by default.
To call a local model server, add --allow-local-http.
Only loopback endpoints are allowed.
For CI-safe testing, use --local-http-protocol fixture.
```

### Loopback-only endpoint policy

Only these endpoints are allowed:

| Allowed | Rejected |
|---|---|
| `http://localhost:...` | `https://...` (any HTTPS) |
| `http://127.0.0.1:...` | `http://example.com/...` (remote host) |
| `http://[::1]:...` | `http://192.168.x.x/...` (private IP) |
| | `http://10.x.x.x/...` (private IP) |
| | `http://172.16.x.x/...` (private IP) |

### No Authorization headers

ExplainLens **never** sends:
- `Authorization` headers
- API keys
- Bearer tokens
- Any authentication credentials

### No remote HTTP

The `local-http` provider **cannot** connect to remote servers. Even if you accidentally pass `https://api.openai.com/...`, it will be rejected at the endpoint validation stage before any network request is made.

---

## 4. Ollama example

### Step 1: Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com/download
```

### Step 2: Start Ollama server

```bash
ollama serve
# Server starts at http://localhost:11434
```

### Step 3: Pull a model

```bash
ollama pull llama3.2
```

### Step 4: Run ExplainLens with Ollama

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_demo \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --local-http-model llama3.2 \
  --allow-local-http
```

### Ollama configuration template

See `examples/configs/local-http-ollama.example.json`:

```json
{
  "provider": "local-http",
  "local_http_protocol": "ollama-chat",
  "local_http_endpoint": "http://localhost:11434/api/chat",
  "local_http_model": "llama3.2",
  "allow_local_http": true,
  "timeout_seconds": 30
}
```

---

## 5. LM Studio example

### Step 1: Install LM Studio

Download from https://lmstudio.ai/

### Step 2: Load a model

1. Open LM Studio
2. Search and download a model (e.g., `llama-3.2-1b-instruct`)
3. Click the **「Local Server」** tab
4. Start the server (default: `http://127.0.0.1:1234`)

### Step 3: Run ExplainLens with LM Studio

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/lm_studio_demo \
  --provider local-http \
  --local-http-protocol openai-compatible-chat \
  --local-http-endpoint http://127.0.0.1:1234/v1/chat/completions \
  --local-http-model local-model \
  --allow-local-http
```

### LM Studio configuration template

See `examples/configs/local-http-lmstudio.example.json`:

```json
{
  "provider": "local-http",
  "local_http_protocol": "openai-compatible-chat",
  "local_http_endpoint": "http://127.0.0.1:1234/v1/chat/completions",
  "local_http_model": "local-model",
  "allow_local_http": true,
  "timeout_seconds": 30
}
```

---

## 6. llama.cpp server example

### Step 1: Build llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make
```

### Step 2: Start the server

```bash
./server -m models/llama-3.2-1b-instruct-q4_0.gguf -c 2048 --port 8080
# Server starts at http://127.0.0.1:8080
```

### Step 3: Run ExplainLens with llama.cpp

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/llama_cpp_demo \
  --provider local-http \
  --local-http-protocol openai-compatible-chat \
  --local-http-endpoint http://127.0.0.1:8080/v1/chat/completions \
  --local-http-model local-model \
  --allow-local-http
```

### llama.cpp configuration template

See `examples/configs/local-http-llamacpp.example.json`:

```json
{
  "provider": "local-http",
  "local_http_protocol": "openai-compatible-chat",
  "local_http_endpoint": "http://127.0.0.1:8080/v1/chat/completions",
  "local_http_model": "local-model",
  "allow_local_http": true,
  "timeout_seconds": 30
}
```

---

## 7. Dry-run endpoint validation

Before trying to connect to a local model server, validate your endpoint **without sending any network request**:

```bash
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
# Output:
# Endpoint: http://localhost:11434/api/chat
# Allowed: yes
# Reason: loopback endpoint

python -m explainlens.cli validate-endpoint https://api.openai.com/v1/chat/completions
# Output:
# Endpoint: https://api.openai.com/v1/chat/completions
# Allowed: no
# Reason: only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed for local-http
```

**This command does NOT:**
- Connect to the endpoint
- Send any network traffic
- Perform DNS resolution
- Read any API keys

It only does **static validation** against the loopback-only policy.

---

## 8. Dump provider prompt safely

To inspect the exact prompt pack sent to the provider (for debugging), use `--dump-provider-prompt`:

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/debug_prompt \
  --provider local-fixture \
  --dump-provider-prompt
```

This writes `provider_prompt_pack.json` to the output directory.

**Safety:**
- No API keys are included.
- No environment variables are read.
- No secrets are leaked.
- The file is safe to inspect and share.

---

## 9. Current limitations

The `local-http` provider is **experimental**. Current limitations:

| Limitation | Description |
|---|---|
| No streaming | Responses are buffered entirely before parsing. Large models may timeout. |
| No auth | No support for API keys, Bearer tokens, or any authentication. Local servers typically don't need auth. |
| No remote endpoints | Only loopback (`localhost`, `127.0.0.1`, `::1`) is allowed. Cannot connect to remote servers. |
| No prompt logging | Prompts are not logged to disk. Use `--dump-provider-prompt` to inspect. |
| No automatic model detection | You must specify `--local-http-model` manually. |
| No retry logic | A failed request fails immediately. No exponential backoff. |
| No concurrent requests | Requests are sequential. No batching or parallelism. |
| Timeout hardcoded | Timeout is set via `--local-http-timeout` but not adaptive. |

---

## 10. Troubleshooting

### Connection refused

```
urllib.error.URLError: [Errno 10061] Connection refused
```

**Cause:** The local model server is not running.

**Fix:**
```bash
# Ollama
ollama serve

# LM Studio: click "Start Server" in the Local Server tab

# llama.cpp
./server -m <model-path> --port 8080
```

---

### Invalid endpoint

```
Endpoint rejected: http://example.com:11434/api/chat
Reason: only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed for local-http
```

**Cause:** The endpoint is not a loopback address.

**Fix:** Use `localhost`, `127.0.0.1`, or `[::1]`:
```bash
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
```

---

### Model not found

```
HTTP 404 from http://localhost:11434/api/chat: model 'llama3.2' not found
```

**Cause:** The specified model is not available in your local server.

**Fix:**
```bash
# Ollama
ollama list          # List available models
ollama pull llama3.2  # Pull the model

# LM Studio / llama.cpp: ensure the model is loaded in the server UI
```

---

### Non-JSON model response

```
Provider response content is not valid JSON. Protocol: ollama-chat.
```

**Cause:** The local model server returned a non-JSON response (possibly an error page or plain text).

**Fix:**
1. Check the model server logs.
2. Verify the endpoint URL is correct.
3. Try with `--local-http-protocol fixture` to isolate whether the issue is the model or the prompt.

---

### Output contract validation failed

```
ValidationError: Field 'concept_map' missing in provider response.
```

**Cause:** The local model did not return JSON matching the expected output contract.

**Fix:**
1. Use a larger/more capable model (small models may not follow JSON format instructions well).
2. Check `provider_prompt_pack.json` to verify the prompt is correct.
3. Try with `--local-http-protocol fixture` to verify the contract logic works.

---

## 11. Diagnostics

Run the built-in doctor command for a quick health check:

```bash
python -m explainlens.cli doctor
```

Output:
```
ExplainLens Doctor

Python: 3.x
Package import: OK
Providers:
  - rule-based: available
  - mock-llm: available
  - local-fixture: experimental
  - local-http: experimental
  - openai: disabled

Local HTTP:
  - Default network access: disabled
  - Allowed endpoint policy: loopback only
  - Remote endpoints: rejected
  - Authorization headers: never sent
  - Real local model check: skipped by default

Artifacts:
  - source_index.json: supported
  - provider_manifest.json: supported
  - provider_prompt_pack.json: supported with --dump-provider-prompt
```

**This command does NOT:**
- Connect to any network endpoint
- Read API keys
- Execute any external command
- Modify any files

---

## 12. Security audit

To verify the security properties of your ExplainLens installation:

```bash
python scripts/release_audit.py
```

Look for these passing checks:

```
>>> Local HTTP Provider (Phase 3.2B)
  [PASS] src/explainlens/providers/local_http.py exists
  [PASS] src/explainlens/providers/local_http_transport.py exists
  [PASS] README contains local-http
  [PASS] docs/SECURITY.md contains loopback
  [PASS] CLI providers output includes local-http
  [PASS] local-http fixture smoke test in CI
  [PASS] CI includes network block check
  [PASS] CI includes fail-closed check for local-http
  [PASS] remote endpoint is rejected
  [PASS] .env.example does not include local HTTP secrets
```

---

## 13. Further reading

- [Provider System Overview](PROVIDERS.md)
- [Security Policy](SECURITY.md)
- [FAQ](FAQ.md)
- [Release Audit](scripts/release_audit.py)
