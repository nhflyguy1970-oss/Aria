"""Memory Reconciliation artifacts — lineage without history rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReconciliationStatus(StrEnum):
    REINFORCE = "reinforce"
    UNRESOLVED = "unresolved"
    CONTEXT_DEPENDENT = "context_dependent"
    COMPETING = "competing"
    REVISED = "revised"


@dataclass
class ReconciliationRecord:
    id: str
    cue: str
    status: ReconciliationStatus
    subject_ids: list[str]  # concepts / experiences / associations involved
    evidence_ids: list[str]
    conflicting_ids: list[str]
    supporting_ids: list[str]
    confidence_before: float
    confidence_after: float
    summary: str
    created: float
    context_tags: tuple[str, ...] = ()
    factors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": "When memories disagree, how should memory reconcile them?",
            "cue": self.cue,
            "status": self.status.value,
            "subject_ids": list(self.subject_ids),
            "evidence_ids": list(self.evidence_ids),
            "conflicting_ids": list(self.conflicting_ids),
            "supporting_ids": list(self.supporting_ids),
            "confidence_before": round(self.confidence_before, 4),
            "confidence_after": round(self.confidence_after, 4),
            "summary": self.summary,
            "context_tags": list(self.context_tags),
            "factors": list(self.factors),
            "historical_rewrite": False,
            "deleted": False,
            "plans": False,
        }
