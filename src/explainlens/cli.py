"""CLI entry point for ExplainLens.

Usage:
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/sample_run --provider rule-based
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/mock_run --provider mock-llm
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/local_fixture_demo --provider local-fixture
    python -m explainlens.cli analyze --input examples/sample_paper.pdf --output outputs/pdf_demo
    python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/debug --provider local-fixture --dump-provider-prompt
    python -m explainlens.cli providers
"""

from __future__ import annotations

import argparse
import json
import os
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

    # 0b. Configure provider with CLI arguments (if supported)
    if hasattr(provider, "endpoint") and args.local_http_endpoint is not None:
        provider.endpoint = args.local_http_endpoint
    if hasattr(provider, "model"):
        if args.provider == "openai":
            provider.model = args.openai_model
        else:
            provider.model = args.local_http_model
    if hasattr(provider, "protocol"):
        provider.protocol = args.local_http_protocol
    if hasattr(provider, "allow_network"):
        provider.allow_network = args.allow_local_http
    if hasattr(provider, "allow_external_api"):
        provider.allow_external_api = args.allow_external_api
    if hasattr(provider, "timeout_seconds"):
        if args.provider == "openai":
            provider.timeout_seconds = args.openai_timeout
        else:
            provider.timeout_seconds = args.local_http_timeout

    # 0c. Fail-closed check for external API providers
    if hasattr(provider, "allow_external_api") and not provider.allow_external_api:
        print(
            f"Provider error: {provider.name} is fail-closed by default.\n"
            f"To enable it, set OPENAI_API_KEY and pass --allow-external-api.\n"
            f"No request was sent.",
            file=sys.stderr,
        )
        return 1

    # 0d. For external API providers, validate API key BEFORE creating output
    if hasattr(provider, "allow_external_api") and provider.allow_external_api:
        # Check if API key is available (without printing it)
        # For openai provider, check OPENAI_API_KEY
        if provider.name == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                print(
                    "Provider error: OPENAI_API_KEY is not set.\n"
                    "No request was sent.",
                    file=sys.stderr,
                )
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

    # 2b. Optional: dump provider prompt pack for debugging
    if getattr(args, "dump_provider_prompt", False):
        _write_provider_prompt_pack(output_dir, chunks, args)

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

    # 8b. Image generation (via image adapter)
    from explainlens.images import (
        get_image_adapter,
        write_image_jobs,
        write_image_manifest,
        get_style,
    )

    skip_images = getattr(args, "skip_images", False)
    image_adapter_name = getattr(args, "image_adapter", "placeholder")
    image_style = getattr(args, "image_style", "clean-cartoon-explainer")
    image_records: list[dict] = []
    img_adapter = None
    img_style_obj = None

    if skip_images:
        print(f"   -> Image generation skipped (--skip-images)")
        write_image_jobs(cards, output_dir, skipped=True)
    else:
        # Validate image style
        try:
            img_style_obj = get_style(image_style)
        except ValueError as e:
            print(f"Image style error: {e}", file=sys.stderr)
            return 1
        try:
            img_adapter = get_image_adapter(image_adapter_name)
            print(f"   -> Image adapter: {img_adapter.name} ({img_adapter.version})")
            print(f"   -> Image style: {img_style_obj.name}")
            write_image_jobs(
                cards, output_dir,
                adapter=img_adapter.name,
                style=image_style,
            )
            image_records = img_adapter.generate_images(
                cards, output_dir, style=image_style,
            )
            print(f"   -> Generated {len(image_records)} images")
            write_image_manifest(
                image_records,
                output_dir,
                adapter=img_adapter.name,
                adapter_version=img_adapter.version,
                style=image_style,
                uses_external_api=img_adapter.uses_external_api,
                requires_api_key=img_adapter.requires_api_key,
            )
        except ValueError as e:
            print(f"Image adapter error: {e}", file=sys.stderr)
            return 1

    # 9. Export Markdown
    cards_md = export_cards_markdown(
        cards,
        chunks=chunks,
        image_adapter=image_adapter_name if not skip_images else None,
        skip_images=skip_images,
    )
    write_text(cards_md, output_dir / "cards.md")

    # 10. Export HTML
    cards_html = render_cards_html(
        cards,
        input_title=input_path.name,
        chunk_count=len(chunks),
        chunks=chunks,
        image_adapter=image_adapter_name if not skip_images else None,
        image_adapter_version=(
            img_adapter.version if img_adapter is not None else None
        ),
        uses_external_image_api=(
            img_adapter.uses_external_api if img_adapter is not None else False
        ),
        provider=provider.name,
        input_type=source_type,
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
        "image_jobs.json",
    ]
    if not skip_images and image_records:
        output_files.append("image_manifest.json")
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
        image_adapter=image_adapter_name if not skip_images else None,
        image_adapter_version=(
            img_adapter.version if img_adapter is not None else None
        ),
        image_count=len(image_records),
        uses_external_image_api=(
            img_adapter.uses_external_api if img_adapter is not None else False
        ),
        image_style=image_style if not skip_images else None,
        image_manifest_path="image_manifest.json" if not skip_images else "",
        warnings=warnings,
        source_quality=source_quality,
    )
    write_json(summary, output_dir / "run_summary.json")

    # Summary
    print()
    print("ExplainLens run complete")
    print(f"  Provider:     {provider.name}")
    print(f"  Image adapter: {image_adapter_name if not skip_images else 'skipped'}")
    print(f"  Input type:   {source_type}")
    if source_type == "pdf":
        print(f"  Pages:        {len(pages)}")
    print(f"  Chunks:       {len(chunks)}")
    print(f"  Cards:        {len(cards)}")
    print(f"  Source index: {output_dir / 'source_index.json'}")
    print(f"  Provider manifest: {output_dir / 'provider_manifest.json'}")
    print(f"  Output:       {output_dir / 'cards.html'}")
    return 0


