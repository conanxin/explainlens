"""CLI entry point for ExplainLens.

Usage:
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run
    python -m explainlens.cli analyze --input examples/sample_paper.pdf --output outputs/pdf_demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# On Windows the default stdout/stderr encoding may be GBK/cp936 which
# cannot represent emoji.  Reconfigure to UTF-8 when possible (Python 3.7+).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from explainlens.parser import parse_text, parse_pdf, detect_source_type, ParseError
from explainlens.chunker import chunk_text
from explainlens.analyzer import analyze
from explainlens.planner import create_teaching_plan
from explainlens.storyboard import create_storyboard
from explainlens.renderer import create_cards_from_storyboard, render_cards_html
from explainlens.exporters import write_json, write_text, export_cards_markdown
from explainlens.schemas import RunSummary, SourcePage


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the full analysis pipeline."""
    input_path = Path(args.input)
    output_dir = Path(args.output)

    warnings: list[str] = []
    print(f"Reading: {input_path}")
    print(f"Output:  {output_dir}")

    # Ensure output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect source type
    source_type = detect_source_type(input_path)

    # 1. Parse
    pages: list[SourcePage] = []
    try:
        if source_type == "pdf":
            text, pages = parse_pdf(input_path)
            print(f"   -> Parsed {len(pages)} pages, {len(text)} characters")
        else:
            text = parse_text(input_path)
            print(f"   -> Parsed {len(text)} characters")
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 1

    # Output source_pages.json for PDF
    if source_type == "pdf" and pages:
        write_json([p.model_dump() for p in pages], output_dir / "source_pages.json")

    # 2. Chunk
    if source_type == "pdf":
        chunks = chunk_text(text, source_type="pdf", pages=pages)
    else:
        chunks = chunk_text(text, source_type=source_type)
    if not chunks:
        print("No content found in input file.", file=sys.stderr)
        return 1
    print(f"   -> Created {len(chunks)} chunks")
    write_json([c.model_dump() for c in chunks], output_dir / "source_chunks.json")

    # 3. Analyze
    concept_map = analyze(chunks)
    print(f"   -> Extracted {len(concept_map.key_concepts)} key concepts, "
          f"{len(concept_map.key_claims)} claims")
    write_json(concept_map, output_dir / "concept_map.json")

    # 4. Teaching plan
    teaching_plan = create_teaching_plan(concept_map, chunks)
    print(f"   -> Created {len(teaching_plan.steps)} teaching steps")
    write_json(teaching_plan, output_dir / "teaching_plan.json")

    # 5. Storyboard
    storyboard = create_storyboard(teaching_plan, concept_map, chunks)
    print(f"   -> Created {len(storyboard.panels)} storyboard panels")
    write_json(storyboard, output_dir / "storyboard.json")

    # 6. Image prompts
    image_prompts = [
        {"panel_id": p.panel_id, "title": p.title, "prompt": p.image_prompt}
        for p in storyboard.panels
    ]
    write_json(image_prompts, output_dir / "image_prompts.json")

    # 7. Cards
    cards = create_cards_from_storyboard(storyboard)
    print(f"   -> Created {len(cards)} explainer cards")
    write_json([c.model_dump() for c in cards], output_dir / "cards.json")

    # 8. Export Markdown
    cards_md = export_cards_markdown(cards, chunks=chunks)
    write_text(cards_md, output_dir / "cards.md")

    # 9. Export HTML
    cards_html = render_cards_html(
        cards,
        input_title=input_path.name,
        chunk_count=len(chunks),
        chunks=chunks,
    )
    write_text(cards_html, output_dir / "cards.html")

    # 10. Run summary
    output_files = [
        "source_chunks.json",
        "concept_map.json",
        "teaching_plan.json",
        "storyboard.json",
        "image_prompts.json",
        "cards.json",
        "cards.md",
        "cards.html",
    ]
    if source_type == "pdf":
        output_files.insert(0, "source_pages.json")

    summary = RunSummary(
        input_file=str(input_path.resolve()),
        output_dir=str(output_dir.resolve()),
        input_type=source_type,
        chunk_count=len(chunks),
        page_count=len(pages) if source_type == "pdf" else None,
        concept_count=len(concept_map.key_concepts),
        step_count=len(teaching_plan.steps),
        panel_count=len(storyboard.panels),
        card_count=len(cards),
        output_files=output_files,
        extraction_method="pymupdf" if source_type == "pdf" else "built-in",
        warnings=warnings,
    )
    write_json(summary, output_dir / "run_summary.json")

    # Summary
    print()
    print("ExplainLens run complete")
    print(f"  Input type: {source_type}")
    if source_type == "pdf":
        print(f"  Pages:      {len(pages)}")
    print(f"  Chunks:     {len(chunks)}")
    print(f"  Cards:      {len(cards)}")
    print(f"  Output:     {output_dir / 'cards.html'}")

    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="explainlens",
        description="ExplainLens — Turn papers and complex texts into visual explainer cards.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a document and generate explainer cards")
    analyze_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input file (.txt, .md, or .pdf)",
    )
    analyze_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory path",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        sys.exit(cmd_analyze(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
