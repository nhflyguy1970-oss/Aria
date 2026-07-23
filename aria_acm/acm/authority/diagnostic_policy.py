"""Diagnostic safety policy (B09).

Defines what diagnostic / inspect surfaces may expose and what they must forbid.
Composes B29 redaction; never invents Experiences; never mutates living memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, TYPE_CHECKING

from acm.authority.handlers import FORBIDDEN_TERMINALS, sanitize_cognitive_text
from acm.authority.redaction import (
    DEFAULT_REDACTION_POLICY,
    RedactionContext,
    RedactionPolicy,
    build_redaction_context,
    policy_for_engine,
    redact_inspect_view,
    redact_organ_view,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.diagnostic_safety.v1"

# Keys hosts may rely on at the public diagnostic boundary.
_ALWAYS_KEEP = frozenset(
    {
        "schema",
        "fingerprint",
        "execution_mode",
        "cue",
        "intent",
        "status",
        "who",
        "confidence",
        "reconstruction_confidence",
        "overall_confidence",
        "ambiguous",
        "redaction",
        "redaction_applied",
        "safety_policy",
        "safety_policy_applied",
        "safety_policy_enabled",
        "presentation",
        "terminated_at",
        "explanation_class",
        "uncertainty",
        "memory",
        "answer",
    }
)

# Structural fields never exposed in production diagnostics.
_FORBIDDEN_TOP_LEVEL = frozenset(
    {
        "store",
        "cognitive_store",
        "memory_store",
        "raw_store",
        "db_row",
        "db_rows",
        "sql",
        "traceback",
        "stack",
        "module_path",
        "file_path",
        "source_code",
    }
)

_FORBIDDEN_NESTED = frozenset(
    {
        "raw",  # organ_payload.raw — internal reconstruction dumps
        "reconstruction_steps",
        "adaptation_records",
        "store_dump",
        "internal_state",
    }
)

_LIST_CAPS = {
    "provenance": 20,
    "supporting_experiences": 20,
    "supporting_concepts": 12,
    "supporting_associations": 12,
    "reflective_evidence": 12,
    "learning_evidence": 12,
    "competing": 8,
    "snapshots": 8,
    "contributions": 16,
}


@dataclass(frozen=True)
class DiagnosticSafetyPolicy:
    """Host-configurable diagnostic exposure policy (production-safe default)."""

    enabled: bool = True  # production default: policy ON
    redaction: RedactionPolicy = field(default_factory=lambda: DEFAULT_REDACTION_POLICY)
    max_list_items: int = 20
    strip_organ_raw: bool = True
    strip_reconstruction_steps: bool = True
    sanitize_substrate: bool = True
    forbid_terminals: frozenset[str] = field(default_factory=lambda: FORBIDDEN_TERMINALS)


DEFAULT_DIAGNOSTIC_SAFETY_POLICY = DiagnosticSafetyPolicy()


def policy_for_engine_safety(engine: CognitiveEngine) -> DiagnosticSafetyPolicy:
    """Resolve engine diagnostic safety policy (default enabled + B29 STRICT)."""
    policy = getattr(engine, "diagnostic_safety_policy", None)
    redaction = policy_for_engine(engine)
    if policy is not None and hasattr(policy, "enabled") and hasattr(policy, "redaction"):
        if isinstance(policy, DiagnosticSafetyPolicy):
            if policy.redaction != redaction:
                return replace(policy, redaction=redaction)
            return policy
        return DiagnosticSafetyPolicy(
            enabled=bool(getattr(policy, "enabled", True)),
            redaction=redaction,
            max_list_items=int(getattr(policy, "max_list_items", 20)),
            strip_organ_raw=bool(getattr(policy, "strip_organ_raw", True)),
            strip_reconstruction_steps=bool(
                getattr(policy, "strip_reconstruction_steps", True)
            ),
            sanitize_substrate=bool(getattr(policy, "sanitize_substrate", True)),
        )
    return replace(DEFAULT_DIAGNOSTIC_SAFETY_POLICY, redaction=redaction)


def _cap_list(value: Any, limit: int) -> Any:
    if isinstance(value, list) and len(value) > limit:
        return value[:limit]
    return value


def _sanitize_substrate(touched: Any) -> list[str]:
    if not isinstance(touched, (list, tuple)):
        return []
    out: list[str] = []
    for item in touched:
        s = str(item or "").strip().lower()
        if not s:
            continue
        if s in {"cognitive_store", "memory_store", "store", "database", "db"}:
            out.append("substrate_only")
        elif s in FORBIDDEN_TERMINALS:
            continue
        else:
            out.append(s)
    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _scrub_tree(value: Any, *, policy: DiagnosticSafetyPolicy, depth: int = 0) -> Any:
    if depth > 12:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            key = str(k)
            low = key.casefold()
            if low in _FORBIDDEN_TOP_LEVEL or low in _FORBIDDEN_NESTED:
                if policy.strip_organ_raw and low == "raw":
                    out[key] = {"redacted": True, "reason": "diagnostic_safety"}
                    continue
                if policy.strip_reconstruction_steps and low == "reconstruction_steps":
                    out[key] = {"redacted": True, "reason": "diagnostic_safety"}
                    continue
                continue
            if key == "substrate_touched" and policy.sanitize_substrate:
                out[key] = _sanitize_substrate(v)
                continue
            if key == "terminated_at" and str(v).casefold() in policy.forbid_terminals:
                out[key] = "unknown"
                continue
            cap = _LIST_CAPS.get(key, policy.max_list_items if isinstance(v, list) else None)
            if isinstance(v, list) and cap is not None:
                v = _cap_list(v, int(cap))
            out[key] = _scrub_tree(v, policy=policy, depth=depth + 1)
        return out
    if isinstance(value, list):
        return [_scrub_tree(v, policy=policy, depth=depth + 1) for v in value]
    if isinstance(value, tuple):
        return tuple(_scrub_tree(v, policy=policy, depth=depth + 1) for v in value)
    if isinstance(value, str):
        return sanitize_cognitive_text(value) or value
    return value


def apply_diagnostic_policy(
    payload: dict[str, Any],
    *,
    engine: CognitiveEngine,
    cue: str = "",
    who: str | None = None,
    as_organ_view: bool = False,
) -> dict[str, Any]:
    """Apply B09 safety + B29 redaction at a diagnostic projection boundary."""
    policy = policy_for_engine_safety(engine)
    if not policy.enabled:
        out = dict(payload)
        out["safety_policy"] = SCHEMA
        out["safety_policy_enabled"] = False
        out["safety_policy_applied"] = False
        return out

    ctx = build_redaction_context(
        engine,
        cue=cue or str(payload.get("cue") or ""),
        intent=str(payload.get("intent") or ""),
        who=who,
    )
    scrubbed = _scrub_tree(dict(payload), policy=policy)
    if as_organ_view:
        redacted = redact_organ_view(scrubbed, policy=policy.redaction, ctx=ctx)
    else:
        redacted = redact_inspect_view(scrubbed, policy=policy.redaction, ctx=ctx)

    # Drop any remaining forbidden top-level keys after redaction.
    for key in list(redacted.keys()):
        if str(key).casefold() in _FORBIDDEN_TOP_LEVEL:
            redacted.pop(key, None)

    redacted["safety_policy"] = SCHEMA
    redacted["safety_policy_enabled"] = True
    redacted["safety_policy_applied"] = True
    return redacted


def with_safety_enabled(
    policy: DiagnosticSafetyPolicy, *, enabled: bool
) -> DiagnosticSafetyPolicy:
    return replace(policy, enabled=enabled)
