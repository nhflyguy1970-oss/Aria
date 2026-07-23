"""User-assisted conflict resolution (B13).

Ask the user which competing recollection remains active without silently
discarding evidence. Commits via B11 preference apply / encode; Experiences
stay immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from acm.authority.mode import is_read_only
from acm.authority.preference_edit import (
    _find_active,
    _normalize_key,
    apply_preference_change,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.conflict.resolution.v1"


@dataclass
class ConflictResolutionSession:
    id: str
    cue: str
    key: str
    options: list[str]
    status: str = "open"  # open | confirmed | rejected | abstained
    chosen: str = ""
    created: float = field(default_factory=time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cue": self.cue,
            "key": self.key,
            "options": list(self.options),
            "status": self.status,
            "chosen": self.chosen,
            "created": self.created,
            "prompt": (
                f"I have {' and '.join(repr(o) for o in self.options)}. "
                "Which is current?"
                if self.options
                else "No competing values found."
            ),
        }


class ConflictResolutionGate:
    def __init__(self) -> None:
        self.sessions: dict[str, ConflictResolutionSession] = {}

    def open_session(
        self, *, cue: str, key: str, options: list[str]
    ) -> ConflictResolutionSession:
        sess = ConflictResolutionSession(
            id=f"crs_{uuid4().hex[:12]}",
            cue=cue,
            key=key,
            options=[str(o) for o in options if str(o).strip()],
        )
        self.sessions[sess.id] = sess
        return sess


def _extract_option_values(competing: list[Any]) -> list[str]:
    values: list[str] = []
    for item in competing:
        if isinstance(item, dict):
            for k in ("value", "memory", "answer", "label", "text"):
                if item.get(k):
                    values.append(str(item[k]).strip())
                    break
            else:
                values.append(str(item))
        else:
            values.append(str(item).strip())
    # de-dupe preserve order
    out: list[str] = []
    seen: set[str] = set()
    for v in values:
        low = v.casefold()
        if not v or low in seen:
            continue
        seen.add(low)
        out.append(v)
    return out[:8]


def open_conflict_resolution(
    engine: CognitiveEngine,
    cue: str,
    *,
    key: str = "",
) -> dict[str, Any]:
    """Open an interactive conflict session from inspect_conflict competing set."""
    view = engine.inspect_conflict(cue)
    competing = list(view.get("competing") or [])
    options = _extract_option_values(competing)
    pref_key = _normalize_key(key) if key else ""
    if not pref_key:
        # Heuristic: favorite_color from cue
        low = cue.lower()
        if "color" in low:
            pref_key = "favorite_color"
        elif "tea" in low:
            pref_key = "favorite_tea"
        elif "food" in low:
            pref_key = "favorite_food"
        else:
            pref_key = "favorite_color"
    # Include currently active value if missing
    active = _find_active(engine, pref_key)
    if active and active["value"] not in options:
        options.insert(0, str(active["value"]))
    # Also include retired versions as options when only one active
    one = engine.inspect_preference(pref_key)
    for ver in one.get("versions") or []:
        val = str(ver.get("value") or "")
        if val and val not in options:
            options.append(val)
    options = options[:8]
    if len(options) < 2:
        return {
            "schema": SCHEMA,
            "status": "no_conflict",
            "options": options,
            "key": pref_key,
            "invents_experiences": False,
        }
    gate: ConflictResolutionGate = engine._conflict_gate
    sess = gate.open_session(cue=cue, key=pref_key, options=options)
    return {
        "schema": SCHEMA,
        "status": "open",
        "session": sess.to_public(),
        "inspect": {
            "ambiguous": view.get("ambiguous"),
            "competing_count": len(competing),
        },
        "invents_experiences": False,
        "store_write": False,
    }


def confirm_conflict_resolution(
    engine: CognitiveEngine,
    session_id: str,
    chosen: str,
) -> dict[str, Any]:
    """User confirms the current value — apply via preference edit; retain lineage."""
    if is_read_only():
        return {"status": "read_only_blocked"}
    gate: ConflictResolutionGate = engine._conflict_gate
    sess = gate.sessions.get(session_id)
    if sess is None or sess.status != "open":
        return {"status": "missing_or_not_open"}
    choice = str(chosen or "").strip()
    if not choice:
        return {"status": "empty_choice"}
    # Allow choosing an option case-insensitively
    matched = next((o for o in sess.options if o.casefold() == choice.casefold()), None)
    if matched is None:
        return {
            "status": "unknown_option",
            "options": list(sess.options),
            "invents_experiences": False,
        }
    applied = apply_preference_change(
        engine, key=sess.key, value=matched, op="replace", assent=True
    )
    sess.status = "confirmed"
    sess.chosen = matched
    sess.metadata["experience_id"] = applied.get("experience_id")
    return {
        "schema": SCHEMA,
        "status": "confirmed",
        "session": sess.to_public(),
        "applied": applied,
        "historical_rewrite": False,
        "invents_experiences": False,
        "lineage_preserved": True,
    }


def reject_conflict_resolution(engine: CognitiveEngine, session_id: str) -> dict[str, Any]:
    gate: ConflictResolutionGate = engine._conflict_gate
    sess = gate.sessions.get(session_id)
    if sess is None or sess.status != "open":
        return {"status": "missing_or_not_open"}
    sess.status = "rejected"
    return {
        "schema": SCHEMA,
        "status": "rejected",
        "session": sess.to_public(),
        "invents_experiences": False,
        "store_write": False,
    }


def abstain_conflict_resolution(engine: CognitiveEngine, session_id: str) -> dict[str, Any]:
    gate: ConflictResolutionGate = engine._conflict_gate
    sess = gate.sessions.get(session_id)
    if sess is None or sess.status != "open":
        return {"status": "missing_or_not_open"}
    sess.status = "abstained"
    return {
        "schema": SCHEMA,
        "status": "abstained",
        "session": sess.to_public(),
        "invents_experiences": False,
        "store_write": False,
        "note": "Left competing recollections unchanged.",
    }
