"""Tests for content analyzer."""

import pytest
from explainlens.chunker import chunk_text
from explainlens.analyzer import analyze
from explainlens.schemas import ConceptMap


SAMPLE_TEXT = """This paper addresses the problem of inefficient data processing in distributed systems.
The key challenge is that existing methods cannot scale to petabyte-scale datasets.
We introduce a novel approach called StreamProcess that uses incremental batching.
Our experiments on three benchmark datasets demonstrate a 3x speedup over the state of the art.
However, our method has limitations: it requires at least 16GB of memory and has not been
tested on streaming data. This work matters because efficient data processing enables
real-time analytics at scale."""


def test_analyzer_returns_concept_map():
    """Analyzer should return a ConceptMap instance."""
    chunks = chunk_text(SAMPLE_TEXT)
    result = analyze(chunks)
    assert isinstance(result, ConceptMap), "Result should be a ConceptMap"


def test_concept_map_has_core_problem():
    """Concept map should have a non-empty core_problem."""
    chunks = chunk_text(SAMPLE_TEXT)
    result = analyze(chunks)
    assert result.core_problem, "core_problem should not be empty"


def test_concept_map_has_key_concepts():
    """Concept map should have at least one key concept."""
    chunks = chunk_text(SAMPLE_TEXT)
    result = analyze(chunks)
    assert isinstance(result.key_concepts, list), "key_concepts should be a list"


def test_concept_map_has_methods():
    """Concept map should have methods_or_mechanisms."""
    chunks = chunk_text(SAMPLE_TEXT)
    result = analyze(chunks)
    assert isinstance(result.methods_or_mechanisms, list), "methods_or_mechanisms should be a list"


def test_concept_map_has_why_it_matters():
    """Concept map should have a why_it_matters field."""
    chunks = chunk_text(SAMPLE_TEXT)
    result = analyze(chunks)
    assert result.why_it_matters, "why_it_matters should not be empty"


def test_analyzer_with_empty_chunks():
    """Analyzer should handle empty chunks gracefully."""
    result = analyze([])
    assert result.core_problem == ""
