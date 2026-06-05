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

## Provider Safety

### External API providers must be opt-in

- Providers that make network requests must NOT be enabled by default
- Disabled providers must fail closed (no partial output)
- Attempting to use a disabled provider must produce a clear error message

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

## Dependency Security

- Keep dependencies updated
- We use only well-maintained, widely-used packages
- Current dependencies: `jinja2`, `pydantic`, `pytest` (dev)
