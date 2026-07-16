"""Semantic Extraction — natural language → structured cognitive facts.

LM-independent · host-independent · provider-independent.
"""

from __future__ import annotations

from acm.semantic.facts import extract_fact_patterns
from acm.semantic.model import ExtractionResult
from acm.semantic.perspective import resolve_perspective
from acm.semantic.strip import strip_instructional


def extract_semantics(
    text: str,
    *,
    kind: str = "experience",
    speaker: str | None = None,
) -> ExtractionResult:
    """Convert natural language into structured cognitive facts before storage.

    Original wording is retained as ``evidence`` only.
    ``primary_summary`` is the authoritative cognitive phrasing for Experience.summary.
    """
    evidence = (text or "").strip()
    if not evidence:
        return ExtractionResult(facts=[], evidence="", raw_fallback=True)

    cleaned, stripped = strip_instructional(evidence)
    perspective = resolve_perspective(cleaned, kind=kind, speaker=speaker)
    # Also consider instructional cues on original (before strip removes them)
    if stripped and speaker is None:
        perspective = resolve_perspective(evidence, kind=kind, speaker=speaker)

    facts = extract_fact_patterns(cleaned, perspective=perspective)
    raw_fallback = len(facts) == 0
    return ExtractionResult(
        facts=facts,
        evidence=evidence,
        perspective=perspective,
        instructional_stripped=stripped,
        raw_fallback=raw_fallback,
    )
