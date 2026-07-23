"""Preference editing UX (B11) — preview / propose / assent over encode.

Never mutates Experiences in place. Commits always birth new Experiences via
``encode()`` (or explicit deactivate with evidence Experience). No store CRUD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Literal, TYPE_CHECKING
from uuid import uuid4

from acm.authority.mode import is_read_only, read_only
from acm.provenance import TRUSTED_USER_STATEMENT
from acm.types import ConceptRole

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.preference.edit.v1"
Op = Literal["set", "replace", "remove"]


@dataclass
class PreferenceProposal:
    id: str
    key: str
    previous: str
    proposed: str
    op: str
    reason: str = "preference_edit"
    created: float = field(default_factory=time)
    status: str = "pending"  # pending | assented | rejected | cancelled
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "previous": self.previous,
            "proposed": self.proposed,
            "op": self.op,
            "reason": self.reason,
            "status": self.status,
            "created": self.created,
        }


class PreferencePolicyGate:
    """Assent gate for explicit preference edits (host UX)."""

    def __init__(self) -> None:
        self.proposals: dict[str, PreferenceProposal] = {}

    def propose(
        self,
        *,
        key: str,
        previous: str,
        proposed: str,
        op: str,
        reason: str = "preference_edit",
    ) -> PreferenceProposal:
        prop = PreferenceProposal(
            id=f"prp_{uuid4().hex[:12]}",
            key=key,
            previous=previous,
            proposed=proposed,
            op=op,
            reason=reason,
        )
        self.proposals[prop.id] = prop
        return prop

    def assent(self, proposal_id: str) -> PreferenceProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "assented"
        return prop

    def reject(self, proposal_id: str) -> PreferenceProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "rejected"
        return prop

    def cancel(self, proposal_id: str) -> PreferenceProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "cancelled"
        return prop

    def pending(self) -> list[PreferenceProposal]:
        return [p for p in self.proposals.values() if p.status == "pending"]


def _normalize_key(key: str) -> str:
    k = " ".join((key or "").strip().lower().replace("-", "_").split())
    k = k.replace(" ", "_")
    if not k:
        return ""
    if k.startswith("favorite_") or k.startswith("prefer_"):
        return k
    # "color" → favorite_color
    if not k.startswith("favorite"):
        return f"favorite_{k}"
    return k


def _active_preference_attrs(engine: CognitiveEngine) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in engine.store.concepts.values():
        if not c.active:
            continue
        if c.role != ConceptRole.PREFERENCE and not any(
            a.key.startswith(("favorite_", "prefer_")) and a.active for a in c.attributes
        ):
            continue
        for attr in c.attributes:
            if not attr.active:
                continue
            if not (
                attr.key.startswith("favorite_")
                or attr.key.startswith("prefer_")
                or c.role == ConceptRole.PREFERENCE
            ):
                continue
            out.append(
                {
                    "concept_id": c.id,
                    "key": attr.key,
                    "value": attr.value,
                    "confidence": float(attr.confidence),
                    "evidence_ids": list(getattr(attr, "evidence_ids", ()) or [])[:12],
                }
            )
    out.sort(key=lambda x: x["key"])
    return out


def _find_active(engine: CognitiveEngine, key: str) -> dict[str, Any] | None:
    key = _normalize_key(key)
    for item in _active_preference_attrs(engine):
        if item["key"] == key:
            return item
    return None


def _canonical_text(key: str, value: str, op: str) -> str:
    label = key
    if label.startswith("favorite_"):
        noun = label[len("favorite_") :].replace("_", " ")
        if op == "remove":
            return f"I no longer have a favorite {noun}."
        return f"My favorite {noun} is {value}."
    if label.startswith("prefer_"):
        domain = label[len("prefer_") :].replace("_", " ")
        if op == "remove":
            return f"I no longer prefer anything for {domain}."
        return f"I prefer {value} for {domain}."
    if op == "remove":
        return f"Remove preference {label}."
    return f"My preference for {label} is {value}."


def inspect_preferences(engine: CognitiveEngine, *, key_prefix: str = "") -> dict[str, Any]:
    """Read-only list of active preferences."""
    with read_only():
        items = _active_preference_attrs(engine)
        if key_prefix:
            pref = key_prefix.strip().lower()
            items = [i for i in items if i["key"].startswith(pref)]
        return {
            "schema": "acm.inspect.preferences.v1",
            "preferences": items,
            "count": len(items),
            "execution_mode": "read_only",
            "fingerprint": engine.store_fingerprint(),
            "invents_experiences": False,
        }


def inspect_preference(engine: CognitiveEngine, key: str) -> dict[str, Any]:
    """Read-only single preference + version lineage on the concept attribute."""
    key = _normalize_key(key)
    with read_only():
        active = _find_active(engine, key)
        versions: list[dict[str, Any]] = []
        for c in engine.store.concepts.values():
            for attr in c.attributes:
                if attr.key == key:
                    versions.append(
                        {
                            "value": attr.value,
                            "active": bool(attr.active),
                            "confidence": float(attr.confidence),
                            "concept_id": c.id,
                        }
                    )
        return {
            "schema": "acm.inspect.preference.v1",
            "key": key,
            "known": active is not None,
            "active": active,
            "versions": versions[-12:],
            "execution_mode": "read_only",
            "fingerprint": engine.store_fingerprint(),
            "invents_experiences": False,
        }


def preview_preference_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str = "",
    op: Op = "set",
) -> dict[str, Any]:
    """Preview old→new without writing."""
    key = _normalize_key(key)
    current = _find_active(engine, key)
    previous = str((current or {}).get("value") or "")
    proposed = "" if op == "remove" else str(value or "").strip()
    effective_op = op
    if op == "set" and previous and proposed and previous != proposed:
        effective_op = "replace"
    return {
        "schema": SCHEMA,
        "status": "preview",
        "key": key,
        "op": effective_op,
        "previous": previous,
        "proposed": proposed,
        "would_supersede": bool(previous and proposed and previous != proposed),
        "canonical_text": _canonical_text(key, proposed or previous, effective_op),
        "invents_experiences": False,
        "store_write": False,
    }


def propose_preference_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str = "",
    op: Op = "set",
    reason: str = "preference_edit",
) -> dict[str, Any]:
    if is_read_only():
        return {"status": "read_only_blocked"}
    preview = preview_preference_change(engine, key=key, value=value, op=op)
    gate: PreferencePolicyGate = engine._preference_gate
    prop = gate.propose(
        key=preview["key"],
        previous=preview["previous"],
        proposed=preview["proposed"],
        op=preview["op"],
        reason=reason,
    )
    prop.metadata["canonical_text"] = preview["canonical_text"]
    return {
        "schema": SCHEMA,
        "status": "proposed",
        "proposal": prop.to_public(),
        "preview": preview,
        "invents_experiences": False,
    }


def _apply_commit(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str,
    op: str,
    canonical_text: str,
) -> dict[str, Any]:
    from acm.authority.mode import is_read_only as _ro

    if _ro():
        return {"status": "read_only_blocked"}
    key = _normalize_key(key)
    exp_before = len(engine.store.experiences)
    encoded = engine.encode(
        canonical_text,
        pin=True,
        provenance=TRUSTED_USER_STATEMENT,
        kind="preference",
    )
    if op == "remove":
        # Deactivate living attribute; Experience already records the removal intent.
        for c in engine.store.concepts.values():
            for attr in c.attributes:
                if attr.key == key and attr.active:
                    attr.active = False
                    engine.validation.record_reconsolidation(
                        kind="preference_remove",
                        attribute_key=key,
                        concept_id=c.id,
                        experience_id=encoded.get("experience_id"),
                    )
    active = _find_active(engine, key)
    return {
        "schema": SCHEMA,
        "status": "applied",
        "key": key,
        "op": op,
        "active": active,
        "experience_id": encoded.get("experience_id"),
        "experiences_added": len(engine.store.experiences) - exp_before,
        "invents_experiences": False,  # Experience is host-authorized encode, not invented
        "lineage_preserved": True,
    }


def assent_preference_change(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    gate: PreferencePolicyGate = engine._preference_gate
    prop = gate.assent(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending"}
    text = str(prop.metadata.get("canonical_text") or _canonical_text(prop.key, prop.proposed, prop.op))
    result = _apply_commit(
        engine,
        key=prop.key,
        value=prop.proposed,
        op=prop.op,
        canonical_text=text,
    )
    result["proposal"] = prop.to_public()
    return result


def reject_preference_change(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    gate: PreferencePolicyGate = engine._preference_gate
    prop = gate.reject(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending"}
    return {
        "status": "rejected",
        "proposal": prop.to_public(),
        "invents_experiences": False,
        "store_write": False,
    }


def cancel_preference_change(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    gate: PreferencePolicyGate = engine._preference_gate
    prop = gate.cancel(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending"}
    return {
        "status": "cancelled",
        "proposal": prop.to_public(),
        "invents_experiences": False,
        "store_write": False,
    }


def apply_preference_change(
    engine: CognitiveEngine,
    *,
    key: str,
    value: str = "",
    op: Op = "set",
    assent: bool = True,
) -> dict[str, Any]:
    """Trusted-host commit. If assent=False, only proposes."""
    if not assent:
        return propose_preference_change(engine, key=key, value=value, op=op)
    preview = preview_preference_change(engine, key=key, value=value, op=op)
    return _apply_commit(
        engine,
        key=preview["key"],
        value=preview["proposed"],
        op=preview["op"],
        canonical_text=preview["canonical_text"],
    )
