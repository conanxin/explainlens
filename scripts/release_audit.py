#!/usr/bin/env python3
"""Pre-release audit script for ExplainLens.

Runs a series of checks and exits with code 1 if any fail.

Usage:
    python scripts/release_audit.py
"""

import os
import re
import sys
from pathlib import Path

# Fix Windows GBK encoding issue
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check(name: str, condition: bool, detail: str = "") -> bool:
    """Report a single check result. Returns True if passed."""
    status = "PASS" if condition else "BLOCKED"
    line = f"  [{status}] {name}"
    if detail and not condition:
        line += f" -- {detail}"
    print(line)
    return condition


def file_exists(rel_path: str) -> bool:
    return (PROJECT_ROOT / rel_path).is_file()


def file_contains(rel_path: str, pattern: str) -> bool:
    path = PROJECT_ROOT / rel_path
    if not path.is_file():
        return False
    return bool(re.search(pattern, path.read_text(encoding="utf-8")))


def grep_source(pattern: str) -> list[Path]:
    """Search all tracked source files for pattern."""
    hits = []
    for ext in (".py", ".md", ".toml", ".txt", ".yaml", ".yml", ".cfg", ".ini"):
        for f in PROJECT_ROOT.rglob(f"*{ext}"):
            if "outputs" in f.parts or ".git" in f.parts:
                continue
            if "__pycache__" in f.parts or ".egg-info" in f.parts:
                continue
            if ".pytest_cache" in f.parts or ".workbuddy" in f.parts:
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if re.search(pattern, content):
                hits.append(f)
    return hits