def _write_provider_prompt_pack(output_dir: Path, chunks: list, args) -> None:
    """Write provider_prompt_pack.json for debugging.

    Only writes if --dump-provider-prompt was set. Never includes
    secrets, API keys, or environment variables.

    Args:
        output_dir: Output directory path.
        chunks: Source chunks from the document.
        args: CLI args namespace (for source type detection).
    """
    from explainlens.providers.prompt_contract import build_prompt_pack

    prompt_pack = build_prompt_pack(
        chunks=chunks,
        desired_card_count=8,
        audience_level="general",
    )
    write_json(prompt_pack.model_dump(), output_dir / "provider_prompt_pack.json")

    # Safety: verify no secrets leaked
    raw = json.dumps(prompt_pack.model_dump())
    if "OPENAI_API_KEY" in raw or "sk-" in raw:
        print("WARNING: provider_prompt_pack.json may contain secrets!", file=sys.stderr)


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

    # Add network block for providers that support it
    if provider.name in ("local-http", "openai"):
        network = {
            "uses_local_http": False,
            "allows_remote_http": False,
            "endpoint": None,
            "protocol": "fixture",
            "timeout_seconds": 30,
        }
        # Try to get network info from provider
        if hasattr(provider, "get_network_manifest"):
            network = provider.get_network_manifest()
        elif hasattr(provider, "endpoint"):
            uses_local = (
                provider.protocol != "fixture" and
                getattr(provider, "allow_network", False)
            )
            network = {
                "uses_local_http": uses_local,
                "allows_remote_http": False,
                "endpoint": provider.endpoint if uses_local else None,
                "protocol": getattr(provider, "protocol", "fixture"),
                "timeout_seconds": getattr(provider, "timeout_seconds", 30),
            }
        manifest["network"] = network

    write_json(manifest, output_dir / "provider_manifest.json")


