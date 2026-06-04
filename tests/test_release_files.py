"""Format gate tests for release files.

Ensures key files are readable, properly formatted, and contain correct metadata.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    """Read a file relative to project root."""
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def _line_count(path: str) -> int:
    """Count lines in a file."""
    return len(_read(path).splitlines())


# ---------------------------------------------------------------------------
# 1. README.md — correct repository URL
# ---------------------------------------------------------------------------

def test_readme_has_correct_clone_url():
    """README.md must contain the correct GitHub clone URL."""
    content = _read("README.md")
    assert "github.com/conanxin/explainlens" in content, \
        "README must reference conanxin/explainlens"


def test_readme_does_not_have_wrong_url():
    """README.md must NOT contain the placeholder clone URL."""
    content = _read("README.md")
    assert "github.com/explainlens/explainlens" not in content, \
        "README must NOT reference explainlens/explainlens"


# ---------------------------------------------------------------------------
# 2. pyproject.toml — parsable and valid
# ---------------------------------------------------------------------------

def test_pyproject_toml_is_parsable():
    """pyproject.toml must be parsable as TOML."""
    content = _read("pyproject.toml")
    if sys.version_info >= (3, 11):
        import tomllib
        tomllib.loads(content)
    else:
        # Python 3.10: fallback to basic regex checks
        assert re.search(r'\[project\]', content), "Missing [project] section"
        assert re.search(r'name\s*=\s*"explainlens"', content), \
            "Missing or wrong project name"


def test_pyproject_toml_has_correct_name():
    """pyproject.toml project name must be explainlens."""
    content = _read("pyproject.toml")
    assert re.search(r'name\s*=\s*"explainlens"', content), \
        "project name must be 'explainlens'"


def test_pyproject_toml_has_version():
    """pyproject.toml must have a version field."""
    content = _read("pyproject.toml")
    assert re.search(r'version\s*=\s*"0\.\d+\.\d+', content), \
        "Missing or wrong version"


# ---------------------------------------------------------------------------
# 3. CI workflow — exists and is multi-line YAML
# ---------------------------------------------------------------------------

def test_ci_yml_exists():
    """GitHub Actions CI file must exist."""
    path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    assert path.is_file(), ".github/workflows/ci.yml not found"


def test_ci_yml_is_not_single_line():
    """ci.yml must be a proper multi-line YAML file."""
    lines = _line_count(".github/workflows/ci.yml")
    assert lines >= 10, f"ci.yml has only {lines} lines — likely compressed"


# ---------------------------------------------------------------------------
# 4. release_audit.py — exists and is multi-line Python
# ---------------------------------------------------------------------------

def test_release_audit_exists():
    """Release audit script must exist."""
    path = PROJECT_ROOT / "scripts" / "release_audit.py"
    assert path.is_file(), "scripts/release_audit.py not found"


def test_release_audit_is_not_single_line():
    """release_audit.py must be a proper multi-line Python file."""
    lines = _line_count("scripts/release_audit.py")
    assert lines >= 20, \
        f"release_audit.py has only {lines} lines — likely compressed"


# ---------------------------------------------------------------------------
# 5. Markdown files — not compressed single-line
# ---------------------------------------------------------------------------

MARKDOWN_MIN_LINES = {
    "README.md": 30,
    "CHANGELOG.md": 10,
    "docs/QUICKSTART.md": 20,
    "docs/FAQ.md": 20,
    "docs/CONTRIBUTING.md": 10,
    "docs/SECURITY.md": 10,
    "docs/ROADMAP.md": 15,
}


def test_markdown_files_are_multi_line():
    """Key Markdown files must not be compressed into single lines."""
    failures = []
    for rel_path, min_lines in MARKDOWN_MIN_LINES.items():
        full_path = PROJECT_ROOT / rel_path
        if not full_path.is_file():
            failures.append(f"{rel_path}: MISSING")
            continue
        actual = _line_count(rel_path)
        if actual < min_lines:
            failures.append(f"{rel_path}: {actual} lines < {min_lines} minimum")
    assert not failures, "Compressed/missing MD files:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# 6. LICENSE
# ---------------------------------------------------------------------------

def test_license_is_mit():
    """LICENSE file must contain MIT License text."""
    content = _read("LICENSE")
    assert "MIT" in content or "mit" in content.lower(), \
        "LICENSE does not appear to be MIT"
