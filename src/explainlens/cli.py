"""CLI entry point for ExplainLens.

Usage:
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from datetime import datetime

# On Windows the default stdout/stderr encoding may be GBK/cp936 which
# cannot represent emoji.  Reconfigure to UTF-8 when possible (Python 3.7+).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from explainlens.parser import parse_text, ParseError
from explainlens.chunker import chunk_text
from explainlens.analyzer import analyze
from explainlens.planner import create_teaching_plan
from explainlens.storyboard import create_storyboard
from explainlens.renderer import create_cards_from_storyboard, render_cards_html
from explainlens.exporters import write_json, write_text, export_cards_markdown
from explainlens.schemas import RunSummary


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the full analysis pipeline."""
    input_path = Path(args.input)
    output_dir = Path(args.output)

    warnings: list[str] = []
    print(f"📖 Reading: {input_path}")
    print(f"📁 Output:  {output_dir}")

    # Ensure output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse
    try:
        text = parse_text(input_path)
    except ParseError as e:
        print(f"❌ Parse error: {e}", file=sys.stderr)
        return 1

    print(f"   → Parsed {len(text)} characters")

    # 2. Chunk
    chunks = chunk_text(text)
    if not chunks:
        print("❌ No content found in input file.", file=sys.stderr)
        return 1
    print(f"   → Created {len(chunks)} chunks")
    write_json([c.model_dump() for c in chunks], output_dir / "source_chunks.json")

    # 3. Analyze
    concept_map = analyze(chunks)
    print(f"   → Extracted {len(concept_map.key_concepts)} key concepts, "
          f"{len(concept_map.key_claims)} claims")
    write_json(concept_map, output_dir / "concept_map.json")

    # 4. Teaching plan
    teaching_plan = create_teaching_plan(concept_map, chunks)
    print(f"   → Created {len(teaching_plan.steps)} teaching steps")
    write_json(teaching_plan, output_dir / "teaching_plan.json")

    # 5. Storyboard
    storyboard = create_storyboard(teaching_plan, concept_map, chunks)
    print(f"   → Created {len(storyboard.panels)} storyboard panels")
    write_json(storyboard, output_dir / "storyboard.json")

    # 6. Image prompts
    image_prompts = [
        {"panel_id": p.panel_id, "title": p.title, "prompt": p.image_prompt}
        for p in storyboard.panels
    ]
    write_json(image_prompts, output_dir / "image_prompts.json")

    # 7. Cards
    cards = create_cards_from_storyboard(storyboard)
    print(f"   → Created {len(cards)} explainer cards")
    write_json([c.model_dump() for c in cards], output_dir / "cards.json")

    # 8. Export Markdown
    cards_md = export_cards_markdown(cards)
    write_text(cards_md, output_dir / "cards.md")

    # 9. Export HTML
    cards_html = render_cards_html(
        cards,
        input_title=input_path.name,
        chunk_count=len(chunks),
    )
    write_text(cards_html, output_dir / "cards.html")

    # 10. Run summary
    summary = RunSummary(
        input_file=str(input_path.resolve()),
        output_dir=str(output_dir.resolve()),
        chunk_count=len(chunks),
        concept_count=len(concept_map.key_concepts),
        step_count=len(teaching_plan.steps),
        panel_count=len(storyboard.panels),
        card_count=len(cards),
        output_files=[
            "source_chunks.json",
            "concept_map.json",
            "teaching_plan.json",
            "storyboard.json",
            "image_prompts.json",
            "cards.json",
            "cards.md",
            "cards.html",
        ],
        warnings=warnings,
    )
    write_json(summary, output_dir / "run_summary.json")

    print(f"\n✅ Done! Output files in: {output_dir}")
    print(f"   Open {output_dir / 'cards.html'} in a browser to preview.")

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
        help="Path to input file (.txt or .md)",
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
