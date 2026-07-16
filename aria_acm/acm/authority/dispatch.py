"""Cognitive Dispatch Engine — end-to-end cognitive execution (D040).

classify → ownership → dispatch → organ(s) → reconstruction → CognitiveMemoryResult

A cognitive request SHALL terminate ONLY at a cognitive organ. Implementation
infrastructure is substrate support only — never the cognitive endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from acm.authority.handlers import (
    COGNITIVE_TERMINALS,
    FORBIDDEN_TERMINALS,
    CognitiveOrganHandlers,
    OrganContribution,
    sanitize_cognitive_text,
)
from acm.authority.routing import CognitiveOwnership, CognitiveRoutingEngine, RoutingDecision
from acm.authority.taxonomy import (
    ORGAN_NONE,
    CognitiveIntent,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine


@dataclass
class DispatchRecord:
    """Diagnostics for one completed cognitive dispatch."""

    intent: str
    primary_organ: str
    supporting_organs: list[str]
    dispatch_path: list[str] = field(default_factory=list)
    reconstruction_path: list[str] = field(default_factory=list)
    terminated_at: str = ""
    contributions: list[dict[str, Any]] = field(default_factory=list)
    infrastructure_role: str = "substrate_only"
    uncertain: bool = False
    schema: str = "cognitive_dispatch.v1"

    def to_public(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "primary_organ": self.primary_organ,
            "supporting_organs": list(self.supporting_organs),
            "dispatch_path": list(self.dispatch_path),
            "reconstruction_path": list(self.reconstruction_path),
            "terminated_at": self.terminated_at,
            "contributions": list(self.contributions),
            "infrastructure_role": self.infrastructure_role,
            "uncertain": self.uncertain,
            "schema": self.schema,
        }


@dataclass
class DispatchOutcome:
    decision: RoutingDecision
    payload: dict[str, Any]
    record: DispatchRecord

    def to_public(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_public(),
            "record": self.record.to_public(),
            "schema": "cognitive_dispatch_outcome.v1",
        }


class CognitiveDispatchEngine:
    """Own complete cognitive dispatch — never terminate at infrastructure."""

    def __init__(self, engine: CognitiveEngine) -> None:
        self.engine = engine
        self.router = CognitiveRoutingEngine(engine)
        self.handlers = CognitiveOrganHandlers(engine)

    def dispatch(self, request: str) -> DispatchOutcome:
        decision = self.router.decide(request)
        path = list(decision.reasoning_path)
        path.append("cognitive_dispatch")
        ownership = decision.ownership

        if ownership.primary_organ == ORGAN_NONE or not decision.classification.is_memory_request:
            path.append("non_cognitive_host")
            record = DispatchRecord(
                intent=ownership.intent.value,
                primary_organ=ORGAN_NONE,
                supporting_organs=[],
                dispatch_path=path,
                reconstruction_path=[],
                terminated_at=ORGAN_NONE,
                infrastructure_role="host_execution",
                uncertain=decision.classification.uncertain,
            )
            decision.reasoning_path = path
            return DispatchOutcome(
                decision=decision,
                payload={
                    "memory": None,
                    "confidence": decision.classification.confidence,
                    "explanation_class": "unknown",
                    "ambiguous": False,
                    "concepts": [],
                    "cue_matched": False,
                    "experiences": [],
                    "associations": [],
                    "dispatch": record.to_public(),
                },
                record=record,
            )

        self._assert_cognitive_terminal(ownership.primary_organ)
        path.append(f"dispatch_primary:{ownership.primary_organ}")

        primary = self.handlers.invoke(
            ownership.primary_organ,
            request,
            intent=ownership.intent,
            as_primary=True,
        )
        contributions: list[OrganContribution] = [primary]
        reconstruction: list[str] = list(primary.reconstruction_steps)

        # Supporting organs contribute; primary remains the terminator.
        for support in ownership.supporting_organs:
            if support == ownership.primary_organ:
                continue
            self._assert_cognitive_terminal(support)
            path.append(f"dispatch_support:{support}")
            if (
                ownership.intent == CognitiveIntent.PROJECT
                and support == "identity"
            ):
                contrib = self.handlers.project_support()
            else:
                # Cue supports appropriately for multi-organ reconstruction.
                support_request = _support_cue(ownership.intent, request, support)
                contrib = self.handlers.invoke(
                    support,
                    support_request,
                    intent=ownership.intent,
                    as_primary=False,
                )
            contributions.append(contrib)
            reconstruction.extend(contrib.reconstruction_steps)

        payload = self._merge(ownership, contributions, primary)
        payload["dispatch"] = {}
        terminated_at = ownership.primary_organ
        path.append(f"terminate:{terminated_at}")
        reconstruction.append(f"terminate:{terminated_at}")

        # Integrity: memory text must be cognitive speech, not storage dump.
        payload["memory"] = sanitize_cognitive_text(payload.get("memory"))
        if isinstance(payload.get("memory"), str) and payload["memory"].startswith("{"):
            payload["memory"] = None
            payload["confidence"] = min(float(payload.get("confidence") or 0), 0.3)
            payload["cue_matched"] = False
            path.append("reject_raw_storage_leak")

        record = DispatchRecord(
            intent=ownership.intent.value,
            primary_organ=ownership.primary_organ,
            supporting_organs=list(ownership.supporting_organs),
            dispatch_path=path,
            reconstruction_path=reconstruction,
            terminated_at=terminated_at,
            contributions=[c.to_public() for c in contributions],
            infrastructure_role="substrate_only",
            uncertain=ownership.uncertain,
        )
        payload["dispatch"] = record.to_public()
        decision.reasoning_path = path
        return DispatchOutcome(decision=decision, payload=payload, record=record)

    def _assert_cognitive_terminal(self, organ: str) -> None:
        key = (organ or "").strip().lower().replace("-", "_")
        if key in FORBIDDEN_TERMINALS or organ in FORBIDDEN_TERMINALS:
            raise RuntimeError(
                f"Cognitive termination refused at infrastructure endpoint: {organ}"
            )
        if organ not in COGNITIVE_TERMINALS:
            raise RuntimeError(f"Unknown cognitive terminal: {organ}")

    def _merge(
        self,
        ownership: CognitiveOwnership,
        contributions: list[OrganContribution],
        primary: OrganContribution,
    ) -> dict[str, Any]:
        """Primary owns the answer; supports may fill gaps or enrich evidence."""
        memory = primary.memory
        conf = primary.confidence
        expl = primary.explanation_class
        ambiguous = primary.ambiguous
        cue_matched = primary.cue_matched
        concepts = list(primary.concepts)
        experiences = list(primary.experiences)
        associations = list(primary.associations)
        reflective = list(primary.reflective)
        learning = list(primary.learning)

        for contrib in contributions[1:]:
            concepts.extend(contrib.concepts)
            experiences.extend(contrib.experiences)
            associations.extend(contrib.associations)
            reflective.extend(contrib.reflective)
            learning.extend(contrib.learning)
            # User identity is owned solely by the Identity organ — never fill
            # gaps from remembering/experiences (D043 assistant bleed).
            if ownership.intent == CognitiveIntent.USER_IDENTITY:
                continue
            if ownership.intent == CognitiveIntent.ASSISTANT_IDENTITY:
                continue
            if not memory and contrib.memory:
                memory = contrib.memory
                conf = max(conf, contrib.confidence)
                expl = contrib.explanation_class or expl
                cue_matched = cue_matched or contrib.cue_matched
                ambiguous = ambiguous or contrib.ambiguous
            elif (
                memory
                and contrib.memory
                and contrib.organ in ownership.supporting_organs
                and ownership.intent
                in (
                    CognitiveIntent.GOAL,
                    CognitiveIntent.PROJECT,
                    CognitiveIntent.REFLECTION,
                )
                and contrib.memory not in memory
            ):
                # Bounded enrichment — never replace primary with support.
                if ownership.intent == CognitiveIntent.REFLECTION and contrib.organ == "learning":
                    memory = f"{memory} {contrib.memory}".strip()
                    conf = max(conf, contrib.confidence)
                elif ownership.intent == CognitiveIntent.GOAL and contrib.organ == "remembering":
                    if not primary.memory:
                        memory = contrib.memory
                        conf = contrib.confidence
                        cue_matched = contrib.cue_matched
                elif ownership.intent == CognitiveIntent.PROJECT:
                    memory = f"{contrib.memory} {memory}".strip()
                    conf = max(conf, contrib.confidence)
                    cue_matched = True

        return {
            "memory": memory,
            "confidence": float(conf),
            "explanation_class": expl,
            "ambiguous": ambiguous,
            "concepts": _dedupe_id_dicts(concepts)[:12],
            "cue_matched": cue_matched,
            "experiences": _dedupe_id_dicts(experiences)[:12],
            "associations": _dedupe_id_dicts(associations)[:12],
            "reflective": reflective[:12],
            "learning": learning[:12],
            "terminated_at": ownership.primary_organ,
        }


def _support_cue(intent: CognitiveIntent, request: str, organ: str) -> str:
    if intent == CognitiveIntent.GOAL and organ == "remembering":
        return f"what do you remember about our goals and long-term plans? {request}"
    if intent == CognitiveIntent.REFLECTION and organ == "learning":
        return "how has your understanding changed? what have you learned?"
    if intent == CognitiveIntent.REFLECTION and organ == "experiences":
        return "what experiences changed your understanding?"
    if intent == CognitiveIntent.USER_IDENTITY and organ == "remembering":
        return "what do you know about the user"
    if intent == CognitiveIntent.PROJECT and organ == "remembering":
        return request
    return request


def _dedupe_id_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("id") or item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
