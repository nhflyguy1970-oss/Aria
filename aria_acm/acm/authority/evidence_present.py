"""Memory evidence presentation (B03) — read-only rendering over existing evidence.

Never invents evidence. Applies B29 redaction at the presentation boundary.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from acm.authority.redaction import (
    DEFAULT_REDACTION_POLICY,
    RedactionPolicy,
    build_redaction_context,
    redact_text,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

_MAX_LINES = 6


def present_memory_evidence(
    result: dict[str, Any],
    *,
    engine: CognitiveEngine | None = None,
    policy: RedactionPolicy | None = None,
) -> dict[str, Any]:
    """Render supporting Experiences/concepts as concise user-facing evidence.

    ``result`` is a CognitiveMemoryResult public dict (or inspect_evidence view).
    """
    policy = policy or (
        getattr(engine, "redaction_policy", None) if engine is not None else None
    ) or DEFAULT_REDACTION_POLICY
    cue = str(result.get("cue") or "")
    ctx = (
        build_redaction_context(engine, cue=cue, intent=str(result.get("intent") or ""))
        if engine is not None
        else None
    )

    experiences = list(result.get("supporting_experiences") or [])[:8]
    provenance = list(result.get("provenance") or [])[:8]
    concepts = list(result.get("supporting_concepts") or [])[:6]

    lines: list[str] = []
    for exp in experiences:
        if not isinstance(exp, dict):
            continue
        summary = exp.get("summary") or ""
        if ctx is not None:
            summary = redact_text(str(summary), ctx=ctx, policy=policy) or ""
        if summary:
            lines.append(f"Supporting experience: {summary}")
        if len(lines) >= _MAX_LINES:
            break

    if not lines:
        for prov in provenance:
            if not isinstance(prov, dict):
                continue
            explain = prov.get("explain") or prov.get("origin") or ""
            if ctx is not None:
                explain = redact_text(str(explain), ctx=ctx, policy=policy) or ""
            if explain:
                lines.append(f"Provenance: {explain}")
            if len(lines) >= _MAX_LINES:
                break

    concept_bits = []
    for con in concepts:
        if isinstance(con, dict) and con.get("id"):
            concept_bits.append(str(con.get("label") or con.get("id")))
    if concept_bits and len(lines) < _MAX_LINES:
        lines.append("Related concepts: " + ", ".join(concept_bits[:4]))

    fabricated = False
    speech: str | None
    if lines:
        speech = " ".join(lines[:_MAX_LINES])
        if len(experiences) == 1 and experiences[0].get("summary"):
            # Prefer backlog-style single-evidence phrasing when possible
            one = lines[0].removeprefix("Supporting experience: ").strip()
            if one:
                speech = f"You told me something that supports this; one experience supports it: {one}"
    else:
        memory = result.get("memory")
        if memory and str(memory).strip():
            speech = str(memory).strip()
            if ctx is not None:
                speech = redact_text(speech, ctx=ctx, policy=policy)
        else:
            speech = None

    return {
        "schema": "acm.evidence_presentation.v1",
        "speech": speech,
        "lines": lines[:_MAX_LINES],
        "experience_count": len(experiences),
        "provenance_count": len(provenance),
        "concept_count": len(concepts),
        "fabricated": fabricated,
        "status": "known" if speech else "unknown",
        "redaction": policy.level.value,
    }
