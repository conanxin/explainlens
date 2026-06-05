"""HTML card renderer with SVG placeholders and Jinja2 templates."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from jinja2 import Template

from explainlens.schemas import ImageCard, Storyboard, StoryboardPanel


# ── SVG placeholder generators per metaphor type ──────────────────

def _svg_maze() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#eef2ff" rx="12"/>'
        '<path d="M40,40 L120,40 L120,80 L80,80 L80,130 L160,130 L160,40 '
        'L200,40 L200,160 L240,160 L240,80 L280,80 L280,200 L320,200 L320,40 L360,40" '
        'fill="none" stroke="#4f6ef7" stroke-width="4" stroke-linecap="round"/>'
        '<circle cx="55" cy="40" r="8" fill="#4f6ef7" opacity="0.7"/>'
        '<circle cx="345" cy="200" r="8" fill="#22c55e" opacity="0.8"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#3730a3" '
        'font-family="system-ui,sans-serif" font-weight="600">Complex path → one solution</text>'
        '</svg>'
    )


def _svg_magnifier() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#fff7ed" rx="12"/>'
        '<ellipse cx="180" cy="118" rx="80" ry="62" fill="#fed7aa" opacity="0.5"/>'
        '<circle cx="180" cy="118" r="55" fill="none" stroke="#f97316" stroke-width="5"/>'
        '<line x1="223" y1="153" x2="280" y2="204" stroke="#f97316" stroke-width="7" '
        'stroke-linecap="round"/>'
        '<text x="180" y="122" text-anchor="middle" font-size="30" fill="#ea580c" '
        'font-family="system-ui,sans-serif">?</text>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#9a3412" '
        'font-family="system-ui,sans-serif" font-weight="600">Zoom in on what matters</text>'
        '</svg>'
    )


def _svg_split() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#f0fdf4" rx="12"/>'
        '<rect x="20" y="40" width="155" height="140" fill="#d1d5db" rx="10" opacity="0.6"/>'
        '<rect x="225" y="40" width="155" height="140" fill="#4ade80" rx="10" opacity="0.5"/>'
        '<text x="97" y="115" text-anchor="middle" font-size="14" fill="#6b7280" '
        'font-family="system-ui,sans-serif">Old approach</text>'
        '<text x="302" y="115" text-anchor="middle" font-size="14" fill="#166534" '
        'font-family="system-ui,sans-serif">New approach</text>'
        '<path d="M175,110 L200,95 L225,110 M200,95 L200,130" fill="none" '
        'stroke="#16a34a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        '<text x="200" y="218" text-anchor="middle" font-size="14" fill="#15803d" '
        'font-family="system-ui,sans-serif" font-weight="600">Before vs. after</text>'
        '</svg>'
    )


def _svg_tree() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#fefce8" rx="12"/>'
        '<rect x="188" y="90" width="24" height="120" fill="#92400e" rx="4"/>'
        '<circle cx="200" cy="72" r="45" fill="#22c55e" opacity="0.55"/>'
        '<circle cx="145" cy="68" r="30" fill="#3b82f6" opacity="0.5"/>'
        '<circle cx="255" cy="68" r="30" fill="#f59e0b" opacity="0.5"/>'
        '<circle cx="130" cy="125" r="22" fill="#ef4444" opacity="0.45"/>'
        '<circle cx="272" cy="125" r="22" fill="#a855f7" opacity="0.45"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#854d0e" '
        'font-family="system-ui,sans-serif" font-weight="600">Concepts branch like a tree</text>'
        '</svg>'
    )


def _svg_robot() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#eff6ff" rx="12"/>'
        '<rect x="60" y="100" width="80" height="90" fill="#60a5fa" rx="10"/>'
        '<rect x="80" y="72" width="40" height="36" fill="#3b82f6" rx="8"/>'
        '<circle cx="92" cy="90" r="6" fill="#1e3a8a"/>'
        '<circle cx="108" cy="90" r="6" fill="#1e3a8a"/>'
        '<rect x="150" y="100" width="140" height="24" fill="#bfdbfe" rx="6"/>'
        '<rect x="150" y="134" width="140" height="24" fill="#93c5fd" rx="6"/>'
        '<rect x="150" y="168" width="100" height="24" fill="#60a5fa" rx="6"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#1e40af" '
        'font-family="system-ui,sans-serif" font-weight="600">Step-by-step mechanism</text>'
        '</svg>'
    )


def _svg_detective() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#faf5ff" rx="12"/>'
        '<circle cx="100" cy="68" r="28" fill="#c084fc" opacity="0.7"/>'
        '<line x1="100" y1="96" x2="100" y2="165" stroke="#9333ea" stroke-width="5"/>'
        '<line x1="100" y1="115" x2="148" y2="130" stroke="#9333ea" stroke-width="4"/>'
        '<line x1="100" y1="115" x2="52" y2="130" stroke="#9333ea" stroke-width="4"/>'
        '<rect x="200" y="44" width="170" height="150" fill="#ede9fe" rx="8"/>'
        '<circle cx="220" cy="82" r="6" fill="#7c3aed"/>'
        '<circle cx="248" cy="82" r="6" fill="#7c3aed"/>'
        '<circle cx="276" cy="82" r="6" fill="#a78bfa"/>'
        '<line x1="215" y1="110" x2="355" y2="110" stroke="#9333ea" stroke-width="2"/>'
        '<line x1="215" y1="135" x2="355" y2="135" stroke="#9333ea" stroke-width="2"/>'
        '<line x1="215" y1="160" x2="310" y2="160" stroke="#9333ea" stroke-width="2"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#6b21a8" '
        'font-family="system-ui,sans-serif" font-weight="600">Evidence board</text>'
        '</svg>'
    )


def _svg_bridge() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#fff1f2" rx="12"/>'
        '<rect x="0" y="185" width="400" height="65" fill="#fecdd3" rx="0"/>'
        '<rect x="0" y="185" width="400" height="4" fill="#fca5a5"/>'
        '<path d="M40,185 Q200,70 360,185" fill="none" stroke="#f43f5e" stroke-width="7"/>'
        '<line x1="40" y1="160" x2="40" y2="185" stroke="#e11d48" stroke-width="5"/>'
        '<line x1="360" y1="160" x2="360" y2="185" stroke="#e11d48" stroke-width="5"/>'
        '<path d="M120,185 L120,145 M200,185 L200,120 M280,185 L280,145" '
        'stroke="#fb7185" stroke-width="3" stroke-dasharray="4,3"/>'
        '<text x="200" y="235" text-anchor="middle" font-size="14" fill="#9f1239" '
        'font-family="system-ui,sans-serif" font-weight="600">Bridge the gap</text>'
        '</svg>'
    )


def _svg_lightbulb() -> str:
    return (
        '<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="400" height="250" fill="#fffbeb" rx="12"/>'
        '<ellipse cx="200" cy="118" rx="55" ry="60" fill="#fde68a" opacity="0.6"/>'
        '<path d="M164,138 Q200,172 236,138" fill="none" stroke="#f59e0b" stroke-width="5" '
        'stroke-linecap="round"/>'
        '<rect x="184" y="160" width="32" height="16" fill="#d97706" rx="3"/>'
        '<line x1="192" y1="92" x2="175" y2="52" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="208" y1="92" x2="225" y2="52" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="200" y1="88" x2="200" y2="44" stroke="#fbbf24" stroke-width="3.5"/>'
        '<line x1="152" y1="105" x2="110" y2="92" stroke="#fcd34d" stroke-width="2.5"/>'
        '<line x1="248" y1="105" x2="290" y2="92" stroke="#fcd34d" stroke-width="2.5"/>'
        '<text x="200" y="215" text-anchor="middle" font-size="14" fill="#92400e" '
        'font-family="system-ui,sans-serif" font-weight="600">Insight changes the picture</text>'
        '</svg>'
    )


_SVG_GENERATORS = [
    _svg_maze,
    _svg_magnifier,
    _svg_split,
    _svg_tree,
    _svg_robot,
    _svg_detective,
    _svg_bridge,
    _svg_lightbulb,
]


# ── HTML Template (Jinja2) ───────────────────────────────────────

_CARD_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ExplainLens — Visual Explainer Cards</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --blue-50:  #eff6ff;
    --blue-100: #dbeafe;
    --blue-500: #3b82f6;
    --blue-700: #1d4ed8;
    --blue-900: #1e3a8a;
    --slate-50:  #f8fafc;
    --slate-100: #f1f5f9;
    --slate-200: #e2e8f0;
    --slate-500: #64748b;
    --slate-700: #334155;
    --slate-900: #0f172a;
    --green-50:  #f0fdf4;
    --green-600: #16a34a;
    --radius-lg: 16px;
    --radius-md: 10px;
    --radius-sm: 6px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md: 0 4px 16px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.04);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.10);
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    background: #f4f7fb;
    color: var(--slate-700);
    line-height: 1.6;
    min-height: 100vh;
  }

  /* ── Hero ── */
  .hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #38bdf8 100%);
    color: #fff;
    text-align: center;
    padding: 56px 24px 44px;
  }
  .hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: #bfdbfe;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.25);
  }
  .hero h1 {
    font-size: clamp(1.8rem, 4vw, 2.6rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 12px;
  }
  .hero h1 span { color: #bae6fd; }
  .hero-sub {
    font-size: 1.05rem;
    color: #bfdbfe;
    max-width: 560px;
    margin: 0 auto 24px;
  }
  .hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  .pill {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.22);
    color: #dbeafe;
    font-size: 0.78rem;
    padding: 4px 12px;
    border-radius: 20px;
  }

  /* ── Summary ── */
  .summary-wrap {
    max-width: 860px;
    margin: 32px auto 0;
    padding: 0 24px;
  }
  .summary {
    background: #fff;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 24px 28px;
    display: flex;
    flex-wrap: wrap;
    gap: 20px 40px;
    align-items: flex-start;
  }
  .summary-item { min-width: 120px; }
  .summary-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--slate-500);
    margin-bottom: 4px;
  }
  .summary-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--slate-900);
  }
  .summary-value.accent { color: var(--blue-700); }

  /* ── Cards grid ── */
  .section-title {
    max-width: 1280px;
    margin: 40px auto 0;
    padding: 0 24px;
    font-size: 1rem;
    font-weight: 700;
    color: var(--slate-500);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 24px;
    max-width: 1280px;
    margin: 16px auto 0;
    padding: 0 24px 48px;
  }

  /* ── Card ── */
  .card {
    background: #fff;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
  }
  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 20px 10px;
  }
  .card-num {
    background: var(--blue-500);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .card-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--slate-900);
    line-height: 1.35;
  }
  .card-image {
    margin: 0 16px 0;
    border-radius: var(--radius-md);
    overflow: hidden;
    background: var(--slate-50);
    border: 1px solid var(--slate-200);
  }
  .card-image svg {
    width: 100%;
    height: auto;
    display: block;
  }
  .card-body {
    padding: 14px 20px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex: 1;
  }
  .label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--slate-500);
    margin-bottom: 3px;
  }
  .explanation {
    font-size: 0.88rem;
    line-height: 1.65;
    color: var(--slate-700);
  }
  .takeaway {
    background: var(--blue-50);
    border-left: 4px solid var(--blue-500);
    padding: 10px 14px;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    font-size: 0.85rem;
    color: var(--blue-900);
    line-height: 1.5;
  }

  /* collapsible sections */
  details {
    border: 1px solid var(--slate-200);
    border-radius: var(--radius-sm);
    overflow: hidden;
  }
  details summary {
    cursor: pointer;
    padding: 8px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--slate-500);
    background: var(--slate-50);
    list-style: none;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  details summary::before {
    content: "▶";
    font-size: 0.6rem;
    transition: transform 0.15s;
  }
  details[open] summary::before { transform: rotate(90deg); }
  details .detail-body {
    padding: 10px 12px;
    font-size: 0.8rem;
    color: var(--slate-700);
    line-height: 1.55;
    background: #fff;
  }
  details .detail-body.mono {
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    word-break: break-all;
    color: var(--slate-500);
    white-space: pre-wrap;
  }

  /* ── Footer ── */
  .footer {
    text-align: center;
    padding: 40px 24px 32px;
    border-top: 1px solid var(--slate-200);
    margin-top: 24px;
    font-size: 0.83rem;
    color: var(--slate-500);
  }
  .footer a { color: var(--blue-500); text-decoration: none; }
  .footer a:hover { text-decoration: underline; }
  .safety-note {
    display: inline-block;
    background: var(--green-50);
    border: 1px solid #86efac;
    color: var(--green-600);
    font-size: 0.78rem;
    padding: 6px 14px;
    border-radius: 20px;
    margin-bottom: 10px;
  }
</style>
</head>
<body>

<!-- Hero -->
<section class="hero">
  <div class="hero-badge">ExplainLens</div>
  <h1>Visual <span>Explainer</span> Cards</h1>
  <p class="hero-sub">Turn complex content into visual explainer cards and cartoon storyboards.</p>
  <div class="hero-pills">
    <span class="pill">Local MVP</span>
    <span class="pill">No external AI API</span>
    <span class="pill">SVG placeholder</span>
    <span class="pill">v0.1.0-alpha</span>
  </div>
</section>

<!-- Run Summary -->
<div class="summary-wrap">
  <div class="summary">
    <div class="summary-item">
      <div class="summary-label">Input</div>
      <div class="summary-value">{{ meta.input_title }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-label">Cards</div>
      <div class="summary-value accent">{{ cards|length }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-label">Source Chunks</div>
      <div class="summary-value accent">{{ meta.chunk_count }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-label">Generated</div>
      <div class="summary-value">{{ meta.generated_at }}</div>
    </div>
    <div class="summary-item">
      <div class="summary-label">Version</div>
      <div class="summary-value">v0.1.0-alpha</div>
    </div>
  </div>
</div>

<div class="section-title">Explainer Cards</div>

<!-- Cards -->
<div class="card-grid">
{% for card in cards %}
  <div class="card">
    <div class="card-header">
      <span class="card-num">{{ loop.index }} / {{ cards|length }}</span>
      <div class="card-title">{{ card.title }}</div>
    </div>
    <div class="card-image">{{ card.image_placeholder_svg }}</div>
    <div class="card-body">

      <div>
        <div class="label">Explanation</div>
        <div class="explanation">{{ card.explanation }}</div>
      </div>

      <div>
        <div class="label">Takeaway</div>
        <div class="takeaway">{{ card.takeaway }}</div>
      </div>

      <details>
        <summary>Image Prompt</summary>
        <div class="detail-body mono">{{ card.image_prompt }}</div>
      </details>

      <details>
        <summary>Source Excerpt &mdash; {{ card.source_chunk_ids | join(', ') }}</summary>
        <div class="detail-body">{{ card.source_excerpt[:300] }}{% if card.source_excerpt|length > 300 %}&hellip;{% endif %}</div>
      </details>

    </div>
  </div>
{% endfor %}
</div>

<!-- Footer -->
<footer class="footer">
  <div>
    <span class="safety-note">This local MVP does not call external APIs.</span>
  </div>
  <p>Generated by <a href="https://github.com/conanxin/explainlens" target="_blank">ExplainLens</a> v0.1.0-alpha &mdash; AI Teaching Director</p>
</footer>

</body>
</html>""")


