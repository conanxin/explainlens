# Open Source Release Checklist

Last updated: 2026-06-04 for v0.1.0-alpha

---

## Code Quality

- [x] All tests pass: `python -m pytest` — 33/33
- [x] Source compiles clean: `python -m compileall src tests`
- [x] Code is readable and maintainable
- [x] No "one-liner" compressed code

## Security

- [x] No API keys committed (no `sk-` patterns in source)
- [x] No passwords or secrets in source code
- [x] No private data in example files (both examples are fictional/public)
- [x] `.env` is in `.gitignore` and not committed
- [x] `outputs/*/` is in `.gitignore` (run outputs excluded)

## Documentation

- [x] README.md — complete with install, quick start, output table, architecture
- [x] LICENSE — MIT, exists and correct
- [x] CHANGELOG.md — v0.1.0-alpha entry
- [x] docs/QUICKSTART.md — step-by-step from clone to preview
- [x] docs/FAQ.md — answers 8+ common questions
- [x] docs/CONTRIBUTING.md — contribution workflow
- [x] docs/SECURITY.md — security policy
- [x] docs/ROADMAP.md — Phase 1-6 plan
- [x] docs/ARCHITECTURE.md — system architecture
- [x] docs/PRODUCT_SPEC.md — product specification

## Examples

- [x] `examples/sample_article.txt` — Transformer article (public knowledge)
- [x] `examples/sample_paper_excerpt.txt` — fictional GNN paper
- [x] Example command in README runs successfully

## CI

- [x] `.github/workflows/ci.yml` — tests on Python 3.10, 3.11, 3.12
- [x] CI includes compile check, pytest, and CLI smoke test
- [x] CI badge in README

## Repository

- [x] `git status` is clean
- [x] `.gitignore` covers: __pycache__, .env, venv, outputs, .pytest_cache, .workbuddy, node_modules
- [x] Configuration files are valid (pyproject.toml, .gitignore)

## Release Tooling

- [x] `scripts/release_audit.py` — automated pre-release checks
- [x] Release audit runs and passes

## GitHub (needs manual setup)

The following must be set manually on the GitHub repository page:

- [ ] **About → Description:**
  Turn papers and complex texts into visual explainer cards and cartoon storyboards.
- [ ] **About → Website:** (leave empty for now)
- [ ] **Topics:**
  `ai` `education` `visualization` `nlp` `explainer` `storyboard` `cartoon` `papers` `python` `knowledge-tools`
- [ ] **First Release:** Create a GitHub Release tagged `v0.1.0-alpha`

## Verified Commands

```bash
# Install
git clone https://github.com/conanxin/explainlens.git
cd explainlens
pip install -e ".[dev]"

# Test
python -m pytest                  # 33 passed

# Run
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/sample_run

# Audit
python scripts/release_audit.py   # ALL PASSED
```
