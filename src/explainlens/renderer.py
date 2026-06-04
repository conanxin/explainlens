"""HTML card renderer with SVG placeholders and Jinja2 templates."""

from __future__ import annotations

import re
from typing import List

from jinja2 import Template

from explainlens.schemas import ImageCard, Storyboard, StoryboardPanel


# ── SVG placeholder generators per metaphor type ──────────────────

def _svg_maze() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#f0f4ff" rx="12"/>
  <path d="M40,40 L120,40 L120,80 L80,80 L80,120 L160,120 L160,40 L200,40 L200,160 L240,160
           L240,80 L280,80 L280,200 L320,200 L320,40 L360,40" fill="none" stroke="#5b7fff" stroke-width="4" stroke-linecap="round"/>
  <text x="200" y="230" text-anchor="middle" font-size="17" fill="#3a5ccc" font-family="sans-serif">解法是一条迷宫</text>
</svg>"""


def _svg_magnifier() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#fff7ed" rx="12"/>
  <ellipse cx="180" cy="120" rx="90" ry="70" fill="#fdd49e" opacity="0.6"/>
  <circle cx="180" cy="120" r="60" fill="none" stroke="#f97316" stroke-width="4"/>
  <line x1="225" y1="155" x2="280" y2="200" stroke="#f97316" stroke-width="6" stroke-linecap="round"/>
  <text x="200" y="230" text-anchor="middle" font-size="17" fill="#c2410c" font-family="sans-serif">放大镜定位关键点</text>
</svg>"""


def _svg_split() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#f0fdf4" rx="12"/>
  <rect x="20" y="30" width="160" height="150" fill="#d1d5db" rx="8" opacity="0.5"/>
  <rect x="220" y="30" width="160" height="150" fill="#4ade80" rx="8" opacity="0.4"/>
  <text x="100" y="110" text-anchor="middle" font-size="15" fill="#6b7280" font-family="sans-serif">旧方法</text>
  <text x="300" y="110" text-anchor="middle" font-size="15" fill="#166534" font-family="sans-serif">新方法</text>
  <text x="200" y="215" text-anchor="middle" font-size="15" fill="#15803d" font-family="sans-serif">→ 进步的方向</text>
</svg>"""


def _svg_tree() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#fefce8" rx="12"/>
  <rect x="185" y="80" width="30" height="120" fill="#92400e" rx="4"/>
  <circle cx="140" cy="60" r="40" fill="#22c55e" opacity="0.6"/>
  <circle cx="260" cy="45" r="35" fill="#3b82f6" opacity="0.6"/>
  <circle cx="120" cy="130" r="30" fill="#f59e0b" opacity="0.6"/>
  <circle cx="280" cy="130" r="30" fill="#ef4444" opacity="0.6"/>
  <text x="200" y="230" text-anchor="middle" font-size="17" fill="#854d0e" font-family="sans-serif">知识树：概念如枝干</text>
</svg>"""


def _svg_robot() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#eff6ff" rx="12"/>
  <rect x="60" y="100" width="50" height="60" fill="#60a5fa" rx="8"/>
  <rect x="85" y="80" width="30" height="30" fill="#3b82f6" rx="6"/>
  <circle cx="95" cy="95" r="5" fill="#1e3a5f"/>
  <circle cx="105" cy="95" r="5" fill="#1e3a5f"/>
  <rect x="120" y="110" width="80" height="20" fill="#93c5fd" rx="6"/>
  <rect x="120" y="140" width="80" height="20" fill="#93c5fd" rx="6"/>
  <rect x="120" y="170" width="80" height="20" fill="#93c5fd" rx="6"/>
  <text x="200" y="230" text-anchor="middle" font-size="17" fill="#1e40af" font-family="sans-serif">机器人分步构建</text>
</svg>"""


def _svg_detective() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#faf5ff" rx="12"/>
  <circle cx="100" cy="60" r="25" fill="#c084fc" opacity="0.6"/>
  <line x1="100" y1="85" x2="100" y2="150" stroke="#9333ea" stroke-width="4"/>
  <line x1="100" y1="100" x2="150" y2="120" stroke="#9333ea" stroke-width="3"/>
  <rect x="200" y="50" width="160" height="130" fill="#e9d5ff" rx="6"/>
  <line x1="220" y1="80" x2="340" y2="80" stroke="#9333ea" stroke-width="2"/>
  <line x1="220" y1="110" x2="340" y2="110" stroke="#9333ea" stroke-width="2"/>
  <line x1="220" y1="140" x2="300" y2="140" stroke="#9333ea" stroke-width="2"/>
  <circle cx="260" cy="80" r="5" fill="#7e22ce"/>
  <circle cx="310" cy="110" r="5" fill="#7e22ce"/>
  <text x="200" y="230" text-anchor="middle" font-size="17" fill="#6b21a8" font-family="sans-serif">侦探收集证据板</text>
</svg>"""


def _svg_bridge() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#fef2f2" rx="12"/>
  <path d="M40,180 Q200,60 360,180" fill="none" stroke="#f87171" stroke-width="6"/>
  <line x1="40" y1="160" x2="40" y2="200" stroke="#dc2626" stroke-width="4"/>
  <line x1="360" y1="160" x2="360" y2="200" stroke="#dc2626" stroke-width="4"/>
  <polygon points="180,200 190,215 170,215" fill="#fbbf24"/>
  <text x="170" y="215" font-size="12" fill="#92400e" font-family="sans-serif">⚠</text>
  <text x="200" y="240" text-anchor="middle" font-size="16" fill="#b91c1c" font-family="sans-serif">桥梁与警示：还有gap</text>
