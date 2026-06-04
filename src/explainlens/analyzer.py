"""Content analyzer — heuristic keyword-based extraction of concepts and claims."""

from __future__ import annotations

import re
from typing import List

from explainlens.schemas import ConceptMap, SourceChunk


# ── Keyword and pattern sets for heuristic analysis ──────────────

_PROBLEM_KEYWORDS = [
    "problem", "challenge", "issue", "gap", "limitation", "limitations",
    "shortcoming", "drawback", "bottleneck", "difficulty", "obstacle",
    "问题", "挑战", "不足", "局限", "瓶颈", "难点", "困难", "障碍",
]

_IMPORTANCE_KEYWORDS = [
    "important", "significant", "critical", "crucial", "essential",
    "impact", "implication", "fundamental",
    "重要", "关键", "根本", "重大", "影响",
]

_METHOD_KEYWORDS = [
    "method", "approach", "algorithm", "framework", "model", "technique",
    "procedure", "protocol", "pipeline", "architecture", "mechanism",
    "we propose", "we introduce", "we present", "we develop",
    "方法", "算法", "框架", "模型", "技术", "架构", "机制", "方案",
    "提出", "引入", "设计",
]

_EVIDENCE_KEYWORDS = [
    "experiment", "result", "evaluation", "benchmark", "dataset",
    "demonstrate", "show that", "found that", "indicate", "suggest",
    "compared to", "outperforms", "achieves",
    "实验", "结果", "评估", "数据", "表明", "证明", "显示",
]

_LIMITATION_KEYWORDS = [
    "limitation", "limitations", "future work", "caveat", "however",
    "although", "despite", "remains", "open question", "not yet",
    "局限", "不足", "未来", "但是", "然而", "尚需", "有待",
]


def _sentences(text: str) -> List[str]:
    """Split text into sentences (simple split on period/exclamation/question + space)."""
    return [s.strip() for s in re.split(r'(?<=[.!?。！？])\s+', text) if s.strip()]


def _find_sentences_with_keywords(text: str, keywords: List[str], max_results: int = 5) -> List[str]:
    """Return sentences that contain any of the given keywords."""
    hits = []
    for sent in _sentences(text):
        sent_lower = sent.lower()
        if any(kw.lower() in sent_lower for kw in keywords):
            hits.append(sent)
            if len(hits) >= max_results:
                break
    return hits


def analyze(chunks: List[SourceChunk]) -> ConceptMap:
    """Perform heuristic analysis on chunks to extract concepts, claims, etc.

    Args:
        chunks: List of source chunks from the document.

    Returns:
        A ConceptMap with extracted structured information.
    """
    full_text = " ".join(c.text for c in chunks)

    # 1. Core problem
    problem_sents = _find_sentences_with_keywords(full_text, _PROBLEM_KEYWORDS, max_results=3)
    if chunks:
        core_problem = problem_sents[0] if problem_sents else chunks[0].text[:200].strip()
    else:
        core_problem = ""

    # 2. Key concepts — extract noun phrases near definition patterns
    definition_pattern = re.compile(
        r'(?:is|are|refers to|means|defined as|denotes)\s+(?:a|an|the)?\s*(.{10,120}?)[.!]',
        re.IGNORECASE,
    )
    key_concepts = []
    for m in definition_pattern.finditer(full_text):
        concept_text = m.group(1).strip()
        if concept_text and concept_text not in key_concepts:
            key_concepts.append(concept_text)
        if len(key_concepts) >= 5:
            break
    # Fallback: use first sentences from early chunks as concepts
    if not key_concepts and chunks:
        # Extract capitalized phrases or key topic words
        key_concepts = [_sentences(c.text)[0][:120] for c in chunks[:3] if _sentences(c.text)]

    # 3. Key claims
    claim_sents = _find_sentences_with_keywords(
        full_text,
        ["we argue", "we claim", "we find", "we show", "key insight", "key finding",
         "contribution", "contributes", "novel", "new approach", "first to",
         "我们认为", "本文发现", "核心观点", "创新", "贡献"],
        max_results=5,
    )
    if not claim_sents:
        # Fallback: use early substantive sentences
        claim_sents = [s for s in _sentences(full_text)[:5] if len(s) > 30]
    key_claims = claim_sents[:5]

    # 4. Methods or mechanisms
    methods = _find_sentences_with_keywords(full_text, _METHOD_KEYWORDS, max_results=5)
    if not methods:
        methods = ["(heuristic extraction found no explicit method descriptions)"]

    # 5. Evidence or examples
    evidence = _find_sentences_with_keywords(full_text, _EVIDENCE_KEYWORDS, max_results=5)
    if not evidence:
        evidence = ["(heuristic extraction found no explicit evidence descriptions)"]

    # 6. Limitations
    limits = _find_sentences_with_keywords(full_text, _LIMITATION_KEYWORDS, max_results=5)
    if not limits:
        limits = ["(no explicit limitations detected — review manually)"]

    # 7. Why it matters
    importance_sents = _find_sentences_with_keywords(full_text, _IMPORTANCE_KEYWORDS, max_results=2)
    why_it_matters = importance_sents[0] if importance_sents else (
        f"This content introduces concepts around: {', '.join(kc[:60] for kc in key_concepts[:3])}"
        if key_concepts else "This content presents new ideas worth understanding."
    )

    return ConceptMap(
        core_problem=core_problem,
        key_concepts=key_concepts,
        key_claims=key_claims,
        methods_or_mechanisms=methods,
        evidence_or_examples=evidence,
        limitations=limits,
        why_it_matters=why_it_matters,
    )
