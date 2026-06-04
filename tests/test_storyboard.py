"""Tests for storyboard generator."""

import pytest
import json
from explainlens.chunker import chunk_text
from explainlens.analyzer import analyze
from explainlens.planner import create_teaching_plan
from explainlens.storyboard import create_storyboard


SAMPLE_TEXT = """This paper presents a new approach to climate modeling using graph neural networks.
The problem with current models is their computational cost and limited spatial resolution.
Our method, ClimateGNN, represents the Earth as a graph where nodes are grid points
and edges represent atmospheric connections. Experiments on ERA5 data show a 40%
reduction in error compared to physics-based models, while running 10x faster.
A key limitation is that our model requires retraining for each new geographic region.
This work changes how we think about weather prediction by showing that learned
models can outperform traditional physics simulations."""


def test_storyboard_has_eight_panels():
    """Storyboard should produce exactly 8 panels."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    assert len(storyboard.panels) == 8, f"Expected 8 panels, got {len(storyboard.panels)}"


def test_each_panel_has_source_chunk_ids():
    """Each panel must have at least one source_chunk_id."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    for panel in storyboard.panels:
        assert len(panel.source_chunk_ids) > 0, (
            f"Panel {panel.panel_id} has no source_chunk_ids"
        )


def test_each_panel_has_image_prompt():
    """Each panel should have a non-empty image_prompt."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    for panel in storyboard.panels:
        assert panel.image_prompt, f"Panel {panel.panel_id} has empty image_prompt"


def test_panels_have_verification_status():
    """Each panel should have a verification_status."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    for panel in storyboard.panels:
        assert panel.verification_status in ("pending", "reviewed", "revised")


def test_storyboard_json_serializable():
    """Storyboard should be JSON serializable."""
    chunks = chunk_text(SAMPLE_TEXT)
    concept_map = analyze(chunks)
    plan = create_teaching_plan(concept_map, chunks)
    storyboard = create_storyboard(plan, concept_map, chunks)
    d = storyboard.model_dump()
    s = json.dumps(d, ensure_ascii=False)
    assert len(s) > 100, "Serialized storyboard too short"
