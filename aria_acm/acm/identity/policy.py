"""Thin Policy Gate for high-impact identity changes — host-agnostic assent."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4


@dataclass
class IdentityProposal:
    id: str
    schema_id: str
    attribute_key: str
    previous: str
    proposed: str
    reason: str
    created: float = field(default_factory=time)
    status: str = "pending"  # pending | assented | rejected
    metadata: dict[str, Any] = field(default_factory=dict)


class IdentityPolicyGate:
    """Assent required for silent flips of active identity attributes."""

    def __init__(self) -> None:
        self.proposals: dict[str, IdentityProposal] = {}

    def propose(
        self,
        *,
        schema_id: str,
        attribute_key: str,
        previous: str,
        proposed: str,
        reason: str = "high_impact_identity_change",
    ) -> IdentityProposal:
        prop = IdentityProposal(
            id=f"idp_{uuid4().hex[:12]}",
            schema_id=schema_id,
            attribute_key=attribute_key,
            previous=previous,
            proposed=proposed,
            reason=reason,
        )
        self.proposals[prop.id] = prop
        return prop

    def assent(self, proposal_id: str) -> IdentityProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "assented"
        return prop

    def reject(self, proposal_id: str) -> IdentityProposal | None:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "pending":
            return None
        prop.status = "rejected"
        return prop

    def pending(self) -> list[IdentityProposal]:
        return [p for p in self.proposals.values() if p.status == "pending"]
