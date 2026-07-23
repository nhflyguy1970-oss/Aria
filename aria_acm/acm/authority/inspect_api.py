"""Non-mutating inspection façades (B08) over read-only diagnostic mode (B07).

These APIs never become a second cognitive authority. They invoke the same
Memory Authority path under ``ExecutionMode.READ_ONLY`` and project structured
read models for hosts and diagnostics. B29 redaction applies at this boundary.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from acm.authority.redaction import (
    build_redaction_context,
    policy_for_engine,
    redact_inspect_view,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine


def _finalize(engine: CognitiveEngine, view: dict[str, Any], *, cue: str = "", who: str | None = None) -> dict[str, Any]:
    policy = policy_for_engine(engine)
    ctx = build_redaction_context(
        engine,
        cue=cue or str(view.get("cue") or ""),
        intent=str(view.get("intent") or ""),
        who=who,
    )
    return redact_inspect_view(view, policy=policy, ctx=ctx)


def inspect_reconstruction(engine: CognitiveEngine, cue: str) -> dict[str, Any]:
    """Reconstruction read-model without reconsolidation."""
    result = engine.inspect(cue)
    payload = result.get("organ_payload") or {}
    view = {
        "schema": "acm.inspect.reconstruction.v1",
        "cue": cue,
        "intent": result.get("intent"),
        "status": result.get("status"),
        "memory": result.get("memory"),
        "confidence": float(result.get("confidence") or 0.0),
        "ambiguous": bool(result.get("ambiguous")),
        "explanation_class": result.get("explanation_class"),
        "uncertainty": result.get("uncertainty"),
        "supporting_concepts": list(result.get("supporting_concepts") or [])[:12],
        "supporting_associations": list(result.get("supporting_associations") or [])[:12],
        "terminated_at": (result.get("diagnostics") or {}).get("terminated_at")
        or payload.get("terminated_at"),
        "execution_mode": (result.get("diagnostics") or {}).get("execution_mode"),
        "fingerprint": engine.store_fingerprint(),
    }
    return _finalize(engine, view, cue=cue)


def inspect_evidence(engine: CognitiveEngine, cue: str) -> dict[str, Any]:
    """Evidence / provenance read-model without store mutation."""
    from acm.authority.evidence_present import present_memory_evidence

    result = engine.inspect(cue)
    view = {
        "schema": "acm.inspect.evidence.v1",
        "cue": cue,
        "intent": result.get("intent"),
        "status": result.get("status"),
        "memory": result.get("memory"),
        "provenance": list(result.get("provenance") or [])[:20],
        "supporting_experiences": list(result.get("supporting_experiences") or [])[:20],
        "supporting_concepts": list(result.get("supporting_concepts") or [])[:12],
        "supporting_associations": list(result.get("supporting_associations") or [])[:12],
        "reflective_evidence": list(result.get("reflective_evidence") or [])[:12],
        "learning_evidence": list(result.get("learning_evidence") or [])[:12],
        "execution_mode": (result.get("diagnostics") or {}).get("execution_mode"),
        "fingerprint": engine.store_fingerprint(),
    }
    finalized = _finalize(engine, view, cue=cue)
    finalized["presentation"] = present_memory_evidence(finalized, engine=engine)
    return finalized


def inspect_confidence(engine: CognitiveEngine, cue: str) -> dict[str, Any]:
    """Confidence / uncertainty read-model without confidence-event writes."""
    from acm.authority.mode import read_only

    with read_only():
        certain = engine.how_certain_am_i(cue)
        result = engine.inspect(cue)
    view = {
        "schema": "acm.inspect.confidence.v1",
        "cue": cue,
        "intent": result.get("intent"),
        "status": result.get("status"),
        "reconstruction_confidence": float(result.get("confidence") or 0.0),
        "overall_confidence": float(certain.get("overall_confidence") or 0.0),
        "uncertainty": certain.get("uncertainty") or result.get("uncertainty"),
        "answer": certain.get("answer"),
        "snapshots": list(certain.get("snapshots") or [])[:8],
        "execution_mode": "read_only",
        "fingerprint": engine.store_fingerprint(),
    }
    return _finalize(engine, view, cue=cue)


def inspect_identity(engine: CognitiveEngine, *, who: str = "user") -> dict[str, Any]:
    """Identity read-model (user or assistant) without remembering gap-fill writes."""
    cue = "Who am I?" if who == "user" else "Who are you?"
    result = engine.inspect(cue)
    snap = engine.identity_snapshot()
    view = {
        "schema": "acm.inspect.identity.v1",
        "who": who,
        "cue": cue,
        "intent": result.get("intent"),
        "status": result.get("status"),
        "memory": result.get("memory"),
        "confidence": float(result.get("confidence") or 0.0),
        "snapshot": {
            "agent_id": snap.get("agent_id"),
            "schemas": snap.get("schemas"),
            "confidence": snap.get("confidence"),
        },
        "execution_mode": (result.get("diagnostics") or {}).get("execution_mode"),
        "fingerprint": engine.store_fingerprint(),
    }
    return _finalize(engine, view, cue=cue, who=who)


def inspect_conflict(engine: CognitiveEngine, cue: str) -> dict[str, Any]:
    """Conflict / ambiguity read-model without reflective birth or learning."""
    result = engine.inspect(cue)
    payload = result.get("organ_payload") or {}
    raw = payload.get("raw") if isinstance(payload.get("raw"), dict) else {}
    competing: list[Any] = []
    if isinstance(raw, dict):
        competing = list(raw.get("competing") or raw.get("competitors") or [])[:8]
    # Prefer reconstruction competing from a fresh remember under read-only.
    from acm.authority.mode import read_only

    with read_only():
        remembered = engine.remember(cue)
    recon = remembered.reconstruction or {}
    if not competing:
        competing = list(recon.get("competing") or [])[:8]
    view = {
        "schema": "acm.inspect.conflict.v1",
        "cue": cue,
        "intent": result.get("intent"),
        "status": result.get("status"),
        "memory": result.get("memory"),
        "ambiguous": bool(result.get("ambiguous") or remembered.ambiguous),
        "confidence": float(result.get("confidence") or remembered.confidence or 0.0),
        "uncertainty": result.get("uncertainty"),
        "competing": competing,
        "supporting_experiences": list(result.get("supporting_experiences") or [])[:12],
        "execution_mode": (result.get("diagnostics") or {}).get("execution_mode"),
        "fingerprint": engine.store_fingerprint(),
    }
    return _finalize(engine, view, cue=cue)
