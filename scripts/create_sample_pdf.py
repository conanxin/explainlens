#!/usr/bin/env python3
"""Generate a sample 3-page PDF for ExplainLens demo and testing.

Uses PyMuPDF (fitz) to create a searchable PDF with embedded text.
Content is original fiction about an AI Reading Assistant.

Usage:
    python scripts/create_sample_pdf.py
    # Output: examples/sample_paper.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

# Fix Windows GBK encoding issue
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import fitz
except ImportError:
    print("[ERROR] PyMuPDF (fitz) is required. Install with: pip install pymupdf")
    sys.exit(1)

OUTPUT = Path(__file__).resolve().parent.parent / "examples" / "sample_paper.pdf"

PAGE_1_TITLE = "Visual Explainer Cards: Turning Complex Papers into Accessible Knowledge"
PAGE_1_BODY = (
    "The rapid growth of scientific publishing has created a widening gap between "
    "specialized research and public understanding. Each year, over 3 million peer-reviewed "
    "papers are published, yet fewer than 0.1% ever reach a non-specialist audience. "
    "This communication bottleneck prevents valuable insights from influencing policy, "
    "education, and public discourse.\n\n"
    "Traditional science communication relies on human mediators—journalists, educators, "
    "and popularizers—to translate dense academic prose into accessible formats. "
    "However, this pipeline cannot scale to match the volume of published research. "
    "Even well-funded science communication initiatives cover only a tiny fraction "
    "of the literature.\n\n"
    "We identify three core challenges: (1) the exponential growth of scientific output "
    "outpaces human translation capacity; (2) existing automated summarization tools "
    "produce text-only outputs that fail to leverage the pedagogical power of visual "
    "explanation; and (3) most readers abandon complex papers within the first two pages, "
    "never reaching the insights buried in methods and results sections.\n\n"
    "This paper proposes Visual Explainer Cards (VEC)—a system that automatically "
    "transforms academic papers into structured, illustrated explainer cards. "
    "Each card targets a single concept, pairing a plain-language explanation with "
    "a visual metaphor, key takeaways, and source references. The system is designed "
    "to operate locally, without requiring external AI APIs, making it suitable "
    "for privacy-sensitive domains such as medical research and legal analysis."
)

PAGE_2_TITLE = "Proposed Approach: The 8-Step Teaching Pipeline"
PAGE_2_BODY = (
    "Our approach is grounded in two observations from cognitive science: "
    "(1) the generation effect shows that restructuring information into new formats "
    "improves comprehension, and (2) dual coding theory demonstrates that combining "
    "verbal and visual channels enhances learning.\n\n"
    "The VEC pipeline consists of eight sequential stages, each inspired by "
    "established pedagogical principles:\n\n"
    "Stage 1 — Problem Identification: Extract the core research question "
    "from the introduction. We use heuristic keyword matching to locate problem "
    "statements, gap declarations, and motivation clauses.\n\n"
    "Stage 2 — Significance Framing: Identify why the problem matters. "
    "We scan for phrases indicating real-world impact, economic implications, "
    "or societal relevance.\n\n"
    "Stage 3 — Baseline Comparison: Extract descriptions of prior approaches. "
    "We leverage section heading heuristics and transition phrases like "
    "'previous work', 'existing methods', and 'state of the art'.\n\n"
    "Stage 4 — Conceptual Mapping: Build a concept graph from key terms. "
    "We extract noun phrases and named entities, then construct a co-occurrence "
    "network weighted by paragraph proximity.\n\n"
    "Stage 5 — Mechanism Decomposition: Break down the proposed method into "
    "sequential steps. We detect enumerations (first, second, then), process "
    "descriptions (the system computes, the algorithm selects), and data flows.\n\n"
    "Stage 6 — Evidence Compilation: Aggregate findings, statistics, and "
    "performance metrics. We extract sentences containing numerical comparisons, "
    "percentage improvements, and statistical significance markers.\n\n"
    "Stage 7 — Limitation Enumeration: Identify caveats, assumptions, "
    "boundary conditions, and acknowledged weaknesses. We scan for hedging "
    "language, limitation sections, and future work declarations.\n\n"
    "Stage 8 — Impact Synthesis: Compose a unified takeaway that connects "
    "the problem, solution, and implications into a concise narrative arc."
)

PAGE_3_TITLE = "Evaluation, Limitations, and Future Directions"
PAGE_3_BODY = (
    "We evaluated VEC on a corpus of 500 open-access papers spanning computer "
    "science, biomedicine, and social sciences. Human raters (n=12, all graduate "
    "students with domain expertise) assessed the generated cards on three "
    "dimensions: factual accuracy (mean 4.2/5.0), pedagogical clarity (mean 4.0/5.0), "
    "and visual metaphor appropriateness (mean 3.7/5.0).\n\n"
    "Inter-rater reliability was moderate (Fleiss kappa = 0.62), suggesting "
    "consistent but not uniform judgment. The lowest-scoring cards typically "
    "involved highly technical methods sections where heuristic extraction "
    "struggled to identify the core mechanism.\n\n"
    "Current limitations include: (1) The system cannot parse figures, tables, "
    "or mathematical notation embedded in PDFs—these are simply omitted from "
    "text extraction. (2) Multi-column academic layouts occasionally produce "
    "out-of-order text, confusing the section detection heuristics. (3) The "
    "visual metaphors are drawn from a fixed palette of eight geometric "
    "templates, which may not suit all subject domains. (4) Scanned PDFs "
    "without embedded text layers are not supported, as we intentionally "
    "exclude OCR from the pipeline to maintain simplicity and speed.\n\n"
    "Several promising directions remain: integrating lightweight language "
    "models for more nuanced concept extraction, adding support for figure "
    "and table parsing, and developing domain-specific visual metaphor "
    "libraries for fields like chemistry, physics, and medicine.\n\n"
    "The source code is available as open source under the MIT license. "
    "We invite contributions from the community to extend the pipeline "
    "and improve extraction quality across diverse document formats."
)


def _add_text_page(doc: fitz.Document, title: str, body: str, page_num: int) -> None:
    """Add a single page of structured text to the PDF."""
    page = doc.new_page(width=595, height=842)  # A4

    # Header
    page.insert_text(
        fitz.Point(50, 50),
        f"ExplainLens Sample Paper — Page {page_num}",
        fontsize=9, color=(0.4, 0.4, 0.4),
    )

    # Title
    rect = fitz.Rect(50, 80, 545, 160)
    page.insert_textbox(rect, title, fontsize=16, fontname="helv",
                        color=(0.1, 0.1, 0.3), align=fitz.TEXT_ALIGN_LEFT)

    # Body
    rect = fitz.Rect(50, 175, 545, 780)
    page.insert_textbox(rect, body, fontsize=11, fontname="helv",
                        color=(0.15, 0.15, 0.15), align=fitz.TEXT_ALIGN_LEFT)

    # Footer
    page.insert_text(
        fitz.Point(50, 810),
        f"Sample Paper for ExplainLens Demo — Not a real publication",
        fontsize=8, color=(0.6, 0.6, 0.6),
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    _add_text_page(doc, PAGE_1_TITLE, PAGE_1_BODY, 1)
    _add_text_page(doc, PAGE_2_TITLE, PAGE_2_BODY, 2)
    _add_text_page(doc, PAGE_3_TITLE, PAGE_3_BODY, 3)

    doc.save(str(OUTPUT))
    doc.close()

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Sample PDF generated: {OUTPUT}")
    print(f"Pages: 3, Size: {size_kb:.1f} KB")
    print(f"Content: AI Reading Assistant / Visual Explainer Cards (fictional)")


if __name__ == "__main__":
    main()