def main() -> int:
    print("=" * 60)
    print("  ExplainLens -- Release Audit")
    print("=" * 60)
    print()

    all_pass = True

    # --- Documentation ---
    print(">>> Documentation")
    all_pass &= check("README.md exists", file_exists("README.md"))
    all_pass &= check("README.md has correct GitHub URL",
                      file_contains("README.md", r"conanxin/explainlens"),
                      "README must reference conanxin/explainlens")
    all_pass &= check("README.md does NOT have wrong GitHub URL",
                      not file_contains("README.md", r"github\.com/explainlens/explainlens"),
                      "README must NOT reference explainlens/explainlens")
    all_pass &= check("LICENSE exists", file_exists("LICENSE"))
    all_pass &= check("CHANGELOG.md exists", file_exists("CHANGELOG.md"))
    all_pass &= check("docs/QUICKSTART.md exists", file_exists("docs/QUICKSTART.md"))
    all_pass &= check("docs/FAQ.md exists", file_exists("docs/FAQ.md"))
    all_pass &= check("docs/CONTRIBUTING.md exists", file_exists("docs/CONTRIBUTING.md"))
    all_pass &= check("docs/SECURITY.md exists", file_exists("docs/SECURITY.md"))
    all_pass &= check("docs/ROADMAP.md exists", file_exists("docs/ROADMAP.md"))
    all_pass &= check("docs/DEMO.md exists", file_exists("docs/DEMO.md"))
    all_pass &= check("docs/PROVIDERS.md exists", file_exists("docs/PROVIDERS.md"))
    all_pass &= check("docs/assets/demo-preview.svg exists",
                      file_exists("docs/assets/demo-preview.svg"))
    print()

    # --- Configuration ---
    print(">>> Configuration")
    all_pass &= check("pyproject.toml exists", file_exists("pyproject.toml"))
    all_pass &= check("pyproject.toml has correct name",
                      file_contains("pyproject.toml", r'name\s*=\s*"explainlens"'),
                      "project name must be 'explainlens'")
    all_pass &= check("pyproject.toml has version 0.1.0",
                      file_contains("pyproject.toml", r'version\s*=\s*"0\.1\.0"'),
                      "version must be 0.1.0")
    all_pass &= check(".gitignore exists", file_exists(".gitignore"))
    all_pass &= check(".gitignore covers .env",
                      file_contains(".gitignore", r"\.env"))
    all_pass &= check(".gitignore covers __pycache__",
                      file_contains(".gitignore", r"__pycache__"))
    all_pass &= check(".gitignore covers outputs/*/",
                      file_contains(".gitignore", r"outputs/\*/"))
    all_pass &= check(".env.example exists", file_exists(".env.example"))
    all_pass &= check(".env.example has no real API key",
                      not file_contains(".env.example", r"sk-[a-zA-Z0-9]{20,}"),
                      ".env.example must not contain real API keys")
    print()

    # --- Security ---
    print(">>> Security")
    env_committed = (PROJECT_ROOT / ".env").is_file()
    all_pass &= check(".env is NOT committed", not env_committed,
                      ".env file found in project root -- should NOT be committed")

    secret_patterns = [
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key (sk-...)"),
        (r"OPENAI_API_KEY\s*=", "OPENAI_API_KEY assignment"),
        (r"password\s*=\s*['\"]\S+['\"]", "hardcoded password"),
        (r"token\s*=\s*['\"]\S+['\"]", "hardcoded token"),
        (r"secret\s*=\s*['\"]\S+['\"]", "hardcoded secret"),
    ]
    for pattern, description in secret_patterns:
        hits = grep_source(pattern)
        all_pass &= check(f"No {description} in source", len(hits) == 0,
                          f"Found in: {', '.join(str(h) for h in hits)}")
    print()

    # --- Examples ---
    print(">>> Examples")
    all_pass &= check("sample_article.txt exists",
                      file_exists("examples/sample_article.txt"))
    all_pass &= check("sample_paper_excerpt.txt exists",
                      file_exists("examples/sample_paper_excerpt.txt"))
    all_pass &= check("sample_ai_research_note.txt exists",
                      file_exists("examples/sample_ai_research_note.txt"))
    all_pass &= check("outputs/.gitkeep exists",
                      file_exists("outputs/.gitkeep"),
                      "outputs/.gitkeep should be tracked to preserve the output directory")
    print()

    # --- PDF Support ---
    print(">>> PDF Support")
    all_pass &= check("pymupdf in pyproject.toml dependencies",
                      file_contains("pyproject.toml", r"pymupdf>=1\.24"),
                      "pymupdf must be in dependencies")
    all_pass &= check("scripts/create_sample_pdf.py exists",
                      file_exists("scripts/create_sample_pdf.py"))
    all_pass &= check("README contains PDF input section",
                      file_contains("README.md", r"PDF 输入"),
                      "README must document PDF support")
    all_pass &= check("FAQ mentions PDF support",
                      file_contains("docs/FAQ.md", r"Phase 2 已支持"),
                      "FAQ must reflect Phase 2 PDF support")
    all_pass &= check("FAQ mentions scanned PDF limitation",
                      file_contains("docs/FAQ.md", r"扫描版 PDF"),
                      "FAQ must document scanned PDF limitation")
    print()

    # --- Source Citations ---
    print(">>> Source Citations")
    all_pass &= check("src/explainlens/source_index.py exists",
                      file_exists("src/explainlens/source_index.py"),
                      "source_index module must exist")
    all_pass &= check("README mentions source_index.json",
                      file_contains("README.md", r"source_index\.json"),
                      "README must mention source_index.json output")
    all_pass &= check("FAQ contains source citations explanation",
                      file_contains("docs/FAQ.md", r"Source citations"),
                      "FAQ must document source citation feature")
    all_pass &= check("FAQ mentions Source Appendix",
                      file_contains("docs/FAQ.md", r"Source Appendix"),
                      "FAQ must mention Source Appendix")
    all_pass &= check("source_index.json output checkable in CI",
                      file_contains(".github/workflows/ci.yml",
                                    r"source_index\.json"),
                      "CI must verify source_index.json is generated")
    all_pass &= check("CI checks for Source Appendix in HTML",
                      file_contains(".github/workflows/ci.yml",
                                    r"Source Appendix"),
                      "CI must verify Source Appendix in cards.html")
    all_pass &= check("CI checks for source anchors in HTML",
                      file_contains(".github/workflows/ci.yml",
                                    r"source-chunk_"),
                      "CI must verify source-chunk anchors in cards.html")
    print()

    # --- Provider Interface ---
    print(">>> Provider Interface")
    all_pass &= check("src/explainlens/providers/base.py exists",
                      file_exists("src/explainlens/providers/base.py"),
                      "Provider base class must exist")
    all_pass &= check("src/explainlens/providers/rule_based.py exists",
                      file_exists("src/explainlens/providers/rule_based.py"),
                      "rule-based provider must exist")
    all_pass &= check("src/explainlens/providers/mock_llm.py exists",
                      file_exists("src/explainlens/providers/mock_llm.py"),
                      "mock-llm provider must exist")
    all_pass &= check("src/explainlens/providers/registry.py exists",
                      file_exists("src/explainlens/providers/registry.py"),
                      "Provider registry must exist")
    all_pass &= check("README contains --provider mock-llm",
                      file_contains("README.md", r"--provider mock-llm"),
                      "README must document mock-llm usage")
    all_pass &= check("docs/PROVIDERS.md exists",
                      file_exists("docs/PROVIDERS.md"),
                      "Provider documentation must exist")
    all_pass &= check(".env.example exists",
                      file_exists(".env.example"),
                      ".env.example must exist")
    all_pass &= check(".env.example has no real API key",
                      not file_contains(".env.example", r"sk-[a-zA-Z0-9]{20,}"),
                      ".env.example must not contain real API keys")
    all_pass &= check("CI has mock provider smoke test",
                      file_contains(".github/workflows/ci.yml",
                                    r"--provider mock-llm"),
                      "CI must include a mock-llm smoke test")
    all_pass &= check("CI checks uses_external_api: false",
                      file_contains(".github/workflows/ci.yml",
                                    r"uses_external_api.*false"),
                      "CI must verify uses_external_api is false")
    print()

    # --- Provider Contract (Phase 3.1) ---
    print(">>> Provider Contract (Phase 3.1)")
    all_pass &= check("src/explainlens/providers/contract.py exists",
                      file_exists("src/explainlens/providers/contract.py"),
                      "Provider contract module must exist")
    all_pass &= check("src/explainlens/providers/openai_draft.py exists",
                      file_exists("src/explainlens/providers/openai_draft.py"),
                      "Disabled OpenAI provider draft must exist")
    all_pass &= check("README contains provider status table",
                      file_contains("README.md", r"\|\s*Available\s*\|"),
                      "README must show provider status table")
    all_pass &= check("docs/PROVIDERS.md contains provider lifecycle",
                      file_contains("docs/PROVIDERS.md", r"Provider lifecycle"),
                      "PROVIDERS.md must document provider lifecycle")
    all_pass &= check("docs/PROVIDERS.md contains provider manifest",
                      file_contains("docs/PROVIDERS.md", r"provider_manifest"),
                      "PROVIDERS.md must document provider_manifest")
    all_pass &= check("docs/SECURITY.md contains external API providers",
                      file_contains("docs/SECURITY.md", r"external API"),
                      "SECURITY.md must cover external API provider safety")
    all_pass &= check("CLI providers command runs",
                      file_contains(".github/workflows/ci.yml",
                                    r"explainlens\.cli providers"),
                      "CI should test the providers subcommand")
    all_pass &= check("CI generates provider_manifest.json",
                      file_contains(".github/workflows/ci.yml",
                                    r"provider_manifest\.json"),
                      "CI must verify provider_manifest.json is generated")
    all_pass &= check("provider_manifest uses_external_api is false",
                      file_contains(".github/workflows/ci.yml",
                                    r"uses_external_api.*false"),
                      "CI must verify uses_external_api is false in manifest")
    all_pass &= check(".env.example has no real API key",
                      not file_contains(".env.example", r"sk-[a-zA-Z0-9]{20,}"),
                      ".env.example must not contain real API keys")
    # Check that openai provider is disabled (error message exists in source)
    openai_disabled = grep_source(r"Provider.*openai.*disabled")
    all_pass &= check("disabled OpenAI provider cannot run",
                      len(openai_disabled) > 0,
                      "OpenAI provider must be disabled with clear error")
    print()

    # --- Local Fixture Provider (Phase 3.2A) ---
    print(">>> Local Fixture Provider (Phase 3.2A)")
    all_pass &= check("src/explainlens/providers/prompt_contract.py exists",
                      file_exists("src/explainlens/providers/prompt_contract.py"),
                      "Prompt contract module must exist")
    all_pass &= check("src/explainlens/providers/response_contract.py exists",
                      file_exists("src/explainlens/providers/response_contract.py"),
                      "Response contract module must exist")
    all_pass &= check("src/explainlens/providers/fixture_transport.py exists",
                      file_exists("src/explainlens/providers/fixture_transport.py"),
                      "Fixture transport module must exist")
    all_pass &= check("src/explainlens/providers/local_fixture.py exists",
                      file_exists("src/explainlens/providers/local_fixture.py"),
                      "Local fixture provider must exist")
    all_pass &= check("README contains local-fixture",
                      file_contains("README.md", r"local-fixture"),
                      "README must mention local-fixture")
    all_pass &= check("docs/PROVIDERS.md contains prompt contract",
                      file_contains("docs/PROVIDERS.md", r"prompt.contract"),
                      "PROVIDERS.md must document prompt contract")
    all_pass &= check("docs/SECURITY.md contains localhost",
                      file_contains("docs/SECURITY.md", r"localhost"),
                      "SECURITY.md must address localhost safety")
    all_pass &= check("CLI providers output includes local-fixture",
                      file_contains(".github/workflows/ci.yml", r"local-fixture"),
                      "CI must include local-fixture")
    all_pass &= check("CI generates provider_manifest.json for local-fixture",
                      file_contains(".github/workflows/ci.yml",
                                    r"local-fixture.*provider_manifest"),
                      "CI must verify provider_manifest for local-fixture")
    all_pass &= check("provider_manifest uses_external_api false (local-fixture)",
                      file_contains(".github/workflows/ci.yml",
                                    r"uses_external_api.*false"),
                      "CI must verify uses_external_api=false for all providers")
    print()

    # --- Local HTTP Provider (Phase 3.2B) ---
    print(">>> Local HTTP Provider (Phase 3.2B)")
    all_pass &= check("src/explainlens/providers/local_http.py exists",
                      file_exists("src/explainlens/providers/local_http.py"),
                      "Local HTTP provider must exist")
    all_pass &= check("src/explainlens/providers/local_http_transport.py exists",
                      file_exists("src/explainlens/providers/local_http_transport.py"),
                      "Local HTTP transport module must exist")
    all_pass &= check("README contains local-http",
                      file_contains("README.md", r"local-http"),
                      "README must mention local-http")
    all_pass &= check("docs/SECURITY.md contains loopback",
                      file_contains("docs/SECURITY.md", r"loopback"),
                      "SECURITY.md must address loopback safety")
    all_pass &= check("CLI providers output includes local-http",
                      file_contains(".github/workflows/ci.yml", r"local-http"),
                      "CI must include local-http")
    all_pass &= check("local-http fixture smoke test in CI",
                      file_contains(".github/workflows/ci.yml", r"ci_local_http_fixture"),
                      "CI must have local-http fixture smoke test")
    all_pass &= check("CI includes network block check",
                      file_contains(".github/workflows/ci.yml", r"uses_local_http"),
                      "CI must verify network block in manifest")
    all_pass &= check("CI includes fail-closed check for local-http",
                      file_contains(".github/workflows/ci.yml", r"ci_local_http_blocked"),
                      "CI must verify local-http fails closed")
    all_pass &= check("remote endpoint is rejected",
                      file_contains(".github/workflows/ci.yml", r"ci.*local.*http.*blocked"),
                      "CI must check remote endpoint rejection")
    all_pass &= check(".env.example does not include local HTTP secrets",
                      not file_contains(".env.example", r"LOCAL_HTTP_API_KEY"),
                      ".env.example must not include local HTTP secrets")
    print()

    # --- CI ---
    print(">>> CI")
    all_pass &= check(".github/workflows/ci.yml exists",
                      file_exists(".github/workflows/ci.yml"))
    print()

    # --- Scripts ---
    print(">>> Scripts")
    all_pass &= check("scripts/release_audit.py exists",
                      file_exists("scripts/release_audit.py"))
    all_pass &= check("scripts/prepare_release.py exists",
                      file_exists("scripts/prepare_release.py"))
    print()

    # --- Summary ---
    print("=" * 60)
    if all_pass:
        print("  RESULT: ALL CHECKS PASSED -- Ready for release")
        print("=" * 60)
        return 0
    else:
        print("  RESULT: SOME CHECKS FAILED -- Fix before release")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
