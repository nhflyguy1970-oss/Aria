"""The result of routing: what was chosen, what was not, and why."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

POLICY_VERSION = "1.0.0"

# Selection methods.
PREFERRED = "preferred_model"
SCORED = "highest_scored"
FALLBACK = "fallback_after_failure"
NONE_AVAILABLE = "no_compatible_model"


@dataclass
class Candidate:
    """One model considered for a request, with its verdict."""

    model_id: str
    provider: str
    score: float = 0.0
    accepted: bool = True
    rejection_reason: str = ""
    score_breakdown: dict[str, float] = field(default_factory=dict)
    capability_evidence: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "score": round(self.score, 4),
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "score_breakdown": {k: round(v, 4) for k, v in self.score_breakdown.items()},
            "capability_evidence": dict(self.capability_evidence),
        }


@dataclass
class RoutingDecision:
    """An explainable answer to 'which model, and why that one?'"""

    request: dict[str, Any]
    selected_model: str = ""
    provider: str = ""
    selection_method: str = NONE_AVAILABLE
    score: float = 0.0
    preferred_model: str = ""
    preferred_model_used: bool = False
    preferred_model_status: str = "not_requested"
    fallback_active: bool = False
    fallback_count: int = 0
    fallback_chain: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    capability_evidence: dict[str, str] = field(default_factory=dict)
    reason: str = ""
    policy_version: str = POLICY_VERSION

    @property
    def ok(self) -> bool:
        return bool(self.selected_model)

    def accepted(self) -> list[Candidate]:
        return [c for c in self.candidates if c.accepted]

    def rejected(self) -> list[Candidate]:
        return [c for c in self.candidates if not c.accepted]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "request": dict(self.request),
            "selected_model": self.selected_model,
            "provider": self.provider,
            "selection_method": self.selection_method,
            "score": round(self.score, 4),
            "preferred_model": self.preferred_model,
            "preferred_model_used": self.preferred_model_used,
            "preferred_model_status": self.preferred_model_status,
            "fallback_active": self.fallback_active,
            "fallback_count": self.fallback_count,
            "fallback_chain": list(self.fallback_chain),
            "candidates": [c.to_dict() for c in self.candidates],
            "accepted_count": len(self.accepted()),
            "rejected_count": len(self.rejected()),
            "capability_evidence": dict(self.capability_evidence),
            "reason": self.reason,
            "policy_version": self.policy_version,
        }
