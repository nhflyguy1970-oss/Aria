"""Provenance records — explainable lineage without fabrication."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from time import time
from typing import Any

from acm.types import new_id


class ProvenanceSource(StrEnum):
    TOLD = "told"
    PERCEIVED = "perceived"
    INFERRED = "inferred"
    RECONSTRUCTED = "reconstructed"
    LEGACY_IMPORT = "legacy_import"
    LEARNED = "learned"
    REFLECTIVE = "reflective"
    RECONCILED = "reconciled"
    SIMULATED = "simulated"  # contributor only — never historical
    ANALOGICAL = "analogical"
    ENCODE = "encode"
    UNKNOWN = "unknown"


@dataclass
class ProvenanceRecord:
    """Answers: Where did this artifact originate? What contributed?"""

    id: str
    artifact_kind: str
    artifact_id: str
    origin: ProvenanceSource = ProvenanceSource.UNKNOWN
    source_actor: str = ""
    host_operation: str = ""
    message_role: str = ""
    eligibility_reason: str = ""
    contributor_ids: list[str] = field(default_factory=list)
    experience_ids: list[str] = field(default_factory=list)
    learning_ids: list[str] = field(default_factory=list)
    reflection_ids: list[str] = field(default_factory=list)
    reconciliation_ids: list[str] = field(default_factory=list)
    simulation_ids: list[str] = field(default_factory=list)
    analogy_ids: list[str] = field(default_factory=list)
    confidence_event_ids: list[str] = field(default_factory=list)
    parent_provenance_ids: list[str] = field(default_factory=list)
    explain: str = ""
    created: float = field(default_factory=time)
    fabricated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "artifact_kind": self.artifact_kind,
            "artifact_id": self.artifact_id,
            "origin": self.origin.value,
            "source_actor": self.source_actor,
            "host_operation": self.host_operation,
            "message_role": self.message_role,
            "eligibility_reason": self.eligibility_reason,
            "contributor_ids": list(self.contributor_ids),
            "experience_ids": list(self.experience_ids),
            "learning_ids": list(self.learning_ids),
            "reflection_ids": list(self.reflection_ids),
            "reconciliation_ids": list(self.reconciliation_ids),
            "simulation_ids": list(self.simulation_ids),
            "analogy_ids": list(self.analogy_ids),
            "confidence_event_ids": list(self.confidence_event_ids),
            "parent_provenance_ids": list(self.parent_provenance_ids),
            "explain": self.explain,
            "created": self.created,
            "fabricated": False,
        }

    @classmethod
    def from_public(cls, d: dict[str, Any]) -> ProvenanceRecord:
        origin_raw = d.get("origin", "unknown")
        try:
            origin = ProvenanceSource(origin_raw)
        except ValueError:
            origin = ProvenanceSource.UNKNOWN
        return cls(
            id=str(d.get("id") or new_id("prov")),
            artifact_kind=str(d.get("artifact_kind", "")),
            artifact_id=str(d.get("artifact_id", "")),
            origin=origin,
            source_actor=str(d.get("source_actor", "")),
            host_operation=str(d.get("host_operation", "")),
            message_role=str(d.get("message_role", "")),
            eligibility_reason=str(d.get("eligibility_reason", "")),
            contributor_ids=list(d.get("contributor_ids") or []),
            experience_ids=list(d.get("experience_ids") or []),
            learning_ids=list(d.get("learning_ids") or []),
            reflection_ids=list(d.get("reflection_ids") or []),
            reconciliation_ids=list(d.get("reconciliation_ids") or []),
            simulation_ids=list(d.get("simulation_ids") or []),
            analogy_ids=list(d.get("analogy_ids") or []),
            confidence_event_ids=list(d.get("confidence_event_ids") or []),
            parent_provenance_ids=list(d.get("parent_provenance_ids") or []),
            explain=str(d.get("explain", "")),
            created=float(d.get("created", time())),
            fabricated=False,
            metadata=dict(d.get("metadata") or {}),
        )


def stamp_provenance(
    store: Any,
    *,
    artifact_kind: str,
    artifact_id: str,
    origin: ProvenanceSource | str,
    experience_ids: list[str] | None = None,
    contributor_ids: list[str] | None = None,
    learning_ids: list[str] | None = None,
    reflection_ids: list[str] | None = None,
    reconciliation_ids: list[str] | None = None,
    simulation_ids: list[str] | None = None,
    analogy_ids: list[str] | None = None,
    confidence_event_ids: list[str] | None = None,
    parent_provenance_ids: list[str] | None = None,
    explain: str = "",
    source_actor: str = "",
    host_operation: str = "",
    message_role: str = "",
    eligibility_reason: str = "",
) -> ProvenanceRecord:
    """Record only observed contributors — never invent links."""
    if isinstance(origin, str):
        try:
            origin_e = ProvenanceSource(origin)
        except ValueError:
            origin_e = ProvenanceSource.UNKNOWN
    else:
        origin_e = origin
    record = ProvenanceRecord(
        id=new_id("prov"),
        artifact_kind=artifact_kind,
        artifact_id=artifact_id,
        origin=origin_e,
        source_actor=source_actor,
        host_operation=host_operation,
        message_role=message_role,
        eligibility_reason=eligibility_reason,
        contributor_ids=list(contributor_ids or []),
        experience_ids=list(experience_ids or []),
        learning_ids=list(learning_ids or []),
        reflection_ids=list(reflection_ids or []),
        reconciliation_ids=list(reconciliation_ids or []),
        simulation_ids=list(simulation_ids or []),
        analogy_ids=list(analogy_ids or []),
        confidence_event_ids=list(confidence_event_ids or []),
        parent_provenance_ids=list(parent_provenance_ids or []),
        explain=explain or f"{artifact_kind}:{artifact_id} origin={origin_e.value}",
        fabricated=False,
    )
    store.provenance[record.id] = record
    return record
