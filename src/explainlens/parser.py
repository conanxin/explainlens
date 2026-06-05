"""Document parser — reads .txt, .md, and .pdf files."""

from __future__ import annotations

from pathlib import Path
from typing import List

from explainlens.schemas import SourcePage


class ParseError(Exception):
    """Raised when a file cannot be parsed."""


def detect_source_type(file_path: str | Path) -> str:
    """Detect source type from file extension.

    Returns 'txt', 'md', or 'pdf'.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    elif suffix in (".md", ".markdown"):
        return "md"
    else:
        return "txt"


def parse_text(file_path: str | Path) -> str:
    """Read a plain text or Markdown file and return its full content as a string.

    Args:
        file_path: Path to .txt or .md file.

    Returns:
        Full text content of the file.

    Raises:
        ParseError: If the file cannot be read or is a PDF (use parse_pdf instead).
    """
    path = Path(file_path)

    if not path.exists():
        raise ParseError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raise ParseError(
            f"PDF files must be parsed with parse_pdf(). "
            f"Use parse_pdf('{path.name}') for PDF input."
        )
    if suffix not in (".txt", ".md", ".markdown"):
        print(f"Warning: unknown file extension '{suffix}', attempting to read as text.")

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        for enc in ("latin-1", "cp1252", "gbk"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ParseError(f"Could not decode file: {path}")


def parse_pdf(file_path: str | Path) -> tuple[str, List[SourcePage]]:
    """Extract text from a searchable PDF using PyMuPDF.

    Args:
        file_path: Path to .pdf file.

    Returns:
        Tuple of (full_text, list of SourcePage objects).

    Raises:
        ParseError: If the file is not a PDF, cannot be opened, or contains
                    no extractable text (scanned PDFs are not supported).
    """
    path = Path(file_path)

    if not path.exists():
        raise ParseError(f"File not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ParseError(
            f"Not a PDF file: {path}. Use parse_text() for text files."
        )

    try:
        import fitz
    except ImportError:
        raise ParseError(
            "PyMuPDF (fitz) is required for PDF parsing. "
            "Install with: pip install pymupdf"
        )

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        raise ParseError(f"Cannot open PDF file: {path} — {e}")

    pages: List[SourcePage] = []
    full_text_parts: List[str] = []
    char_offset = 0
    warnings: List[str] = []

    try:
        for page_index in range(doc.page_count):
            page = doc[page_index]
            page_text = page.get_text("text")

            if not page_text.strip():
                warnings.append(f"Page {page_index + 1}: no extractable text")
                pages.append(SourcePage(
                    page_number=page_index + 1,
                    text="",
                    char_start=char_offset,
                    char_end=char_offset,
                ))
                continue

            text_len = len(page_text)
            pages.append(SourcePage(
                page_number=page_index + 1,
                text=page_text,
                char_start=char_offset,
                char_end=char_offset + text_len,
            ))
            full_text_parts.append(page_text)
            char_offset += text_len
    finally:
        doc.close()

    full_text = "\n\n".join(full_text_parts)

    if not full_text.strip():
        raise ParseError(
            "No extractable text found. "
            "Scanned PDFs are not supported in Phase 2."
        )

    if warnings:
        print(f"PDF parsing warnings:")
        for w in warnings:
            print(f"  - {w}")

    return full_text, pages
