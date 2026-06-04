"""Document parser — reads .txt and .md files."""

from __future__ import annotations

from pathlib import Path


class ParseError(Exception):
    """Raised when a file cannot be parsed."""


def parse_text(file_path: str | Path) -> str:
    """Read a plain text or Markdown file and return its full content as a string.

    Args:
        file_path: Path to .txt or .md file.

    Returns:
        Full text content of the file.

    Raises:
        ParseError: If the file cannot be read or has an unsupported extension.
    """
    path = Path(file_path)

    if not path.exists():
        raise ParseError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in (".txt", ".md", ".markdown"):
        if suffix == ".pdf":
            raise ParseError(
                f"PDF parsing is not yet supported. "
                f"Please convert '{path.name}' to .txt first. "
                f"PDF support is planned for Phase 2."
            )
        # For unknown types, attempt to read as text anyway
        print(f"Warning: unknown file extension '{suffix}', attempting to read as text.")

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try common fallback encodings
        for enc in ("latin-1", "cp1252", "gbk"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ParseError(f"Could not decode file: {path}")