def cmd_providers(args: argparse.Namespace) -> int:
    """List all known providers (available + disabled)."""
    print("Available providers:\n")
    for info in list_providers():
        name = info["name"]
        ext_api = "yes" if info["uses_external_api"] else "no"
        needs_key = "yes" if _provider_requires_key(name) else "no"
        caps_info = _get_caps(name)
        status = caps_info.status if caps_info else "available"
        print(f"  - {name}")
        print(f"    Status:       {status}")
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


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run offline diagnostics without networking."""
    import sys
    print("ExplainLens Doctor\n")

    # Python version
    import platform
    print(f"Python: {platform.python_version()}")

    # Package import
    try:
        import explainlens
        print(f"Package import: OK (v{explainlens.__version__ if hasattr(explainlens, '__version__') else 'unknown'})")
    except ImportError:
        print("Package import: FAIL")
        return 1

    # Providers
    print("\nProviders:")
    for info in list_providers():
        name = info["name"]
        status = info.get("status", "available")
        print(f"  - {name}: {status}")

    # Disabled providers
    try:
        from explainlens.providers.registry import DISABLED_PROVIDERS
        for name in sorted(DISABLED_PROVIDERS.keys()):
            print(f"  - {name}: disabled")
    except ImportError:
        pass

    # Local HTTP policy
    print("\nLocal HTTP:")
    print("  - Default network access: disabled")
    print("  - Allowed endpoint policy: loopback only")
    print("  - Remote endpoints: rejected")
    print("  - Authorization headers: never sent")
    print("  - Real local model check: skipped by default")

    # OpenAI
    print("\nOpenAI:")
    print("  - Status: experimental")
    print("  - Default access: disabled")
    print("  - Requires: --allow-external-api + OPENAI_API_KEY")
    print("  - CI real API calls: disabled")

    # Artifacts
    print("\nArtifacts:")
    print("  - source_index.json: supported")
    print("  - provider_manifest.json: supported")
    print("  - provider_prompt_pack.json: supported with --dump-provider-prompt")
    print("  - image_jobs.json: supported")
    print("  - image_manifest.json: supported")

    # Image adapters
    print("\nImage adapters:")
    from explainlens.images import list_image_adapters
    for info in list_image_adapters():
        name = info["name"]
        status = info["status"]
        print(f"  - {name}: {status}")

    print("\nImage generation:")
    print("  - Default adapter: placeholder")
    print("  - External image APIs: disabled")
    print("  - Real image generation: not implemented")

    # Image styles
    print("\nImage styles:")
    from explainlens.images import list_styles
    for info in list_styles():
        print(f"  - {info['name']}")

    # Visual exports
    print("\nVisual exports:")
    print("  - HTML cards: supported")
    print("  - Markdown cards: supported")
    print("  - SVG images: supported")
    print("  - External image APIs: disabled")

    print("\nDoctor check complete. No issues found.")
    return 0


def cmd_validate_endpoint(args: argparse.Namespace) -> int:
    """Validate an endpoint for local-http provider (static check, no network)."""
    import sys
    endpoint = args.endpoint

    print(f"Endpoint: {endpoint}")

    # Static validation only - no network calls
    try:
        from explainlens.providers.local_http_transport import is_local_endpoint
        if is_local_endpoint(endpoint):
            print("Allowed: yes")
            print("Reason: loopback endpoint")
            return 0
        else:
            print("Allowed: no")
            print("Reason: only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed for local-http")
            return 1
    except ImportError:
        # Fallback: manual check
        from urllib.parse import urlparse
        try:
            parsed = urlparse(endpoint)
            if parsed.scheme not in ("http", "https"):
                print("Allowed: no")
                print(f"Reason: invalid URL scheme: {parsed.scheme}")
                return 1
            if parsed.scheme == "https":
                print("Allowed: no")
                print("Reason: remote HTTPS endpoints are not allowed for local-http")
                return 1
            hostname = parsed.hostname or ""
            if hostname in ("localhost", "127.0.0.1", "::1"):
                print("Allowed: yes")
                print("Reason: loopback endpoint")
                return 0
            else:
                print("Allowed: no")
                print("Reason: only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed for local-http")
                return 1
        except Exception as e:
            print("Allowed: no")
            print(f"Reason: invalid URL: {e}")
            return 1


def cmd_image_adapters(args: argparse.Namespace) -> int:
    """List all available image adapters."""
    from explainlens.images import list_image_adapters

    print("Available image adapters:\n")
    for info in list_image_adapters():
        name = info["name"]
        ext_api = "yes" if info["uses_external_api"] else "no"
        needs_key = "yes" if info["requires_api_key"] else "no"
        status = info["status"]
        print(f"  - {name}")
        print(f"    Status:       {status}")
        print(f"    External API: {ext_api}")
        print(f"    Requires API key: {needs_key}")
        print()
    return 0


def cmd_image_styles(args: argparse.Namespace) -> int:
    """List all available image style presets."""
    from explainlens.images import list_styles

    print("Available image styles:\n")
    for info in list_styles():
        name = info["name"]
        desc = info["description"]
        print(f"  - {name}")
        print(f"    {desc}")
        print()
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
        choices=["rule-based", "mock-llm", "openai", "local-fixture", "local-http"],
        help="Analysis provider (default: rule-based)",
    )
    analyze_parser.add_argument(
        "--local-http-endpoint",
        default=None,
        help="Local HTTP endpoint (e.g., http://localhost:11434/api/chat)",
    )
    analyze_parser.add_argument(
        "--local-http-model",
        default="local-model",
        help="Model name for local HTTP provider (default: local-model)",
    )
    analyze_parser.add_argument(
        "--local-http-protocol",
        default="fixture",
        choices=["fixture", "ollama-chat", "openai-compatible-chat"],
        help="Protocol for local HTTP provider (default: fixture)",
    )
    analyze_parser.add_argument(
        "--allow-local-http",
        action="store_true",
        default=False,
        help="Allow local HTTP calls (required for non-fixture protocols)",
    )
    analyze_parser.add_argument(
        "--local-http-timeout",
        type=float,
        default=30.0,
        help="Timeout for local HTTP calls in seconds (default: 30.0)",
    )
    analyze_parser.add_argument(
        "--dump-provider-prompt",
        action="store_true",
        default=False,
        help="Dump the provider prompt pack to provider_prompt_pack.json for debugging",
    )
    analyze_parser.add_argument(
        "--allow-external-api",
        action="store_true",
        default=False,
        help="Allow calling external APIs (required for openai provider)",
    )
    analyze_parser.add_argument(
        "--openai-model",
        default="gpt-5.5",
        help="Model name for OpenAI provider (default: gpt-5.5)",
    )
    analyze_parser.add_argument(
        "--openai-timeout",
        type=float,
        default=60.0,
        help="Timeout for OpenAI API calls in seconds (default: 60.0)",
    )
    analyze_parser.add_argument(
        "--image-adapter",
        default="placeholder",
        choices=["placeholder", "fixture"],
        help="Image adapter for card illustrations (default: placeholder)",
    )
    analyze_parser.add_argument(
        "--image-style",
        default="clean-cartoon-explainer",
        help="Visual style for generated images (default: clean-cartoon-explainer)",
    )
    analyze_parser.add_argument(
        "--skip-images",
        action="store_true",
        default=False,
        help="Skip image generation entirely (cards.html falls back to inline SVG)",
    )

    # providers subcommand
    providers_parser = subparsers.add_parser(
        "providers", help="List all known providers and their capabilities"
    )

    # doctor subcommand
    doctor_parser = subparsers.add_parser(
        "doctor", help="Run offline diagnostics (no network calls)"
    )

    # validate-endpoint subcommand
    validate_parser = subparsers.add_parser(
        "validate-endpoint", help="Validate an endpoint for local-http provider (static check, no network)"
    )
    validate_parser.add_argument(
        "endpoint",
        help="Endpoint URL to validate (e.g., http://localhost:11434/api/chat)",
    )

    # image-adapters subcommand
    subparsers.add_parser(
        "image-adapters", help="List all available image adapters"
    )

    # image-styles subcommand
    subparsers.add_parser(
        "image-styles", help="List all available image style presets"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        sys.exit(cmd_analyze(args))
    elif args.command == "providers":
        sys.exit(cmd_providers(args))
    elif args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "validate-endpoint":
        sys.exit(cmd_validate_endpoint(args))
    elif args.command == "image-adapters":
        sys.exit(cmd_image_adapters(args))
    elif args.command == "image-styles":
        sys.exit(cmd_image_styles(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
