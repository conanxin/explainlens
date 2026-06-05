#!/usr/bin/env python3
"""Release preparation script for ExplainLens.

Runs a series of pre-release checks and prints a suggested release command.
Does NOT create tags, does NOT publish to GitHub.

Usage:
    python scripts/prepare_release.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Resolve project root relative to this script's location
ROOT = Path(__file__).resolve().parent.parent

# Fix Windows GBK encoding issue
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(_sys.stderr, "reconfigure"):
    _sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _ok(label: str) -> None:
    print(f"  [PASS]  {label}")


def _fail(label: str, detail: str = "") -> None:
    msg = f"  [FAIL]  {label}"
    if detail:
        msg += f"\n          -> {detail}"
    print(msg)


def check_version_from_pyproject() -> str | None:
    """Parse version from pyproject.toml."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        # Python 3.11+ has tomllib in stdlib
        import tomllib  # type: ignore
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version")
    except ImportError:
        # Fallback: simple regex
        import re
        text = pyproject.read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else None


def main() -> int:
    print()
    print("=" * 60)
    print("  ExplainLens — Release Preparation Check")
    print("=" * 60)
    print()

    all_pass = True

    # 1. Read version from pyproject.toml
    version = check_version_from_pyproject()
    if version:
        _ok(f"Version from pyproject.toml: {version}")
    else:
        _fail("Could not read version from pyproject.toml")
        all_pass = False

    print()
    print("--- File Checks ---")

    # 2. CHANGELOG contains version string
    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists() and version and version in changelog.read_text(encoding="utf-8"):
        _ok(f"CHANGELOG.md contains version {version}")
    else:
        _fail(
            f"CHANGELOG.md does not mention version {version}",
            "Add a changelog entry for this version before releasing.",
        )
        all_pass = False

    # 3. Release notes file exists (allow suffix like -alpha, -beta, -rc1)
    releases_dir = ROOT / "docs" / "releases"
    tag_prefix = f"v{version}" if version else "v0.0.0"
    # Find any release notes file starting with the version tag
    matching_notes = list(releases_dir.glob(f"{tag_prefix}*.md")) if releases_dir.exists() else []
    if matching_notes:
        release_notes = matching_notes[0]
        _ok(f"Release notes exist: docs/releases/{release_notes.name}")
    else:
        release_notes = releases_dir / f"{tag_prefix}.md"
        _fail(
            f"Release notes not found: docs/releases/{tag_prefix}*.md",
            f"Create docs/releases/{tag_prefix}.md (or {tag_prefix}-alpha.md etc.) with release notes.",
        )
        all_pass = False

    # 4. README references docs/DEMO.md
    readme = ROOT / "README.md"
    if readme.exists() and "docs/DEMO.md" in readme.read_text(encoding="utf-8"):
        _ok("README.md references docs/DEMO.md")
    else:
        _fail(
            "README.md does not reference docs/DEMO.md",
            "Add a Demo section to README.md.",
        )
        all_pass = False

    # 5. demo-preview.svg exists
    demo_svg = ROOT / "docs" / "assets" / "demo-preview.svg"
    if demo_svg.exists():
        _ok("docs/assets/demo-preview.svg exists")
    else:
        _fail(
            "docs/assets/demo-preview.svg not found",
            "Create the demo preview SVG.",
        )
        all_pass = False

    # 6. docs/DEMO.md exists
    demo_md = ROOT / "docs" / "DEMO.md"
    if demo_md.exists():
        _ok("docs/DEMO.md exists")
    else:
        _fail("docs/DEMO.md not found", "Create docs/DEMO.md.")
        all_pass = False

    # 7. No uncommitted .env
    dot_env = ROOT / ".env"
    if not dot_env.exists():
        _ok(".env is not committed (good)")
    else:
        _fail(
            ".env file exists in project root",
            "Remove .env from the repository before releasing.",
        )
        all_pass = False

    print()
    print("--- Release Audit Gate ---")

    # 8. Run release_audit.py
    audit_script = ROOT / "scripts" / "release_audit.py"
    if audit_script.exists():
        result = subprocess.run(
            [sys.executable, str(audit_script)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        if result.returncode == 0:
            _ok("release_audit.py passed all checks")
        else:
            _fail(
                "release_audit.py reported failures",
                "Fix the issues reported above, then re-run this script.",
            )
            if result.stdout:
                print()
                print("Audit output:")
                print(result.stdout)
            all_pass = False
    else:
        _fail("scripts/release_audit.py not found")
        all_pass = False

    # ── Summary ──────────────────────────────────────────────────
    print()
    print("=" * 60)
    if all_pass:
        print("  RESULT: PASS -- Ready to release!")
        print()
        if version:
            # Use the actual release notes filename (may have -alpha suffix)
            if matching_notes:
                notes_file = f"docs/releases/{matching_notes[0].name}"
                tag_name = matching_notes[0].stem  # e.g. v0.1.0-alpha
            else:
                tag_name = f"v{version}"
                notes_file = f"docs/releases/{tag_name}.md"
            print("  Suggested release commands (do NOT run automatically):")
            print()
            print(f"    git tag -a {tag_name} -m \"ExplainLens {tag_name}\"")
            print(f"    git push origin {tag_name}")
            print(f"    gh release create {tag_name} \\")
            print(f"      --title \"ExplainLens {tag_name}\" \\")
            print(f"      --notes-file {notes_file}")
        print()
    else:
        print("  RESULT: BLOCKED -- Fix the failing checks before releasing.")
        print()
    print("=" * 60)
    print()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
