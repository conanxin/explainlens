"""Tests for HTML card renderer."""

import pytest
import json
from pathlib import Path
from explainlens.chunker import chunk_text
from explainlens.analyzer import analyze
from explainlens.planner import create_teaching_plan
from explainlens.storyboard import create_storyboard
from explainlens.renderer import create_cards_from_storyboard, render_cards_html
from explainlens.exporters import write_json, write_text


SAMPLE_TEXT = """This paper presents a new approach to climate modeling using graph neural networks.
The problem with current models is their computational cost and limited spatial resolution.
Our method, ClimateGNN, represents the Earth as a graph where nodes are grid points."""


def test_create_cards_produces_eight_cards():
    """Should produce 8 cards from storyboard."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    cards = create_cards_from_storyboard(storyboard)
    assert len(cards) == 8


def test_each_card_has_svg_placeholder():
    """Each card should have an SVG placeholder string."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    cards = create_cards_from_storyboard(storyboard)
    for card in cards:
        assert "<svg" in card.image_placeholder_svg, (
            f"Card {card.card_id} missing SVG placeholder"
        )
        assert "</svg>" in card.image_placeholder_svg


def test_render_html_produces_valid_document():
    """HTML output should be a valid HTML5 document."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    cards = create_cards_from_storyboard(storyboard)
    html = render_cards_html(cards)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "ExplainLens" in html


def test_cards_json_serializable():
    """Cards should be JSON serializable."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    cards = create_cards_from_storyboard(storyboard)
    data = [c.model_dump() for c in cards]
    s = json.dumps(data, ensure_ascii=False)
    parsed = json.loads(s)
    assert len(parsed) == 8


def test_cards_can_be_exported(tmp_path: Path):
    """Cards should be exportable to JSON and HTML files."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    cards = create_cards_from_storyboard(storyboard)

    # Export JSON
    json_path = tmp_path / "cards.json"
    write_json([c.model_dump() for c in cards], json_path)
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        assert len(json.load(f)) == 8

    # Export HTML
    html_path = tmp_path / "cards.html"
    html = render_cards_html(cards)
    write_text(html, html_path)
    assert html_path.exists()
    with open(html_path, encoding="utf-8") as f:
        content = f.read()
        assert "ExplainLens" in content