</svg>"""


def _svg_lightbulb() -> str:
    return """<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="#fffbeb" rx="12"/>
  <ellipse cx="200" cy="120" rx="50" ry="55" fill="#fde68a" opacity="0.6"/>
  <path d="M160,140 Q200,170 240,140" fill="none" stroke="#f59e0b" stroke-width="4" stroke-linecap="round"/>
  <rect x="185" y="160" width="30" height="15" fill="#d97706" rx="2"/>
  <line x1="190" y1="90" x2="175" y2="55" stroke="#fbbf24" stroke-width="3"/>
  <line x1="210" y1="90" x2="225" y2="55" stroke="#fbbf24" stroke-width="3"/>
  <line x1="200" y1="85" x2="200" y2="45" stroke="#fbbf24" stroke-width="3"/>
  <text x="200" y="210" text-anchor="middle" font-size="17" fill="#b45309" font-family="sans-serif">灵光一现：理解改变了</text>
</svg>"""


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

_CARD_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ExplainLens — 图解卡片预览</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    color: #1a1a2e;
    min-height: 100vh;
  }
  .header {
    text-align: center;
    padding: 48px 24px 32px;
  }
  .header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 8px;
  }
  .header p {
    font-size: 1rem;
    color: #5b6e8c;
  }
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px 48px;
  }
  .card {
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.10);
  }
  .card-number {
    display: inline-block;
    background: #3b82f6;
    color: #fff;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin: 16px 0 4px 20px;
  }
  .card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1e3a5f;
    padding: 4px 20px 8px;
    line-height: 1.4;
  }
  .card-image {
    margin: 0 16px;
    border-radius: 10px;
    overflow: hidden;
    background: #f8fafc;
  }
  .card-image svg {
    width: 100%;
    height: auto;
    display: block;
  }
  .card-body {
    padding: 16px 20px 20px;
  }
  .card-section-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #6b7280;
    margin-bottom: 4px;
  }
  .card-explanation {
    font-size: 0.9rem;
    line-height: 1.6;
    color: #374151;
    margin-bottom: 12px;
  }
  .card-takeaway {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #1e40af;
    margin-bottom: 12px;
  }
  .card-prompt {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    padding: 10px 14px;
    border-radius: 8px;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 12px;
    word-break: break-all;
    line-height: 1.5;
    max-height: 100px;
    overflow-y: auto;
  }
  .card-source {
    font-size: 0.78rem;
    color: #9ca3af;
    line-height: 1.4;
    border-top: 1px solid #f3f4f6;
    padding-top: 10px;
  }
  .card-source strong {
    color: #6b7280;
  }
  .footer {
    text-align: center;
    padding: 32px 24px;
    color: #9ca3af;
    font-size: 0.85rem;
  }
  .footer a {
    color: #3b82f6;
    text-decoration: none;
  }
</style>
</head>
<body>

<div class="header">
  <h1>🔍 ExplainLens 图解卡片</h1>
  <p>复杂内容 → 8 张可视化解释卡</p>
</div>

<div class="card-grid">
{% for card in cards %}
  <div class="card">
    <div class="card-number">卡片 {{ loop.index }} / {{ cards|length }}</div>
    <div class="card-title">{{ card.title }}</div>
    <div class="card-image">
      {{ card.image_placeholder_svg }}
    </div>
    <div class="card-body">
      <div class="card-section-label">简单解释</div>
      <div class="card-explanation">{{ card.explanation }}</div>

      <div class="card-section-label">Takeaway</div>
      <div class="card-takeaway">{{ card.takeaway }}</div>

      <div class="card-section-label">图片 Prompt</div>
      <div class="card-prompt">{{ card.image_prompt }}</div>

      <div class="card-source">
        <strong>来源片段：</strong>{{ card.source_chunk_ids|join(', ') }}<br>
        {{ card.source_excerpt[:200] }}{% if card.source_excerpt|length > 200 %}...{% endif %}
      </div>
    </div>
  </div>
{% endfor %}
</div>

<div class="footer">
  由 <a href="https://github.com/explainlens/explainlens" target="_blank">ExplainLens</a> 生成 &mdash; AI 教学导演
</div>

</body>
</html>""")


def _truncate(text: str, max_len: int = 500) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def create_cards_from_storyboard(storyboard: Storyboard) -> List[ImageCard]:
    """Create ImageCard objects from storyboard panels with SVG placeholders.

    Args:
        storyboard: The complete storyboard with panels.

    Returns:
        List of ImageCard objects.
    """
    cards: List[ImageCard] = []

    for i, panel in enumerate(storyboard.panels):
        # Generate SVG placeholder
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


def render_cards_html(cards: List[ImageCard]) -> str:
    """Render the cards list into a complete, standalone HTML page.

    Args:
        cards: List of ImageCard objects.

    Returns:
        Complete HTML string.
    """
    return _CARD_TEMPLATE.render(cards=cards)
