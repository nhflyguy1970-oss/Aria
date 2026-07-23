"""Identity correction & assent UX (B20).

Explicit preview / propose / assent / reject / cancel over IdentityPolicyGate.
Preserves user/assistant separation (D043/D044). Never invents Experiences;
commits go through ``encode(kind='identity')`` with governed assent.
"""

from __future__ import annotations

import re
from typing import Any, Literal, TYPE_CHECKING

from acm.authority.mode import is_read_only, read_only
from acm.provenance import TRUSTED_USER_STATEMENT

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.identity.edit.v1"
Who = Literal["user", "assistant"]

_LEGAL_NAME = re.compile(
    r"^\s*(?:my\s+)?(?:legal\s+)?name\s+(?:changed\s+to|is\s+now|is)\s+(?P<value>.+?)\s*\.?\s*$",
    re.I,
)
_CALL_ME = re.compile(
    r"^\s*(?:please\s+)?call\s+me\s+(?P<value>[A-Za-z][\w' -]*)\s*\.?\s*$",
    re.I,
)
_I_AM = re.compile(
    r"^\s*i\s+am\s+(?:a\s+|an\s+)?(?P<value>.+?)\s*\.?\s*$",
    re.I,
)


def _schema_role(who: Who) -> str:
    return "user" if who == "user" else "agent"


def _active_attr(engine: CognitiveEngine, who: Who, key: str) -> str:
    schema = engine.identity.schema_concept(_schema_role(who))
    for attr in schema.attributes:
        if attr.active and attr.key == key:
            return str(attr.value)
    return ""


def _canonical_text(who: Who, key: str, value: str) -> str:
    # Emit forms IdentityOrgan / semantic extraction already recognize.
    if key in {"name", "legal_name"}:
        return f"My name is {value}."
    if key == "preferred_name":
        return f"Call me {value}."
    if key == "role":
        return f"I am a {value}." if who == "assistant" else f"I am {value}."
    if key == "location":
        return f"I live in {value}."
    return f"My {key.replace('_', ' ')} is {value}."


def parse_identity_correction(
    text: str, *, who: Who = "user"
) -> dict[str, Any] | None:
    body = (text or "").strip()
    if not body:
        return None
    m = _CALL_ME.match(body)
    if m:
        return {
            "who": who,
            "key": "preferred_name",
            "value": m.group("value").strip().rstrip("."),
            "phrase": "call_me",
        }
    m = _LEGAL_NAME.match(body)
    if m:
        return {
            "who": who,
            "key": "name",
            "value": m.group("value").strip().rstrip("."),
            "phrase": "legal_name",
        }
    if who == "assistant":
        m = _I_AM.match(body)
        if m:
            return {
                "who": who,
                "key": "role",
                "value": m.group("value").strip().rstrip("."),
                "phrase": "role",
            }
    return None


def preview_identity_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str,
    who: Who = "user",
) -> dict[str, Any]:
    """Preview identity attribute impact without writing."""
    key = (key or "").strip().lower().replace(" ", "_")
    value = (value or "").strip()
    if key == "legal_name":
        key = "name"
    previous = _active_attr(engine, who, key)
    # Collision guard: never preview writing user name onto assistant schema
    if who == "assistant" and key in {"name", "preferred_name"}:
        user_name = _active_attr(engine, "user", "name") or _active_attr(
            engine, "user", "preferred_name"
        )
        if user_name and value and value.casefold() == user_name.casefold():
            return {
                "schema": SCHEMA,
                "status": "blocked_collision",
                "reason": "user_assistant_name_collision",
                "who": who,
                "key": key,
                "previous": previous,
                "proposed": value,
                "invents_experiences": False,
                "store_write": False,
            }
    return {
        "schema": SCHEMA,
        "status": "preview",
        "who": who,
        "key": key,
        "previous": previous,
        "proposed": value,
        "would_supersede": bool(previous and value and previous.casefold() != value.casefold()),
        "requires_assent": bool(previous and value and previous.casefold() != value.casefold()),
        "canonical_text": _canonical_text(who, key, value),
        "impact": (
            f"Change {who} {key} from '{previous}' to '{value}'."
            if previous
            else f"Set {who} {key} to '{value}'."
        ),
        "invents_experiences": False,
        "store_write": False,
    }