def _truncate(text: str, max_len: int = 500) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def create_cards_from_storyboard(storyboard: Storyboard) -> List[ImageCard]:
    """Create ImageCard objects from storyboard panels with SVG placeholders.

    Args:
        storyboard: The complete storyboard with panels.

    Returns:
        List of ImageCard objects.
    """
    cards: List[ImageCard] = []

    for i, panel in enumerate(storyboard.panels):
        svg = _SVG_GENERATORS[i % len(_SVG_GENERATORS)]()

        card = ImageCard(
            card_id=f"card_{i + 1:02d}",
            title=panel.title,
            explanation=panel.plain_explanation,
            image_placeholder_svg=svg,
            image_prompt=panel.image_prompt,
            takeaway=panel.takeaway,
            source_chunk_ids=panel.source_chunk_ids,
            source_excerpt=_truncate(panel.plain_explanation),
            review_status="pending",
        )
        cards.append(card)

    return cards


def render_cards_html(
    cards: List[ImageCard],
    input_title: str = "Unknown",
    chunk_count: int = 0,
) -> str:
    """Render the cards list into a complete, standalone HTML page.

    Args:
        cards: List of ImageCard objects.
        input_title: Title or filename of the input document.
        chunk_count: Number of source chunks processed.

    Returns:
        Complete HTML string.
    """
    meta = {
        "input_title": input_title,
        "chunk_count": chunk_count,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return _CARD_TEMPLATE.render(cards=cards, meta=meta)
