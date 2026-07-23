"""Diagnostic privacy / redaction policy (B29).

Protects inspect façades and organ views from leaking unrelated identity,
context, or sensitive content. Reuses D044 isolation primitives. Applies only
at diagnostic projection boundaries — never invents or mutates memory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, TYPE_CHECKING

from acm.identity.rendering import (
    IdentityRenderTarget,
    assistant_forbidden_from_user,
    isolate_identity_text,
    is_relationship_identity_request,
    user_forbidden_from_assistant,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_REDACTED = "[redacted]"
_MAX_SNIPPET = 120

# Text field names commonly carrying memory content in diagnostic views.
_TEXT_KEYS = frozenset(
    {
        "memory",
        "answer",
        "summary",
        "explain",
        "cue",
        "label",
        "answer_preview",
        "text",
        "content",
        "value",
        "uncertainty",
    }
)


class RedactionLevel(StrEnum):
    """Diagnostic redaction strictness."""

    NONE = "none"
    STANDARD = "standard"
    STRICT = "strict"  # engineering-bounded production default


@dataclass(frozen=True)
class RedactionPolicy:
    """Shared rendering policy for diagnostic surfaces."""

    level: RedactionLevel = RedactionLevel.STRICT
    max_snippet: int = _MAX_SNIPPET


DEFAULT_REDACTION_POLICY = RedactionPolicy()


@dataclass(frozen=True)
class RedactionContext:
    """Per-request isolation context for diagnostic projection."""

    cue: str = ""
    intent: str = ""
    target: IdentityRenderTarget = IdentityRenderTarget.USER
    forbidden_values: frozenset[str] = field(default_factory=frozenset)
    relationship_allowed: bool = False


def _attr_pairs(concept: Any) -> list[tuple[str, str]]:
    if concept is None:
        return []
    pairs: list[tuple[str, str]] = []
    for attr in getattr(concept, "attributes", ()) or ():
        if getattr(attr, "active", False) and getattr(attr, "value", None):
            pairs.append((str(attr.key), str(attr.value)))
    return pairs


def build_redaction_context(
    engine: CognitiveEngine,
    *,
    cue: str = "",
    intent: str = "",
    who: str | None = None,
) -> RedactionContext:
    """Build forbidden-value isolation context from living identity schemas."""
    relationship = is_relationship_identity_request(cue)
    if who == "assistant" or (intent or "").lower() in {
        "assistant_identity",
        "who_are_you",
        "agent_identity",
    }:
        target = IdentityRenderTarget.ASSISTANT
    elif relationship:
        target = IdentityRenderTarget.RELATIONSHIP
    else:
        target = IdentityRenderTarget.USER

    user = engine.identity.schema_concept("user")
    agent = engine.identity.schema_concept("agent")
    user_pairs = _attr_pairs(user)
    agent_pairs = _attr_pairs(agent)

    if target == IdentityRenderTarget.ASSISTANT:
        forbidden = assistant_forbidden_from_user(user_pairs)
    elif target == IdentityRenderTarget.RELATIONSHIP:
        forbidden = set()
    else:
        forbidden = user_forbidden_from_assistant(agent_pairs, str(engine.agent_id or ""))

    return RedactionContext(
        cue=cue or "",
        intent=intent or "",
        target=target,
        forbidden_values=frozenset(v for v in forbidden if v and str(v).strip()),
        relationship_allowed=relationship,
    )


def scrub_sensitive_patterns(text: str) -> str:
    """Replace emails/phones with a redaction marker."""
    out = _EMAIL.sub(_REDACTED, text)
    return _PHONE.sub(_REDACTED, out)


def redact_text(
    text: str | None,
    *,
    ctx: RedactionContext,
    policy: RedactionPolicy = DEFAULT_REDACTION_POLICY,
) -> str | None:
    """Redact a single text field. Fail-closed: None when nothing safe remains."""
    if text is None:
        return None
    raw = str(text)
    if not raw.strip():
        return None
    if policy.level == RedactionLevel.NONE:
        return raw

    scrubbed = scrub_sensitive_patterns(raw)
    isolated = isolate_identity_text(
        scrubbed,
        target=ctx.target,
        forbidden_values=set(ctx.forbidden_values),
    )
    if isolated is None:
        return None if policy.level == RedactionLevel.STRICT else _REDACTED

    # Explicit token scrub for any residual forbidden values (non-sentence text).
    out = isolated
    for val in ctx.forbidden_values:
        if not val:
            continue
        out = re.sub(rf"\b{re.escape(val)}\b", _REDACTED, out, flags=re.IGNORECASE)

    out = scrub_sensitive_patterns(out).strip()
    if not out:
        return None if policy.level == RedactionLevel.STRICT else _REDACTED
    if len(out) > policy.max_snippet:
        out = out[: policy.max_snippet].rstrip() + "…"
    return out


def _redact_value(value: Any, *, ctx: RedactionContext, policy: RedactionPolicy, key: str = "") -> Any:
    if isinstance(value, str):
        if key in _TEXT_KEYS or key.endswith("_summary") or key.endswith("_text"):
            return redact_text(value, ctx=ctx, policy=policy)
        # Structural strings (ids, enums) — still scrub PII patterns.
        if policy.level != RedactionLevel.NONE and (_EMAIL.search(value) or _PHONE.search(value)):
            return scrub_sensitive_patterns(value)
        # Forbidden exact values in any string field under STRICT/STANDARD.
        if policy.level != RedactionLevel.NONE:
            low = value.casefold()
            for forbidden in ctx.forbidden_values:
                if forbidden and forbidden.casefold() == low:
                    return _REDACTED
                if forbidden and re.search(rf"\b{re.escape(forbidden)}\b", value, re.I):
                    return redact_text(value, ctx=ctx, policy=policy)
        return value
    if isinstance(value, dict):
        return {
            k: _redact_value(v, ctx=ctx, policy=policy, key=str(k))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(v, ctx=ctx, policy=policy, key=key) for v in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(v, ctx=ctx, policy=policy, key=key) for v in value)
    return value


def redact_inspect_view(
    view: dict[str, Any],
    *,
    policy: RedactionPolicy,
    ctx: RedactionContext,
) -> dict[str, Any]:
    """Apply redaction to an inspect façade payload."""
    if policy.level == RedactionLevel.NONE:
        out = dict(view)
        out["redaction"] = RedactionLevel.NONE.value
        out["redaction_applied"] = False
        return out

    # Preserve fingerprint / schema / numeric metadata; deep-redact content trees.
    protected = {"schema", "fingerprint", "execution_mode", "cue", "intent", "status", "who"}
    out: dict[str, Any] = {}
    for key, value in view.items():
        if key in protected:
            out[key] = value
        elif key in {"confidence", "reconstruction_confidence", "overall_confidence", "ambiguous"}:
            out[key] = value
        else:
            out[key] = _redact_value(value, ctx=ctx, policy=policy, key=key)

    # Identity snapshot: strip foreign schema attributes under STRICT.
    snap = out.get("snapshot")
    if isinstance(snap, dict) and isinstance(snap.get("schemas"), dict):
        out["snapshot"] = _redact_identity_snapshot(snap, ctx=ctx, policy=policy, who=str(view.get("who") or ""))

    out["redaction"] = policy.level.value
    out["redaction_applied"] = True
    return out


def _redact_identity_snapshot(
    snap: dict[str, Any],
    *,
    ctx: RedactionContext,
    policy: RedactionPolicy,
    who: str,
) -> dict[str, Any]:
    schemas = snap.get("schemas")
    if not isinstance(schemas, dict):
        return snap
    cleaned = dict(snap)
    new_schemas: dict[str, Any] = {}
    for schema_name, schema_body in schemas.items():
        # When inspecting assistant, drop user schema values; vice versa.
        if who == "assistant" and schema_name in {"user", "profile"}:
            new_schemas[schema_name] = {"redacted": True, "reason": "cross_identity"}
            continue
        if who == "user" and schema_name in {"agent", "assistant"}:
            new_schemas[schema_name] = {"redacted": True, "reason": "cross_identity"}
            continue
        new_schemas[schema_name] = _redact_value(schema_body, ctx=ctx, policy=policy)
    cleaned["schemas"] = new_schemas
    return cleaned


def redact_organ_view(
    view: dict[str, Any],
    *,
    policy: RedactionPolicy,
    ctx: RedactionContext | None = None,
) -> dict[str, Any]:
    """Apply redaction to an organ observability view."""
    ctx = ctx or RedactionContext()
    if policy.level == RedactionLevel.NONE:
        out = dict(view)
        out["redaction"] = RedactionLevel.NONE.value
        out.pop("note", None)
        return out

    out = dict(view)
    out["harness"] = _redact_value(view.get("harness") or {}, ctx=ctx, policy=policy)
    out["observables"] = _redact_value(view.get("observables") or {}, ctx=ctx, policy=policy)
    out["redaction"] = policy.level.value
    out["redaction_applied"] = True
    out.pop("note", None)
    return out


def policy_for_engine(engine: CognitiveEngine) -> RedactionPolicy:
    """Resolve the engine's diagnostic redaction policy (default STRICT)."""
    policy = getattr(engine, "redaction_policy", None)
    if policy is not None and hasattr(policy, "level"):
        if isinstance(policy, RedactionPolicy):
            return policy
        try:
            level = policy.level if isinstance(policy.level, RedactionLevel) else RedactionLevel(str(policy.level))
        except Exception:  # noqa: BLE001
            level = RedactionLevel.STRICT
        return RedactionPolicy(
            level=level,
            max_snippet=int(getattr(policy, "max_snippet", _MAX_SNIPPET)),
        )
    return DEFAULT_REDACTION_POLICY


def with_level(policy: RedactionPolicy, level: RedactionLevel) -> RedactionPolicy:
    return replace(policy, level=level)
