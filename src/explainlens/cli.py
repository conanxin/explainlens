"""CLI entry point for ExplainLens.

Usage:
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run --provider rule-based
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/mock_run --provider mock-llm
    python -m explainlens.cli analyze --input examples/sample_paper.pdf --output outputs/pdf_demo
    python -m explainlens.cli providers
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
from explainlens.renderer import create_cards_from_storyboard, render_cards_html
from explainlens.exporters import write_json, write_text, export_cards_markdown
from explainlens.schemas import RunSummary, SourcePage
from explainlens.source_index import build_source_index, build_source_quality
from explainlens.providers import get_provider, list_providers, list_provider_capabilities
from explainlens.providers.contract import ProviderCapabilities


# ── CLI Commands ──────────────────────────────────────────────


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the full analysis pipeline."""
    input_path = Path(args.input)
    output_dir = Path(args.output)

    warnings: list[str] = []

    # 0. Validate provider BEFORE any output is created
    try:
        provider = get_provider(args.provider)
    except (ValueError, RuntimeError) as e:
        print(f"Provider error: {e}", file=sys.stderr)
        return 1

    print(f"Reading: {input_path}")
    print(f"Output:  {output_dir}")
    print(f"   -> Provider: {provider.name} ({provider.version})")

    # Ensure output directory (only after provider is validated)
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

    # 3. Analyze — concept map
    concept_map = provider.build_concept_map(chunks)
    print(f"   -> Extracted {len(concept_map.key_concepts)} key concepts, "
          f"{len(concept_map.key_claims)} claims")
    write_json(concept_map, output_dir / "concept_map.json")

    # 5. Teaching plan
    teaching_plan = provider.build_teaching_plan(chunks, concept_map)
    print(f"   -> Created {len(teaching_plan.steps)} teaching steps")
    write_json(teaching_plan, output_dir / "teaching_plan.json")

    # 6. Storyboard
    storyboard = provider.build_storyboard(chunks, concept_map, teaching_plan)
    print(f"   -> Created {len(storyboard.panels)} storyboard panels")
    write_json(storyboard, output_dir / "storyboard.json")

    # 7. Image prompts
    image_prompts = [
        {"panel_id": p.panel_id, "title": p.title, "prompt": p.image_prompt}
        for p in storyboard.panels
    ]
    write_json(image_prompts, output_dir / "image_prompts.json")

    # 8. Cards
    cards = provider.build_cards(storyboard)
    print(f"   -> Created {len(cards)} explainer cards")
    write_json([c.model_dump() for c in cards], output_dir / "cards.json")

    # 9. Export Markdown
    cards_md = export_cards_markdown(cards, chunks=chunks)
    write_text(cards_md, output_dir / "cards.md")

    # 10. Export HTML
    cards_html = render_cards_html(
        cards,
        input_title=input_path.name,
        chunk_count=len(chunks),
        chunks=chunks,
    )
    write_text(cards_html, output_dir / "cards.html")

    # 10b. Source index (cross-references for citation UX)
    source_index = build_source_index(
        chunks=chunks,
        cards=cards,
        pages=pages if source_type == "pdf" else None,
        source_file=str(input_path.resolve()),
        input_type=source_type,
    )
    write_json(source_index, output_dir / "source_index.json")

    # 10c. Provider manifest
    _write_provider_manifest(
        output_dir=output_dir,
        provider=provider,
    )

    # 11. Run summary
    output_files = [
        "source_chunks.json",
        "source_index.json",
        "concept_map.json",
        "teaching_plan.json",
        "storyboard.json",
        "image_prompts.json",
        "cards.json",
        "cards.md",
        "cards.html",
        "provider_manifest.json",
    ]
    if source_type == "pdf":
        output_files.insert(0, "source_pages.json")

    # Track warnings
    source_quality = build_source_quality(chunks, pages if source_type == "pdf" else None)
    if source_quality.get("empty_pages"):
        warnings.append(f"Empty pages: {source_quality['empty_pages']}")

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
        provider=provider.name,
        provider_version=provider.version,
        uses_external_api=provider.uses_external_api,
        warnings=warnings,
        source_quality=source_quality,
    )
    write_json(summary, output_dir / "run_summary.json")

    # Summary
    print()
    print("ExplainLens run complete")
    print(f"  Provider:     {provider.name}")
    print(f"  Input type:   {source_type}")
    if source_type == "pdf":
        print(f"  Pages:        {len(pages)}")
    print(f"  Chunks:       {len(chunks)}")
    print(f"  Cards:        {len(cards)}")
    print(f"  Source index: {output_dir / 'source_index.json'}")
    print(f"  Provider manifest: {output_dir / 'provider_manifest.json'}")
    print(f"  Output:       {output_dir / 'cards.html'}")
    return 0


