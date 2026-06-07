"""ExplainLens Local Web UI.

A Codex-style three-column dashboard for running analyses,
browsing results, and previewing visual explainer cards.

Usage:
    python -m explainlens.web --host 127.0.0.1 --port 8765

Then open http://127.0.0.1:8765.
"""

from explainlens.web.app import create_app

__all__ = ["create_app"]
