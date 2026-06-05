"""Data models for ExplainLens using Pydantic."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Source Chunks ────────────────────────────────────────────────

class SourceChunk(BaseModel):
    """A chunk of the source document."""
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. 'chunk_001'")
    text: str = Field(..., description="The chunk text content")
    start_char: int = Field(..., description="Character offset start in original document")
    end_char: int = Field(..., description="Character offset end in original document")
    approx_page: Optional[int] = Field(default=None, description="Approximate page number, if known")
    page_start: Optional[int] = Field(default=None, description="First page this chunk spans (PDF)")
    page_end: Optional[int] = Field(default=None, description="Last page this chunk spans (PDF)")
    section_title: Optional[str] = Field(default=None, description="Nearest section heading, if detected")
    source_type: str = Field(default="txt", description="Source type: txt, md, or pdf")


# ── Source Pages ─────────────────────────────────────────────────

class SourcePage(BaseModel):
    """A single page extracted from a PDF document."""
    page_number: int = Field(..., description="1-based page number")
    text: str = Field(..., description="Extracted text from this page")
    char_start: int = Field(default=0, description="Character offset start in full document text")
    char_end: int = Field(default=0, description="Character offset end in full document text")


# ── Concept Map ──────────────────────────────────────────────────

class ConceptMap(BaseModel):
    """Structured extraction of key ideas from the source."""
    core_problem: str = Field(default="", description="The main problem the content addresses")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts introduced")
    key_claims: List[str] = Field(default_factory=list, description="Core claims or thesis statements")
    methods_or_mechanisms: List[str] = Field(default_factory=list, description="Methods, algorithms, or mechanisms")
    evidence_or_examples: List[str] = Field(default_factory=list, description="Evidence, data, or examples cited")
    limitations: List[str] = Field(default_factory=list, description="Limitations, caveats, or open questions")
    why_it_matters: str = Field(default="", description="Why this content is significant")


# ── Teaching Plan ────────────────────────────────────────────────

class TeachingStep(BaseModel):
    """A single step in the teaching / explanation path."""
    step_id: str = Field(..., description="Step identifier, e.g. 'step_01'")
    title: str = Field(..., description="Step title")
    teaching_goal: str = Field(..., description="What this step aims to teach")
    source_chunk_ids: List[str] = Field(default_factory=list, description="Referenced source chunks")
    simple_explanation: str = Field(default="", description="Plain-language explanation")
    visual_metaphor: str = Field(default="", description="Visual metaphor for this concept")
    audience_level: str = Field(default="general", description="Target audience level")
    risk_note: str = Field(default="", description="Potential misunderstanding risk")


class TeachingPlan(BaseModel):
    """Complete teaching plan with ordered steps."""
    steps: List[TeachingStep] = Field(..., description="Ordered teaching steps (typically 8)")


# ── Storyboard ───────────────────────────────────────────────────

class StoryboardPanel(BaseModel):
    """A single panel in the cartoon storyboard."""
    panel_id: str = Field(..., description="Panel identifier, e.g. 'panel_01'")
    title: str = Field(..., description="Panel title")
    source_chunk_ids: List[str] = Field(default_factory=list, description="Referenced source chunks")
    plain_explanation: str = Field(default="", description="Plain-language explanation of the concept")
    visual_scene: str = Field(default="", description="Description of the visual scene for this panel")
    characters: List[str] = Field(default_factory=list, description="Characters or elements in the scene")
    composition: str = Field(default="", description="Composition and layout guidance")
    caption: str = Field(default="", description="Caption text for the panel")
    takeaway: str = Field(default="", description="Key takeaway from this panel")
    must_include: List[str] = Field(default_factory=list, description="Elements that must appear in the image")
    must_avoid: List[str] = Field(default_factory=list, description="Elements to avoid in the image")
    image_prompt: str = Field(default="", description="English image generation prompt")
    verification_status: str = Field(default="pending", description="Verification status: pending|reviewed|revised")


class Storyboard(BaseModel):
    """Complete cartoon storyboard with panels."""
    panels: List[StoryboardPanel] = Field(..., description="Storyboard panels (typically 8)")


# ── Cards ────────────────────────────────────────────────────────

class ImageCard(BaseModel):
    """Final explainer card with SVG placeholder and metadata."""
    card_id: str = Field(..., description="Card identifier, e.g. 'card_01'")
    title: str = Field(..., description="Card title")
    explanation: str = Field(..., description="Plain-language explanation")
    image_placeholder_svg: str = Field(default="", description="Inline SVG placeholder")
    image_prompt: str = Field(default="", description="English image generation prompt")
    takeaway: str = Field(default="", description="Key takeaway")
    source_chunk_ids: List[str] = Field(default_factory=list, description="Referenced source chunks")
    source_excerpt: str = Field(default="", description="Verbatim excerpt from source")
    review_status: str = Field(default="pending", description="Review status: pending|reviewed|revised")


# ── Run Summary ──────────────────────────────────────────────────

class RunSummary(BaseModel):
    """Summary of a complete analysis run."""
    input_file: str = Field(..., description="Path to input file")
    output_dir: str = Field(..., description="Path to output directory")
    input_type: str = Field(default="txt", description="Input source type: txt, md, or pdf")
    chunk_count: int = Field(default=0)
    page_count: Optional[int] = Field(default=None, description="Number of source pages (PDF only)")
    concept_count: int = Field(default=0)
    step_count: int = Field(default=0)
    panel_count: int = Field(default=0)
    card_count: int = Field(default=0)
    output_files: List[str] = Field(default_factory=list, description="Files generated")
    extraction_method: str = Field(default="built-in", description="How text was extracted")
    warnings: List[str] = Field(default_factory=list, description="Warnings during processing")
    source_quality: dict = Field(default_factory=dict, description="Source quality metadata")