def _write_provider_manifest(output_dir: Path, provider) -> None:
    """Write provider_manifest.json for the current run.

    Args:
        output_dir: Output directory path.
        provider: The active provider instance.
    """
    caps = None
    try:
        from explainlens.providers.registry import get_provider_capabilities
        caps = get_provider_capabilities(provider.name)
    except Exception:
        pass

    if caps is None:
        # Fallback: build a basic manifest from provider attributes
        caps = ProviderCapabilities(
            name=provider.name,
            version=provider.version,
            status="available",
            uses_external_api=provider.uses_external_api,
            requires_api_key=False,
            supports_pdf=True,
            supports_text=True,
            preserves_source_chunk_ids=True,
            description=f"{provider.name} provider",
        )

    manifest = {
        "provider": caps.name,
        "provider_version": caps.version,
        "provider_status": caps.status,
        "uses_external_api": caps.uses_external_api,
        "requires_api_key": caps.requires_api_key,
        "capabilities": {
            "supports_pdf": caps.supports_pdf,
            "supports_text": caps.supports_text,
            "preserves_source_chunk_ids": caps.preserves_source_chunk_ids,
        },
        "safety": caps.safety_manifest(),
    }
    write_json(manifest, output_dir / "provider_manifest.json")


def cmd_providers(args: argparse.Namespace) -> int:
    """List all known providers (available + disabled)."""
    print("Available providers:\n")
    for info in list_providers():
        name = info["name"]
        version = info["version"]
        ext_api = "yes" if info["uses_external_api"] else "no"
        needs_key = "yes" if _provider_requires_key(name) else "no"
        print(f"  - {name}")
        print(f"    Status:       available")
        print(f"    External API: {ext_api}")
        print(f"    Requires API key: {needs_key}")
        print()

    # Disabled providers
    try:
        from explainlens.providers.registry import DISABLED_PROVIDERS
        if DISABLED_PROVIDERS:
            print("Disabled providers:\n")
            for name in sorted(DISABLED_PROVIDERS.keys()):
                caps = _get_caps(name)
                ext_api = "yes" if caps and caps.uses_external_api else "no"
                needs_key = "yes" if caps and caps.requires_api_key else "no"
                print(f"  - {name}")
                print(f"    Status:       disabled")
                print(f"    External API: {ext_api}")
                print(f"    Requires API key: {needs_key}")
                print()
    except ImportError:
        pass

    return 0


def _provider_requires_key(name: str) -> bool:
    caps = _get_caps(name)
    return caps.requires_api_key if caps else False


def _get_caps(name: str) -> ProviderCapabilities | None:
    try:
        from explainlens.providers.registry import get_provider_capabilities
        return get_provider_capabilities(name)
    except Exception:
        return None


# ── CLI Entry Point ───────────────────────────────────────────


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="explainlens",
        description="ExplainLens — Turn papers and complex texts into visual explainer cards.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a document and generate explainer cards"
    )
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
    analyze_parser.add_argument(
        "--provider", "-p",
        default="rule-based",
        choices=["rule-based", "mock-llm", "openai"],
        help="Analysis provider (default: rule-based)",
    )

    # providers subcommand
    providers_parser = subparsers.add_parser(
        "providers", help="List all known providers and their capabilities"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        sys.exit(cmd_analyze(args))
    elif args.command == "providers":
        sys.exit(cmd_providers(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
