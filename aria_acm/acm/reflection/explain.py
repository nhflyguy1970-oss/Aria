"""Reflection explanation rendering (B18) — structured fields only, no chain-of-thought."""

from __future__ import annotations

from typing import Any


def explain_reflection(evaluation: dict[str, Any] | Any) -> str:
    """Render a ReflectionEvaluation (public dict or object) into faithful speech."""
    if hasattr(evaluation, "to_public"):
        data = evaluation.to_public()
    elif isinstance(evaluation, dict):
        data = evaluation
    else:
        return "I reflected, but no structured evaluation is available."

    outcomes = [str(o) for o in (data.get("outcomes") or [])]
    contradictions = [str(c) for c in (data.get("contradictions") or []) if c]
    consistencies = [str(c) for c in (data.get("consistencies") or []) if c]
    patterns = [str(p) for p in (data.get("patterns") or []) if p]
    remembered = str(data.get("remembered_answer") or "").strip()
    summary = str(data.get("answer") or data.get("evaluation_summary") or "").strip()

    parts: list[str] = []
    if "contradiction" in outcomes and contradictions:
        joined = "; ".join(contradictions[:2])
        parts.append(
            f"I marked this contradictory because these remembered values both answer the cue: {joined}."
        )
    elif "contradiction" in outcomes:
        parts.append(
            "I marked this contradictory because competing remembered values answer the cue."
        )

    if "consistency" in outcomes and consistencies:
        parts.append(
            "Remembered evidence is consistent: " + "; ".join(consistencies[:2]) + "."
        )
    elif "consistency" in outcomes:
        parts.append("Remembered evidence appears consistent for this cue.")

    if "pattern" in outcomes and patterns:
        parts.append("I noticed a pattern: " + "; ".join(patterns[:2]) + ".")
    elif "pattern" in outcomes:
        parts.append("I noticed a recurring pattern across related memories.")

    if "insufficient_evidence" in outcomes or data.get("insufficient_evidence"):
        parts.append("Evidence is insufficient for a firm judgment.")
    if "uncertainty" in outcomes and not parts:
        parts.append("I am uncertain based on the current remembered evidence.")

    if remembered and not any(remembered.lower() in p.lower() for p in parts):
        parts.append(f"What I remember is: {remembered}.")

    if not parts:
        if summary:
            return summary
        return "I reflected on what I remember, without a stronger structured outcome."

    return " ".join(parts)
