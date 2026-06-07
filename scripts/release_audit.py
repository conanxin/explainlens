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
            # Docs contain legitimate usage examples (e.g. "export OPENAI_API_KEY=...")
            if "docs" in f.parts or ".github" in f.parts:
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if re.search(pattern, content):
                hits.append(f)
    return hits


def _run_cli_check(args: list[str], expected_exit: int = 0) -> bool:
    """Run a CLI command and return True if exit code matches expected.

    Args:
        args: CLI arguments (e.g., ["doctor"] or ["validate-endpoint", "http://..."])
        expected_exit: Expected exit code (default 0)

    Returns:
        True if the command exits with expected_exit.
    """
    import subprocess
    cli = [sys.executable, "-m", "explainlens.cli"] + args
    try:
        result = subprocess.run(
            cli,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT,
        )
        return result.returncode == expected_exit
    except Exception:
        return False


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
    all_pass &= check("pyproject.toml has version 0.3.0a0",
                      file_contains("pyproject.toml", r'version\s*=\s*"0\.3\.0a0"'),
                      "version must be 0.3.0a0 for v0.3.0-alpha release")
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
        (r"OPENAI_API_KEY\s*=\s*['\"]", "OPENAI_API_KEY assignment"),
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
    # openai moved to experimental in Phase 3.3
    all_pass &= check("openai provider is in AVAILABLE_PROVIDERS",
                      file_contains("src/explainlens/providers/registry.py",
                                    r'AVAILABLE_PROVIDERS\["openai"\]'),
                      "openai must be in AVAILABLE_PROVIDERS, not DISABLED_PROVIDERS")
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

    # --- Local Provider UX Polish (Phase 3.2C) ---
    print(">>> Local Provider UX Polish (Phase 3.2C)")
    all_pass &= check("docs/LOCAL_PROVIDERS.md exists",
                      file_exists("docs/LOCAL_PROVIDERS.md"))
    all_pass &= check("README contains validate-endpoint",
                      file_contains("README.md", r"validate-endpoint"),
                      "README must mention validate-endpoint command")
    all_pass &= check("README contains doctor",
                      file_contains("README.md", r"doctor"),
                      "README must mention doctor command")
    all_pass &= check("examples/configs/local-http-ollama.example.json exists",
                      file_exists("examples/configs/local-http-ollama.example.json"))
    all_pass &= check("examples/configs/local-http-lmstudio.example.json exists",
                      file_exists("examples/configs/local-http-lmstudio.example.json"))
    all_pass &= check("examples/configs/local-http-llamacpp.example.json exists",
                      file_exists("examples/configs/local-http-llamacpp.example.json"))
    all_pass &= check("doctor command runs",
                      _run_cli_check(["doctor"], expected_exit=0),
                      "doctor command must run without error")
    all_pass &= check("validate-endpoint localhost returns allowed",
                      _run_cli_check(["validate-endpoint", "http://localhost:11434/api/chat"], expected_exit=0),
                      "validate-endpoint must allow localhost")
    all_pass &= check("validate-endpoint api.openai.com returns rejected",
                      _run_cli_check(["validate-endpoint", "https://api.openai.com/v1/chat/completions"], expected_exit=1),
                      "validate-endpoint must reject remote URLs")
    all_pass &= check("SECURITY contains Authorization headers",
                      file_contains("docs/SECURITY.md", r"Authorization header"),
                      "SECURITY.md must mention Authorization headers safety")
    print()

    # --- OpenAI Provider (Phase 3.3) ---
    print(">>> OpenAI Provider (Phase 3.3)")
    all_pass &= check("openai_transport.py exists",
                      file_exists("src/explainlens/providers/openai_transport.py"),
                      "OpenAI transport module must exist")
    all_pass &= check("openai_draft.py contains OpenAIProvider class",
                      file_contains("src/explainlens/providers/openai_draft.py",
                                    r"class OpenAIProvider"),
                      "openai_draft.py must define OpenAIProvider class")
    all_pass &= check("openai is in AVAILABLE_PROVIDERS",
                      file_contains("src/explainlens/providers/registry.py",
                                    r'AVAILABLE_PROVIDERS\["openai"\]'),
                      "openai must be in AVAILABLE_PROVIDERS")
    all_pass &= check("openai status is experimental",
                      file_contains("src/explainlens/providers/contract.py",
                                    r"capabilities_for_openai"),
                      "contract.py must define capabilities_for_openai() with status='experimental'")
    all_pass &= check("README shows openai as experimental",
                      file_contains("README.md", r"openai.*[Ee]xperimental"),
                      "README provider table must show openai as experimental")
    all_pass &= check("No import openai library in OpenAI source",
                      not file_contains("src/explainlens/providers/openai_transport.py",
                                        r"^import openai\b"),
                      "openai_transport.py uses direct HTTP, must not import openai library")
    all_pass &= check("CLI --allow-external-api flag exists",
                      file_contains("src/explainlens/cli.py",
                                    r"--allow-external-api"),
                      "CLI must support --allow-external-api flag")
    all_pass &= check("CLI help shows --allow-external-api",
                      file_contains("src/explainlens/cli.py",
                                    r"help.*[Aa]llow.*external.*API"),
                      "CLI --help must describe --allow-external-api")
    all_pass &= check("OpenAI fail-closed tests in CI",
                      file_contains(".github/workflows/ci.yml",
                                    r"allow-external-api"),
                      "CI must test OpenAI fail-closed behavior")
    all_pass &= check("CI checks openai External API: yes",
                      file_contains(".github/workflows/ci.yml",
                                    r"External API: yes"),
                      "CI providers listing must show openai has External API: yes")
    all_pass &= check("OpenAI test files exist",
                      file_exists("tests/test_openai_transport.py")
                      and file_exists("tests/test_openai_provider.py")
                      and file_exists("tests/test_openai_cli.py")
                      and file_exists("tests/test_openai_security.py"),
                      "All 4 OpenAI test files must exist")
    print()

    # --- v0.2.0-alpha Release Readiness (Phase 3.4) ---
    print(">>> v0.2.0-alpha Release Readiness (Phase 3.4)")
    all_pass &= check("docs/releases/v0.2.0-alpha.md exists",
                      file_exists("docs/releases/v0.2.0-alpha.md"),
                      "Release notes must exist for v0.2.0-alpha")
    all_pass &= check("README mentions v0.2.0-alpha",
                      file_contains("README.md", r"v0\.2\.0-alpha"),
                      "README must mention v0.2.0-alpha")
    all_pass &= check("CHANGELOG contains v0.2.0-alpha",
                      file_contains("CHANGELOG.md", r"v0\.2\.0-alpha"),
                      "CHANGELOG must contain [v0.2.0-alpha] section")
    all_pass &= check("prepare_release.py suggests v0.2.0-alpha",
                      file_contains("scripts/prepare_release.py", r"v0\.2\.0-alpha"),
                      "prepare_release.py must map version to v0.2.0-alpha")
    all_pass &= check("Provider docs mention OpenAI opt-in",
                      file_contains("docs/PROVIDERS.md", r"openai.*fail-closed"),
                      "PROVIDERS.md must document OpenAI opt-in process")
    all_pass &= check("Security docs mention fail-closed external API",
                      file_contains("docs/SECURITY.md", r"fail-closed.*external|External.*fail-closed"),
                      "SECURITY.md must cover fail-closed external API rules")
    all_pass &= check("CI has openai fail-closed checks",
                      file_contains(".github/workflows/ci.yml", r"allow-external-api"),
                      "CI must test OpenAI fail-closed behavior")
    all_pass &= check("CI has local-http fixture checks",
                      file_contains(".github/workflows/ci.yml", r"ci_local_http_fixture"),
                      "CI must have local-http fixture smoke test")
    all_pass &= check("CI has doctor / validate-endpoint checks",
                      file_contains(".github/workflows/ci.yml", r"explainlens\.cli doctor"),
                      "CI must test doctor command")
    all_pass &= check("Release notes mention PDF support",
                      file_contains("docs/releases/v0.2.0-alpha.md", r"PDF.*input|PDF.*PyMuPDF|PDF.*support"),
                      "Release notes must describe PDF support")
    all_pass &= check("Release notes mention provider system",
                      file_contains("docs/releases/v0.2.0-alpha.md", r"Provider.*system|provider.*architecture"),
                      "Release notes must describe provider system")
    all_pass &= check("Release notes mention no OCR",
                      file_contains("docs/releases/v0.2.0-alpha.md", r"OCR"),
                      "Release notes must document OCR limitation")
    all_pass &= check("Release notes mention no real image generation",
                      file_contains("docs/releases/v0.2.0-alpha.md", r"Real image|image generation|图片生成"),
                      "Release notes must document no real image generation")
    print()

    # --- Image Adapter Interface (Phase 4A) ---
    print(">>> Image Adapter Interface (Phase 4A)")
    all_pass &= check("src/explainlens/images/base.py exists",
                      file_exists("src/explainlens/images/base.py"),
                      "Image adapter base must exist")
    all_pass &= check("src/explainlens/images/placeholder.py exists",
                      file_exists("src/explainlens/images/placeholder.py"),
                      "Placeholder image adapter must exist")
    all_pass &= check("src/explainlens/images/fixture.py exists",
                      file_exists("src/explainlens/images/fixture.py"),
                      "Fixture image adapter must exist")
    all_pass &= check("src/explainlens/images/registry.py exists",
                      file_exists("src/explainlens/images/registry.py"),
                      "Image adapter registry must exist")
    all_pass &= check("README contains image adapters",
                      file_contains("README.md", r"[Ii]mage adapters"),
                      "README must mention image adapters")
    all_pass &= check("SECURITY says no external image APIs",
                      file_contains("docs/SECURITY.md", r"[Ii]mage [Aa]dapter.*local-only|no external image"),
                      "SECURITY must state no external image APIs")
    all_pass &= check("CLI image-adapters command exists",
                      file_contains("src/explainlens/cli.py", r"image-adapters"),
                      "CLI must have image-adapters subcommand")
    all_pass &= check("CI has image adapter smoke test",
                      file_contains(".github/workflows/ci.yml", r"ci_image"),
                      "CI must test image adapter")
    all_pass &= check("CI checks image_manifest.json exists",
                      file_contains(".github/workflows/ci.yml", r"image_manifest\.json"),
                      "CI must verify image_manifest.json generation")
    all_pass &= check("CI checks image_jobs.json exists",
                      file_contains(".github/workflows/ci.yml", r"image_jobs\.json"),
                      "CI must verify image_jobs.json generation")
    all_pass &= check("CI checks uses_external_api false in image manifest",
                      file_contains(".github/workflows/ci.yml", r'"uses_external_api":\s*false.*image_manifest'),
                      "CI must verify uses_external_api: false in image manifest")
    all_pass &= check("CI checks images/ in cards.html",
                      file_contains(".github/workflows/ci.yml", r"images/card_"),
                      "CI must verify cards.html references images/")
    print()

    # --- Image Style Presets (Phase 4B) ---
    print(">>> Image Style Presets (Phase 4B)")
    all_pass &= check("src/explainlens/images/styles.py exists",
                      file_exists("src/explainlens/images/styles.py"),
                      "Image styles module must exist")
    all_pass &= check("CLI image-styles command works",
                      _run_cli_check(["image-styles"], expected_exit=0),
                      "image-styles CLI must list all styles")
    all_pass &= check("README links docs/GALLERY.md",
                      file_contains("README.md", r"docs/GALLERY\.md"),
                      "README must link to GALLERY.md")
    all_pass &= check("docs/GALLERY.md exists",
                      file_exists("docs/GALLERY.md"),
                      "GALLERY.md must exist")
    all_pass &= check("docs/assets/demo-preview.svg exists",
                      file_exists("docs/assets/demo-preview.svg"),
                      "demo-preview.svg must exist")
    all_pass &= check("image_manifest contains style",
                      file_contains("src/explainlens/images/manifest.py", r'"style":\s*style'),
                      "image_manifest must include style field")
    all_pass &= check("image_manifest contains generated_locally",
                      file_contains("src/explainlens/images/manifest.py", r"generated_locally"),
                      "image_manifest must include generated_locally")
    all_pass &= check("image_manifest contains external_image_api",
                      file_contains("src/explainlens/images/manifest.py", r"external_image_api"),
                      "image_manifest must include external_image_api")
    all_pass &= check("cards.html contains Image Manifest",
                      file_contains("src/explainlens/renderer.py", r"Image Manifest"),
                      "cards.html must contain Image Manifest section")
    all_pass &= check("cards.md contains Image Manifest",
                      file_contains("src/explainlens/exporters.py", r"Image Manifest"),
                      "cards.md must contain Image Manifest section")
    all_pass &= check("SECURITY mentions local SVG renderers",
                      file_contains("docs/SECURITY.md", r"local SVG renderers"),
                      "SECURITY must mention local SVG renderers")
    print()

    # --- OpenAI Image Adapter (Phase 4C) ---
    print(">>> OpenAI Image Adapter (Phase 4C)")
    all_pass &= check("src/explainlens/images/openai_image_transport.py exists",
                      file_exists("src/explainlens/images/openai_image_transport.py"),
                      "OpenAI image transport must exist")
    all_pass &= check("src/explainlens/images/openai_image.py exists",
                      file_exists("src/explainlens/images/openai_image.py"),
                      "OpenAI image adapter must exist")
    all_pass &= check("openai-image in AVAILABLE_IMAGE_ADAPTERS",
                      file_contains("src/explainlens/images/registry.py", r"openai-image"),
                      "openai-image must be registered")
    all_pass &= check("CLI --allow-external-images flag exists",
                      file_contains("src/explainlens/cli.py", r"--allow-external-images"),
                      "CLI must have --allow-external-images flag")
    all_pass &= check("SECURITY.md mentions openai-image",
                      file_contains("docs/SECURITY.md", r"openai-image"),
                      "SECURITY must mention openai-image")
    all_pass &= check("No API key in openai_image_transport.py",
                      not file_contains("src/explainlens/images/openai_image_transport.py", r"sk-[a-zA-Z0-9_-]{20,}"),
                      "No API key in openai_image_transport.py")
    all_pass &= check("No API key in openai_image.py",
                      not file_contains("src/explainlens/images/openai_image.py", r"sk-[a-zA-Z0-9_-]{20,}"),
                      "No API key in openai_image.py")
    all_pass &= check("CI has openai-image fail-closed check",
                      file_contains(".github/workflows/ci.yml", r"openai-image"),
                      "CI must check openai-image fail-closed")
    all_pass &= check("README mentions openai-image adapter",
                      file_contains("README.md", r"openai-image"),
                      "README must mention openai-image")
    print()

    # --- Local Web UI (Phase 5A) ---
    print(">>> Local Web UI (Phase 5A)")
    all_pass &= check("src/explainlens/web/app.py exists",
                      file_exists("src/explainlens/web/app.py"),
                      "Web app must exist")
    all_pass &= check("src/explainlens/web/run_manager.py exists",
                      file_exists("src/explainlens/web/run_manager.py"),
                      "Run manager must exist")
    all_pass &= check("docs/WEB_UI.md exists",
                      file_exists("docs/WEB_UI.md"),
                      "Web UI docs must exist")
    all_pass &= check("README contains python -m explainlens.web",
                      file_contains("README.md", r"python -m explainlens\.web"),
                      "README must mention web UI launch command")
    all_pass &= check("Web UI rejects openai provider",
                      file_contains("src/explainlens/web/app.py", r"BLOCKED_PROVIDERS"),
                      "Web UI must block openai provider")
    all_pass &= check("Web UI rejects openai-image adapter",
                      file_contains("src/explainlens/web/app.py", r"BLOCKED_IMAGE_ADAPTERS"),
                      "Web UI must block openai-image adapter")
    all_pass &= check("Web UI templates exist",
                      file_exists("src/explainlens/web/templates/layout.html") and
                      file_exists("src/explainlens/web/templates/dashboard.html") and
                      file_exists("src/explainlens/web/templates/run_detail.html"),
                      "All three templates must exist")
    all_pass &= check("Templates contain three-column layout markers",
                      file_contains("src/explainlens/web/templates/layout.html", r"sidebar") and
                      file_contains("src/explainlens/web/templates/layout.html", r"workspace") and
                      file_contains("src/explainlens/web/templates/layout.html", r"preview"),
                      "Templates must have sidebar/workspace/preview layout")
    all_pass &= check("No API key in templates",
                      not file_contains("src/explainlens/web/templates/layout.html", r"sk-[a-zA-Z0-9_-]{20,}") and
                      not file_contains("src/explainlens/web/templates/dashboard.html", r"sk-[a-zA-Z0-9_-]{20,}") and
                      not file_contains("src/explainlens/web/templates/run_detail.html", r"sk-[a-zA-Z0-9_-]{20,}"),
                      "No API key in templates")
    all_pass &= check("docs/WEB_UI.md mentions 127.0.0.1",
                      file_contains("docs/WEB_UI.md", r"127\.0\.0\.1"),
                      "Web UI docs must mention 127.0.0.1 binding")
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
