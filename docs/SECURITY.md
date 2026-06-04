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

## Dependency Security

- Keep dependencies updated
- We use only well-maintained, widely-used packages
- Current dependencies: `jinja2`, `pydantic`, `pytest` (dev)
