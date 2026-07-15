"""In-memory cognitive substrate — informative technology choice, swappable later."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from acm.analogy.model import AnalogyMapping
from acm.associations.model import Association, RelationKind
from acm.attention.model import PriorityEvent
from acm.concepts.model import Concept, ConceptStage
from acm.confidence.model import ConfidenceEvent
from acm.experiences.model import Experience
from acm.forgetting.model import AccessibilityEvent
from acm.learning.model import Adaptation
from acm.prediction.model import Prediction
from acm.provenance.model import ProvenanceRecord
from acm.recombination.model import RecombinedMemory
from acm.reconciliation.model import ReconciliationRecord
from acm.simulation.model import Simulation
from acm.types import ConceptRole, EdgeType, EnvelopeRef, new_id


def _to_relation(edge_type: EdgeType | RelationKind | str) -> RelationKind:
    if isinstance(edge_type, RelationKind):
        return edge_type
    value = edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type)
    if value == "contests":
        value = RelationKind.CONFLICTS_WITH.value
    if value == "is_a":
        value = RelationKind.IS_A_TRAFFIC.value
    try:
        return RelationKind(value)
    except ValueError:
        return RelationKind.RELATED_TO


@dataclass
class Goal:
    id: str
    title: str
    status: str = "active"  # active | completed | abandoned | superseded
    importance: float = 0.6
    created: float = 0.0
    completed: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class CognitiveStore:
    """Minimal durable-feeling store kept in process for foundational milestones."""

    def __init__(self) -> None:
        self.experiences: dict[str, Experience] = {}
        self.concepts: dict[str, Concept] = {}
        self.associations: dict[str, Association] = {}
        self.goals: dict[str, Goal] = {}
        self.envelopes: dict[str, EnvelopeRef] = {}
        self.adaptations: dict[str, Adaptation] = {}
        self.accessibility: dict[str, str] = {}
        self.priority_events: list[PriorityEvent] = []
        self.accessibility_events: list[AccessibilityEvent] = []
        self.predictions: dict[str, Prediction] = {}
        self.simulations: dict[str, Simulation] = {}
        self.recombinations: dict[str, RecombinedMemory] = {}
        self.analogies: dict[str, AnalogyMapping] = {}
        self.reconciliations: dict[str, ReconciliationRecord] = {}
        self.confidence_events: list[ConfidenceEvent] = []
        self.provenance: dict[str, ProvenanceRecord] = {}

    def provenance_for(self, artifact_id: str) -> list[ProvenanceRecord]:
        return [p for p in self.provenance.values() if p.artifact_id == artifact_id]

    def add_concept(
        self, label: str, role: ConceptRole = ConceptRole.ENTITY, **kwargs: Any
    ) -> Concept:
        now = time()
        stage = kwargs.pop("stage", ConceptStage.NUCLEUS)
        concept = Concept(
            id=new_id("con"),
            labels=[label],
            role=role,
            first_seen=now,
            last_activated=now,
            stage=stage,
            **kwargs,
        )
        self.concepts[concept.id] = concept
        return concept

    def find_concepts_by_label(self, text: str) -> list[Concept]:
        q = text.lower()
        hits: list[Concept] = []
        for c in self.concepts.values():
            if c.stage == ConceptStage.RETIRED:
                continue
            if not c.active and c.stage != ConceptStage.DORMANT:
                continue
            for lab in c.labels:
                lab_l = lab.lower()
                if lab_l == q or (len(q) >= 4 and (q in lab_l.split() or lab_l in q.split())):
                    hits.append(c)
                    break
            else:
                for attr in c.attributes:
                    if attr.active and (
                        attr.value.lower() == q
                        or (len(q) >= 4 and q in attr.value.lower())
                        or q in attr.key.lower()
                    ):
                        hits.append(c)
                        break
        seen: set[str] = set()
        out: list[Concept] = []
        for h in hits:
            if h.id not in seen:
                seen.add(h.id)
                out.append(h)
        return out

    def add_association(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType | RelationKind | str = EdgeType.RELATED_TO,
        weight: float = 0.5,
    ) -> Association:
        """Legacy helper — Prefer AssociationOrgan.relate for cognition-first births."""
        now = time()
        assoc = Association(
            id=new_id("asc"),
            source_id=source_id,
            target_id=target_id,
            relation=_to_relation(edge_type),
            strength_forward=weight,
            strength_backward=max(0.1, weight * 0.65),
            confidence=min(0.9, 0.4 + weight * 0.4),
            first_seen=now,
            last_activated=now,
        )
        self.associations[assoc.id] = assoc
        return assoc

    def neighbors(self, concept_id: str) -> list[tuple[Association, Concept]]:
        out: list[tuple[Association, Concept]] = []
        for edge in self.associations.values():
            if not edge.active:
                continue
            other = None
            if edge.source_id == concept_id:
                other = self.concepts.get(edge.target_id)
            elif edge.target_id == concept_id:
                other = self.concepts.get(edge.source_id)
            if other and (other.active or other.stage == ConceptStage.DORMANT):
                out.append((edge, other))
        out.sort(key=lambda x: x[0].weight, reverse=True)
        return out

    def add_goal(self, title: str, **kwargs: Any) -> Goal:
        goal = Goal(id=new_id("goal"), title=title, created=time(), **kwargs)
        self.goals[goal.id] = goal
        return goal

    def active_goals(self) -> list[Goal]:
        return [g for g in self.goals.values() if g.status == "active"]
