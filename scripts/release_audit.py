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