def propose_identity_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str,
    who: Who = "user",
    reason: str = "identity_correction",
) -> dict[str, Any]:
    if is_read_only():
        return {"status": "read_only_blocked"}
    preview = preview_identity_change(engine, key=key, value=value, who=who)
    if preview.get("status") == "blocked_collision":
        return preview
    schema = engine.identity.schema_concept(_schema_role(who))
    prop = engine.identity.policy.propose(
        schema_id=schema.id,
        attribute_key=preview["key"],
        previous=preview["previous"],
        proposed=preview["proposed"],
        reason=reason,
    )
    prop.metadata["who"] = who
    prop.metadata["canonical_text"] = preview["canonical_text"]
    prop.metadata["impact"] = preview["impact"]
    return {
        "schema": SCHEMA,
        "status": "proposed",
        "proposal": {
            "id": prop.id,
            "who": who,
            "key": prop.attribute_key,
            "previous": prop.previous,
            "proposed": prop.proposed,
            "reason": prop.reason,
            "status": prop.status,
        },
        "preview": preview,
        "invents_experiences": False,
        "store_write": False,
    }


def cancel_identity_change(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    prop = engine.identity.policy.cancel(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending", "cancelled": False}
    return {
        "schema": SCHEMA,
        "status": "cancelled",
        "cancelled": True,
        "proposal_id": proposal_id,
        "invents_experiences": False,
        "store_write": False,
    }


def apply_identity_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str,
    who: Who = "user",
    assent: bool = True,
) -> dict[str, Any]:
    """Trusted-host identity commit. If assent=False, only proposes."""
    preview = preview_identity_change(engine, key=key, value=value, who=who)
    if preview.get("status") == "blocked_collision":
        return preview
    if not assent:
        return propose_identity_change(engine, key=key, value=value, who=who)
    if is_read_only():
        return {"status": "read_only_blocked"}
    exp_before = len(engine.store.experiences)
    speaker = "assistant" if who == "assistant" else "user"
    encoded = engine.encode(
        preview["canonical_text"],
        kind="identity",
        pin=True,
        assent=True,
        speaker=speaker,
        provenance=TRUSTED_USER_STATEMENT,
    )
    after = _active_attr(engine, who, preview["key"])
    return {
        "schema": SCHEMA,
        "status": "applied",
        "who": who,
        "key": preview["key"],
        "previous": preview["previous"],
        "value": after or preview["proposed"],
        "experience_id": encoded.get("experience_id"),
        "experiences_added": len(engine.store.experiences) - exp_before,
        "lineage_preserved": True,
        "invents_experiences": False,
        "user_assistant_isolated": True,
    }


def preview_identity_correction(
    engine: CognitiveEngine, text: str, *, who: Who = "user"
) -> dict[str, Any]:
    parsed = parse_identity_correction(text, who=who)
    if parsed is None:
        return {
            "schema": SCHEMA,
            "status": "unrecognized",
            "invents_experiences": False,
            "store_write": False,
        }
    preview = preview_identity_change(
        engine, key=parsed["key"], value=parsed["value"], who=parsed["who"]
    )
    preview["is_correction"] = True
    preview["phrase"] = parsed["phrase"]
    preview["utterance"] = text
    return preview


def apply_identity_correction(
    engine: CognitiveEngine,
    text: str,
    *,
    who: Who = "user",
    assent: bool = True,
) -> dict[str, Any]:
    preview = preview_identity_correction(engine, text, who=who)
    if preview.get("status") not in {"preview", "blocked_collision"}:
        return preview
    if preview.get("status") == "blocked_collision":
        return preview
    result = apply_identity_change(
        engine,
        key=preview["key"],
        value=preview["proposed"],
        who=preview["who"],
        assent=assent,
    )
    result["is_correction"] = True
    result["explanation"] = preview.get("impact")
    result["phrase"] = preview.get("phrase")
    # Side-channel lineage (Experiences are frozen)
    store = getattr(engine, "_identity_corrections", None)
    if not isinstance(store, dict):
        engine._identity_corrections = {}
        store = engine._identity_corrections
    if result.get("experience_id"):
        store[str(result["experience_id"])] = {
            "identity_correction": True,
            "who": preview["who"],
            "key": preview["key"],
            "corrected_from": preview.get("previous"),
            "corrected_to": preview.get("proposed"),
        }
    result["correction_lineage"] = store.get(str(result.get("experience_id") or ""), {})
    return result


def pending_identity_changes(engine: CognitiveEngine) -> dict[str, Any]:
    with read_only():
        items = [
            {
                "id": p.id,
                "key": p.attribute_key,
                "previous": p.previous,
                "proposed": p.proposed,
                "reason": p.reason,
                "who": (p.metadata or {}).get("who", "user"),
                "status": p.status,
            }
            for p in engine.identity.pending_proposals()
        ]
        return {
            "schema": "acm.identity.pending.v1",
            "pending": items,
            "count": len(items),
            "execution_mode": "read_only",
            "invents_experiences": False,
        }
