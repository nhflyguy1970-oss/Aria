"""Prune / forget / erase assent UX (B36).

Soft forget cools accessibility and deactivates living attributes.
Legal erase additionally audits envelope purge requests.
Experiences are never physically deleted (P17 / Memory Authority).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import time
from typing import Any, Literal, TYPE_CHECKING
from uuid import uuid4

from acm.authority.mode import is_read_only, read_only
from acm.provenance import TRUSTED_USER_STATEMENT

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.erase.governance.v1"
Op = Literal["soft_forget", "prune", "legal_erase"]

_FORGET = re.compile(
    r"^\s*(?:please\s+)?(?:forget|stop\s+remembering)\s+(?:my\s+)?(?P<target>.+?)\s*\.?\s*$",
    re.I,
)
_ERASE = re.compile(
    r"^\s*(?:please\s+)?(?:erase|delete|purge)\s+(?:my\s+)?(?P<target>.+?)\s*\.?\s*$",
    re.I,
)
_PRUNE = re.compile(
    r"^\s*(?:please\s+)?prune\s+(?:my\s+)?(?P<target>.+?)\s*\.?\s*$",
    re.I,
)

_TARGET_ALIASES = {
    "old address": "location",
    "address": "location",
    "location": "location",
    "where i live": "location",
    "name": "name",
    "legal name": "name",
    "preferred name": "preferred_name",
    "favorite color": "favorite_color",
    "favourite color": "favorite_color",
    "favorite food": "favorite_food",
    "favourite food": "favorite_food",
}


@dataclass
class EraseProposal:
    id: str
    op: str
    target_key: str
    target_label: str
    impact: str
    concept_ids: list[str] = field(default_factory=list)
    attribute_keys: list[str] = field(default_factory=list)
    envelope_ids: list[str] = field(default_factory=list)
    identity_protected: bool = False
    created: float = field(default_factory=time)
    status: str = "pending"  # pending | assented | rejected | cancelled
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "op": self.op,
            "target_key": self.target_key,
            "target_label": self.target_label,
            "impact": self.impact,
            "concept_ids": list(self.concept_ids),
            "attribute_keys": list(self.attribute_keys),
            "envelope_ids": list(self.envelope_ids),
            "identity_protected": self.identity_protected,
            "status": self.status,
            "created": self.created,
        }


class ErasePolicyGate:
    def __init__(self) -> None:
        self.proposals: dict[str, EraseProposal] = {}

    def propose(self, **kwargs: Any) -> EraseProposal:
        prop = EraseProposal(id=f"erp_{uuid4().hex[:12]}", **kwargs)
        self.proposals[prop.id] = prop
        return prop

    def assent(self, proposal_id: str) -> EraseProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "assented"
        return prop

    def reject(self, proposal_id: str) -> EraseProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "rejected"
        return prop

    def cancel(self, proposal_id: str) -> EraseProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "cancelled"
        return prop

    def pending(self) -> list[EraseProposal]:
        return [p for p in self.proposals.values() if p.status == "pending"]


def _gate(engine: CognitiveEngine) -> ErasePolicyGate:
    gate = getattr(engine, "_erase_gate", None)
    if not isinstance(gate, ErasePolicyGate):
        engine._erase_gate = ErasePolicyGate()
        gate = engine._erase_gate
    return gate


def _normalize_target(raw: str) -> tuple[str, str]:
    body = (raw or "").strip().rstrip(".").lower()
    body = re.sub(r"^(?:the\s+|an?\s+)", "", body)
    key = _TARGET_ALIASES.get(body, body.replace(" ", "_"))
    return key, body


def parse_erase_request(text: str) -> dict[str, Any] | None:
    body = (text or "").strip()
    if not body:
        return None
    m = _ERASE.match(body)
    if m:
        key, label = _normalize_target(m.group("target"))
        return {"op": "legal_erase", "target_key": key, "target_label": label, "utterance": body}
    m = _PRUNE.match(body)
    if m:
        key, label = _normalize_target(m.group("target"))
        return {"op": "prune", "target_key": key, "target_label": label, "utterance": body}
    m = _FORGET.match(body)
    if m:
        key, label = _normalize_target(m.group("target"))
        return {"op": "soft_forget", "target_key": key, "target_label": label, "utterance": body}
    return None


def _collect_impact(
    engine: CognitiveEngine, *, target_key: str, op: Op
) -> dict[str, Any]:
    concept_ids: list[str] = []
    attribute_keys: list[str] = []
    envelope_ids: list[str] = []
    identity_protected = target_key in {"name", "preferred_name"}
    living: list[str] = []

    user = engine.identity.schema_concept("user")
    for attr in user.attributes:
        if not attr.active:
            continue
        if attr.key == target_key or (
            target_key.startswith("favorite_") and attr.key == target_key
        ):
            attribute_keys.append(attr.key)
            living.append(f"user.{attr.key}={attr.value}")
            for eid in attr.evidence_ids or []:
                exp = engine.store.experiences.get(eid)
                if exp is not None:
                    envelope_ids.extend(list(exp.envelope_ids or ()))

    # Preference-style concepts / experiences
    for concept in engine.store.concepts.values():
        if not concept.active:
            continue
        labels = " ".join(concept.labels).lower()
        if target_key.replace("_", " ") in labels or target_key in labels:
            if concept.identity and identity_protected:
                continue
            concept_ids.append(concept.id)
            living.append(f"concept:{concept.labels[0] if concept.labels else concept.id}")

    for exp in engine.store.experiences.values():
        summary = (exp.summary or "").lower()
        needle = target_key.replace("_", " ")
        if needle in summary or target_key in summary:
            envelope_ids.extend(list(exp.envelope_ids or ()))

    envelope_ids = list(dict.fromkeys(envelope_ids))
    concept_ids = list(dict.fromkeys(concept_ids))

    if op == "soft_forget":
        impact = (
            f"Soft-forget '{target_key}': deactivate living attributes "
            f"({', '.join(attribute_keys) or 'none'}); cool related concepts; "
            "Experiences remain immutable."
        )
    elif op == "prune":
        impact = (
            f"Mark prune-eligible for '{target_key}' concepts "
            f"({len(concept_ids)}); never auto-delete."
        )
    else:
        impact = (
            f"Legal-erase request for '{target_key}': soft-forget living memory, "
            f"audit purge of {len(envelope_ids)} envelope(s); Experiences stay."
        )
    return {
        "concept_ids": concept_ids,
        "attribute_keys": attribute_keys,
        "envelope_ids": envelope_ids,
        "identity_protected": identity_protected,
        "living": living,
        "impact": impact,
        "experiences_deleted": False,
    }


def preview_erase_request(
    engine: CognitiveEngine, text: str
) -> dict[str, Any]:
    parsed = parse_erase_request(text)
    if parsed is None:
        return {
            "schema": SCHEMA,
            "status": "unrecognized",
            "invents_experiences": False,
            "store_write": False,
            "experiences_deleted": False,
        }
    impact = _collect_impact(
        engine, target_key=parsed["target_key"], op=parsed["op"]  # type: ignore[arg-type]
    )
    return {
        "schema": SCHEMA,
        "status": "preview",
        "op": parsed["op"],
        "target_key": parsed["target_key"],
        "target_label": parsed["target_label"],
        "utterance": parsed["utterance"],
        **impact,
        "requires_assent": True,
        "invents_experiences": False,
        "store_write": False,
    }


def propose_erase_request(
    engine: CognitiveEngine, text: str
) -> dict[str, Any]:
    if is_read_only():
        return {"status": "read_only_blocked"}
    preview = preview_erase_request(engine, text)
    if preview.get("status") != "preview":
        return preview
    # Identity soft-forget of name blocked — redirect to identity correction
    if preview["op"] == "soft_forget" and preview.get("identity_protected"):
        return {
            "schema": SCHEMA,
            "status": "blocked_identity_protection",
            "reason": "use_identity_correction",
            "hint": "Use apply_identity_correction / propose_identity_change for names.",
            "preview": preview,
            "invents_experiences": False,
            "experiences_deleted": False,
        }
    prop = _gate(engine).propose(
        op=preview["op"],
        target_key=preview["target_key"],
        target_label=preview["target_label"],
        impact=preview["impact"],
        concept_ids=list(preview.get("concept_ids") or []),
        attribute_keys=list(preview.get("attribute_keys") or []),
        envelope_ids=list(preview.get("envelope_ids") or []),
        identity_protected=bool(preview.get("identity_protected")),
        metadata={"utterance": preview.get("utterance")},
    )
    return {
        "schema": SCHEMA,
        "status": "proposed",
        "proposal": prop.to_public(),
        "preview": preview,
        "invents_experiences": False,
        "store_write": False,
        "experiences_deleted": False,
    }


def cancel_erase_request(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    prop = _gate(engine).cancel(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending", "cancelled": False}
    return {
        "schema": SCHEMA,
        "status": "cancelled",
        "cancelled": True,
        "proposal_id": proposal_id,
        "experiences_deleted": False,
    }


def reject_erase_request(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    prop = _gate(engine).reject(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending", "rejected": False}
    return {
        "schema": SCHEMA,
        "status": "rejected",
        "rejected": True,
        "proposal_id": proposal_id,
        "experiences_deleted": False,
    }


def assent_erase_request(engine: CognitiveEngine, proposal_id: str) -> dict[str, Any]:
    if is_read_only():
        return {"status": "read_only_blocked"}
    prop = _gate(engine).assent(proposal_id)
    if prop is None:
        return {"status": "missing_or_not_pending", "assented": False}
    return _apply_proposal(engine, prop)


def apply_erase_request(
    engine: CognitiveEngine, text: str, *, assent: bool = True
) -> dict[str, Any]:
    """Trusted-host path: propose+assent when assent=True."""
    proposed = propose_erase_request(engine, text)
    if proposed.get("status") != "proposed":
        return proposed
    if not assent:
        return proposed
    return assent_erase_request(engine, proposed["proposal"]["id"])


def _apply_proposal(engine: CognitiveEngine, prop: EraseProposal) -> dict[str, Any]:
    before_exp = len(engine.store.experiences)
    deactivated: list[str] = []
    cooled: list[str] = []
    pruned: list[str] = []
    envelopes_purged: list[str] = []

    # Deactivate living user attributes (soft forget + legal erase)
    if prop.op in {"soft_forget", "legal_erase"}:
        user = engine.identity.schema_concept("user")
        for attr in user.attributes:
            if attr.active and attr.key in prop.attribute_keys:
                attr.active = False
                deactivated.append(attr.key)
        for cid in prop.concept_ids:
            concept = engine.store.concepts.get(cid)
            if concept is None or concept.identity:
                continue
            # Cool hard under explicit assent
            ev = engine.forgetting.cool(cid, source="erase_assent", steps=3, force=True)
            if ev is not None:
                cooled.append(cid)

    if prop.op == "prune":
        for cid in prop.concept_ids:
            out = engine.forgetting.mark_prune_eligible(cid)
            if out.get("status") == "proposed":
                pruned.append(cid)
            else:
                # Force archive-ish cool then mark
                engine.forgetting.cool(cid, source="erase_assent", steps=4, force=True)
                out2 = engine.forgetting.mark_prune_eligible(cid)
                if out2.get("status") == "proposed":
                    pruned.append(cid)

    if prop.op == "legal_erase":
        for eid in prop.envelope_ids:
            if eid in engine.store.envelopes:
                del engine.store.envelopes[eid]
                envelopes_purged.append(eid)

    # Audit Experience (governance lineage — not a silent delete)
    audit_text = (
        f"User assented {prop.op} for '{prop.target_label}' "
        f"(attributes={deactivated or prop.attribute_keys}; "
        f"experiences_deleted=false)."
    )
    encoded = engine.encode(
        audit_text,
        kind="governance",
        pin=True,
        assent=True,
        provenance=TRUSTED_USER_STATEMENT,
    )

    audits = getattr(engine, "_erase_audits", None)
    if not isinstance(audits, dict):
        engine._erase_audits = {}
        audits = engine._erase_audits
    audits[str(encoded.get("experience_id") or prop.id)] = {
        "op": prop.op,
        "target_key": prop.target_key,
        "deactivated": deactivated,
        "cooled": cooled,
        "pruned": pruned,
        "envelopes_purged": envelopes_purged,
        "experiences_deleted": False,
        "proposal_id": prop.id,
    }

    return {
        "schema": SCHEMA,
        "status": "applied",
        "assented": True,
        "proposal": prop.to_public(),
        "deactivated_attributes": deactivated,
        "cooled_concepts": cooled,
        "pruned_concepts": pruned,
        "envelopes_purged": envelopes_purged,
        "audit_experience_id": encoded.get("experience_id"),
        "experiences_added": len(engine.store.experiences) - before_exp,
        "experiences_deleted": False,
        "invents_experiences": False,
        "lineage_preserved": True,
    }


def pending_erase_requests(engine: CognitiveEngine) -> dict[str, Any]:
    with read_only():
        items = [p.to_public() for p in _gate(engine).pending()]
        return {
            "schema": "acm.erase.pending.v1",
            "pending": items,
            "count": len(items),
            "execution_mode": "read_only",
            "experiences_deleted": False,
        }
