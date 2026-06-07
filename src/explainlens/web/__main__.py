"""Entry point for `python -m explainlens.web`.

Usage:
    python -m explainlens.web --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import argparse
import sys

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ExplainLens Local Web UI",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind (default: 8765)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    print(f"ExplainLens Web UI starting on http://{args.host}:{args.port}")
    print("Local-first Visual Explainer — no external APIs by default")
    print("Press Ctrl+C to stop.\n")

    uvicorn.run(
        "explainlens.web.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
