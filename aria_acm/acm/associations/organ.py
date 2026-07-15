"""Association organ — answers: How is this related?"""

from __future__ import annotations

from collections import defaultdict, deque
from time import time
from typing import TYPE_CHECKING, Any

from acm.associations.model import (
    Association,
    AssociationStage,
    CognitiveDistance,
    RelationKind,
)
from acm.types import new_id

if TYPE_CHECKING:
    from acm.concepts.organ import ConceptOrgan
    from acm.core.store import CognitiveStore
    from acm.experiences.model import Experience
    from acm.validation.harness import ValidationHarness


class AssociationOrgan:
    """Living cognitive relationships among Concepts."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        concepts: ConceptOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.concepts = concepts
        self._births = 0
        self._strengthenings = 0
        self._weakenings = 0
        self._dormancies = 0
        self._reactivations = 0

    def bind_concepts(self, concepts: ConceptOrgan) -> None:
        self.concepts = concepts

    # --- birth / relate ---------------------------------------------------------

    def relate(
        self,
        source_id: str,
        target_id: str,
        relation: RelationKind | str = RelationKind.RELATED_TO,
        *,
        strength_forward: float = 0.4,
        strength_backward: float | None = None,
        confidence: float = 0.5,
        evidence_id: str = "",
        context_tags: tuple[str, ...] = (),
        goal_influenced: bool = False,
        identity_influenced: bool = False,
        temporal_weight: float = 0.0,
        unexpected: bool = False,
    ) -> Association | None:
        if source_id == target_id:
            return None
        if source_id not in self.store.concepts or target_id not in self.store.concepts:
            return None
        kind = relation if isinstance(relation, RelationKind) else RelationKind(str(relation))
        back = (
            strength_backward
            if strength_backward is not None
            else max(0.1, strength_forward * _default_asymmetry(kind))
        )
        existing = self._find(source_id, target_id, kind)
        if existing is not None:
            return self.reinforce(
                existing.id,
                forward_delta=0.06 * strength_forward,
                backward_delta=0.04 * back,
                evidence_id=evidence_id,
                context_tags=context_tags,
                goal_influenced=goal_influenced,
                identity_influenced=identity_influenced,
                temporal_weight=temporal_weight,
            )

        now = time()
        assoc = Association(
            id=new_id("asc"),
            source_id=source_id,
            target_id=target_id,
            relation=kind,
            strength_forward=min(1.0, strength_forward),
            strength_backward=min(1.0, back),
            confidence=min(1.0, confidence),
            stage=AssociationStage.NASCENT,
            evidence_ids=[evidence_id] if evidence_id else [],
            context_tags=tuple(context_tags),
            goal_influenced=goal_influenced,
            identity_influenced=identity_influenced,
            temporal_weight=temporal_weight,
            first_seen=now,
            last_activated=now,
            metadata={"unexpected": unexpected} if unexpected else {},
        )
        self.store.associations[assoc.id] = assoc
        self._births += 1
        self._recompute_stage(assoc)
        self.validation.record_association_organ(
            action="birth",
            association_id=assoc.id,
            relation=kind.value,
            source_id=source_id,
            target_id=target_id,
            strength_forward=assoc.strength_forward,
            strength_backward=assoc.strength_backward,
            distance=assoc.distance_band().value,
            birth=1,
            goal_influenced=goal_influenced,
            identity_influenced=identity_influenced,
            temporal=1 if temporal_weight else 0,
        )
        return assoc

    def reinforce(
        self,
        association_id: str,
        *,
        forward_delta: float = 0.05,
        backward_delta: float = 0.03,
        evidence_id: str = "",
        context_tags: tuple[str, ...] = (),
        goal_influenced: bool = False,
        identity_influenced: bool = False,
        temporal_weight: float = 0.0,
    ) -> Association | None:
        assoc = self.store.associations.get(association_id)
        if assoc is None:
            return None
        before_f, before_b = assoc.strength_forward, assoc.strength_backward
        if assoc.stage == AssociationStage.DORMANT:
            assoc.stage = AssociationStage.ACTIVE
            self._reactivations += 1
            self.validation.record_association_organ(
                action="reactivate",
                association_id=assoc.id,
                reactivation=1,
            )
        assoc.strength_forward = min(1.0, assoc.strength_forward + forward_delta)
        assoc.strength_backward = min(1.0, assoc.strength_backward + backward_delta)
        assoc.confidence = min(1.0, assoc.confidence + 0.03)
        assoc.access_count += 1
        assoc.last_activated = time()
        if evidence_id and evidence_id not in assoc.evidence_ids:
            assoc.evidence_ids.append(evidence_id)
        if context_tags:
            assoc.context_tags = tuple(dict.fromkeys(list(assoc.context_tags) + list(context_tags)))
        assoc.goal_influenced = assoc.goal_influenced or goal_influenced
        assoc.identity_influenced = assoc.identity_influenced or identity_influenced
        assoc.temporal_weight = max(assoc.temporal_weight, temporal_weight)
        self._strengthenings += 1
        self._recompute_stage(assoc)
        self.validation.record_association_organ(
            action="strengthen",
            association_id=assoc.id,
            strength_forward_before=before_f,
            strength_forward_after=assoc.strength_forward,
            strength_backward_before=before_b,
            strength_backward_after=assoc.strength_backward,
            distance=assoc.distance_band().value,
            strengthening=1,
        )
        return assoc

    def weaken(self, association_id: str, *, amount: float = 0.08) -> Association | None:
        assoc = self.store.associations.get(association_id)
        if assoc is None:
            return None
        before = assoc.strength_forward
        assoc.strength_forward = max(0.0, assoc.strength_forward - amount)
        assoc.strength_backward = max(0.0, assoc.strength_backward - amount * 0.8)
        assoc.confidence = max(0.05, assoc.confidence - amount * 0.4)
        self._weakenings += 1
        self._recompute_stage(assoc)
        self.validation.record_association_organ(
            action="weaken",
            association_id=assoc.id,
            strength_before=before,
            strength_after=assoc.strength_forward,
            distance=assoc.distance_band().value,
            weakening=1,
        )
        if assoc.stage == AssociationStage.DORMANT:
            self._dormancies += 1
        return assoc

    # --- experience / hierarchy absorption --------------------------------------

    def absorb_experience(
        self,
        experience: Experience,
        concept_ids: list[str],
        *,
        identity_influenced: bool = False,
    ) -> list[Association]:
        """Co-activation + context/goal/identity stamps among Concepts in one Experience."""
        created: list[Association] = []
        ids = [c for c in concept_ids if c in self.store.concepts]
        goal_bias = bool(experience.goal_ids)
        tags = tuple(experience.context_tags)
        # Pairwise co-activation (cap to avoid O(n^2) explosion on huge encodes)
        for i, a in enumerate(ids[:12]):
            for b in ids[i + 1 : 12]:
                # Prefer higher-maturity as source for slight asymmetry
                src, tgt = self._order_by_maturity(a, b)
                assoc = self.relate(
                    src,
                    tgt,
                    RelationKind.CO_ACTIVATED,
                    strength_forward=0.35 + 0.25 * experience.importance,
                    strength_backward=0.30 + 0.20 * experience.importance,
                    confidence=0.45 + 0.2 * experience.importance,
                    evidence_id=experience.id,
                    context_tags=tags,
                    goal_influenced=goal_bias,
                    identity_influenced=identity_influenced,
                )
                if assoc:
                    # Also soft belongs_with for neighborhood formation
                    self.relate(
                        src,
                        tgt,
                        RelationKind.BELONGS_WITH,
                        strength_forward=0.25 + 0.15 * experience.importance,
                        strength_backward=0.22 + 0.12 * experience.importance,
                        evidence_id=experience.id,
                        context_tags=tags,
                        goal_influenced=goal_bias,
                    )
                    created.append(assoc)
        return created

    def absorb_hierarchy_edge(
        self, child_id: str, parent_id: str, *, weight: float = 0.5
    ) -> Association | None:
        """Mirror Concept is_a as directional traffic (specific → general stronger)."""
        return self.relate(
            child_id,
            parent_id,
            RelationKind.IS_A_TRAFFIC,
            strength_forward=min(0.95, 0.55 + weight * 0.35),
            strength_backward=min(0.5, 0.2 + weight * 0.15),  # Animal → Dog weaker
            confidence=0.6,
        )

    def absorb_siblings(self, parent_id: str) -> list[Association]:
        """Resemblance among children sharing a parent Concept."""
        parent = self.store.concepts.get(parent_id)
        if parent is None:
            return []
        kids = [c for c in parent.child_ids if c in self.store.concepts][:8]
        out: list[Association] = []
        for i, a in enumerate(kids):
            for b in kids[i + 1 :]:
                assoc = self.relate(
                    a,
                    b,
                    RelationKind.RESEMBLES,
                    strength_forward=0.35,
                    strength_backward=0.35,
                    confidence=0.4,
                    unexpected=False,
                )
                if assoc:
                    out.append(assoc)
        return out

    # --- queries: How is this related? ------------------------------------------

    def how_related(
        self,
        left: str,
        right: str,
    ) -> dict[str, Any]:
        """Cognitive question M4: How is this related?"""
        a = self._resolve_concept(left)
        b = self._resolve_concept(right)
        if a is None or b is None:
            return {
                "question": "How is this related?",
                "answer": "I don't yet have solid Concepts to relate.",
                "related": False,
                "links": [],
            }
        links = self._links_between(a.id, b.id)
        if not links:
            # Path search one hop via shared neighbor
            path = self._common_neighbor_path(a.id, b.id)
            if path:
                return {
                    "question": "How is this related?",
                    "answer": (
                        f"{a.labels[0]} and {b.labels[0]} meet near {path['via_label']} "
                        f"(indirect / {path['distance']})."
                    ),
                    "related": True,
                    "mode": "neighborhood",
                    "path": path,
                    "links": [],
                    "neighborhoods": {
                        a.id: self.neighborhood(a.id, limit=5),
                        b.id: self.neighborhood(b.id, limit=5),
                    },
                }
            return {
                "question": "How is this related?",
                "answer": f"No clear relationship between {a.labels[0]} and {b.labels[0]} yet.",
                "related": False,
                "links": [],
            }

        top = max(links, key=lambda x: max(x.strength_forward, x.strength_backward))
        direction = (
            f"{a.labels[0]} → {b.labels[0]}"
            if top.source_id == a.id
            else f"{b.labels[0]} → {a.labels[0]}"
        )
        fwd = top.strength_toward(a.id, b.id)
        back = top.strength_toward(b.id, a.id)
        answer = (
            f"{a.labels[0]} is related to {b.labels[0]} via {top.relation.value} "
            f"({top.distance_band().value}; {direction}; "
            f"forward={fwd:.2f}, back={back:.2f})."
        )
        return {
            "question": "How is this related?",
            "answer": answer,
            "related": True,
            "mode": "direct",
            "links": [lnk.to_public() for lnk in links],
            "asymmetric": abs(fwd - back) > 0.08,
            "distance": top.distance_band().value,
        }

    def neighborhood(
        self,
        concept_ref: str,
        *,
        limit: int = 12,
        max_distance: CognitiveDistance | None = None,
    ) -> list[dict[str, Any]]:
        concept = self._resolve_concept(concept_ref)
        if concept is None:
            return []
        scored: list[tuple[float, Association, str]] = []
        for assoc in self.store.associations.values():
            if assoc.stage == AssociationStage.RETIRED:
                continue
            other = None
            strength = 0.0
            if assoc.source_id == concept.id:
                other = assoc.target_id
                strength = assoc.strength_forward
            elif assoc.target_id == concept.id:
                other = assoc.source_id
                strength = assoc.strength_backward
            else:
                continue
            band = assoc.distance_band()
            if max_distance and not _band_lte(band, max_distance):
                continue
            scored.append((strength, assoc, other))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for strength, assoc, other_id in scored[:limit]:
            other = self.store.concepts.get(other_id)
            out.append(
                {
                    "concept_id": other_id,
                    "label": other.labels[0] if other else other_id,
                    "relation": assoc.relation.value,
                    "strength": round(strength, 3),
                    "distance": assoc.distance_band().value,
                    "association_id": assoc.id,
                    "direction": "out" if assoc.source_id == concept.id else "in",
                }
            )
        return out

    def clusters(self, *, min_strength: float = 0.35) -> list[dict[str, Any]]:
        """Simple connected components over active Associations (cognitive neighborhoods)."""
        graph: dict[str, set[str]] = defaultdict(set)
        for assoc in self.store.associations.values():
            if not assoc.active:
                continue
            if max(assoc.strength_forward, assoc.strength_backward) < min_strength:
                continue
            graph[assoc.source_id].add(assoc.target_id)
            graph[assoc.target_id].add(assoc.source_id)
        seen: set[str] = set()
        communities: list[dict[str, Any]] = []
        for node in list(graph.keys()):
            if node in seen:
                continue
            comp: list[str] = []
            q: deque[str] = deque([node])
            seen.add(node)
            while q:
                cur = q.popleft()
                comp.append(cur)
                for nxt in graph[cur]:
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)
            if len(comp) < 2:
                continue
            labels = [
                self.store.concepts[c].labels[0]
                for c in comp
                if c in self.store.concepts and self.store.concepts[c].labels
            ]
            communities.append(
                {
                    "size": len(comp),
                    "concept_ids": comp,
                    "labels": labels[:12],
                }
            )
        communities.sort(key=lambda c: c["size"], reverse=True)
        self.validation.record_association_organ(
            action="clusters",
            cluster_count=len(communities),
            neighborhood=1,
            clusters=1,
        )
        return communities

    def observables(self) -> dict[str, Any]:
        by_stage: dict[str, int] = {}
        by_relation: dict[str, int] = {}
        by_distance: dict[str, int] = {}
        for a in self.store.associations.values():
            by_stage[a.stage.value] = by_stage.get(a.stage.value, 0) + 1
            by_relation[a.relation.value] = by_relation.get(a.relation.value, 0) + 1
            by_distance[a.distance_band().value] = by_distance.get(a.distance_band().value, 0) + 1
        return {
            "association_count": len(self.store.associations),
            "births": self._births,
            "strengthenings": self._strengthenings,
            "weakenings": self._weakenings,
            "dormancies": self._dormancies,
            "reactivations": self._reactivations,
            "by_stage": by_stage,
            "by_relation": by_relation,
            "by_distance": by_distance,
        }

    # --- internals --------------------------------------------------------------

    def _find(
        self, source_id: str, target_id: str, kind: RelationKind
    ) -> Association | None:
        for assoc in self.store.associations.values():
            if assoc.relation != kind:
                continue
            if assoc.source_id == source_id and assoc.target_id == target_id:
                return assoc
            # Oriented store: also match reverse pair as same cognitive link of this kind
            if assoc.source_id == target_id and assoc.target_id == source_id:
                return assoc
        return None

    def _links_between(self, a: str, b: str) -> list[Association]:
        out: list[Association] = []
        for assoc in self.store.associations.values():
            if assoc.stage == AssociationStage.RETIRED:
                continue
            if {assoc.source_id, assoc.target_id} == {a, b}:
                out.append(assoc)
        return out

    def _common_neighbor_path(self, a: str, b: str) -> dict[str, Any] | None:
        na = {n["concept_id"]: n for n in self.neighborhood(a, limit=20)}
        nb = {n["concept_id"]: n for n in self.neighborhood(b, limit=20)}
        shared = set(na) & set(nb)
        if not shared:
            return None
        via = next(iter(shared))
        label = self.store.concepts[via].labels[0] if via in self.store.concepts else via
        return {
            "via": via,
            "via_label": label,
            "distance": "near",
            "left": na[via],
            "right": nb[via],
        }

    def _resolve_concept(self, ref: str):
        if ref in self.store.concepts:
            return self.store.concepts[ref]
        if self.concepts is not None:
            matches = self.concepts.recognize(ref, limit=1)
            if matches:
                return self.store.concepts.get(matches[0]["concept_id"])
        hits = self.store.find_concepts_by_label(ref)
        return hits[0] if hits else None

    def _order_by_maturity(self, a: str, b: str) -> tuple[str, str]:
        ca, cb = self.store.concepts.get(a), self.store.concepts.get(b)
        sa = (ca.strength if ca else 0.0) * (ca.confidence if ca else 0.0)
        sb = (cb.strength if cb else 0.0) * (cb.confidence if cb else 0.0)
        return (a, b) if sa >= sb else (b, a)

    def _recompute_stage(self, assoc: Association) -> None:
        s = max(assoc.strength_forward, assoc.strength_backward)
        if assoc.stage == AssociationStage.RETIRED:
            return
        if s < 0.15:
            assoc.stage = AssociationStage.DORMANT
        elif s >= 0.75 and assoc.confidence >= 0.65 and len(assoc.evidence_ids) >= 3:
            assoc.stage = AssociationStage.STRONG
        elif s >= 0.35:
            assoc.stage = AssociationStage.ACTIVE
        else:
            assoc.stage = AssociationStage.NASCENT


def _default_asymmetry(kind: RelationKind) -> float:
    """Backward / forward ratio defaults (directed cognition)."""
    if kind in (
        RelationKind.IS_A_TRAFFIC,
        RelationKind.PART_OF,
        RelationKind.CAUSED_BY,
        RelationKind.DEPENDS_ON,
        RelationKind.REQUIRES,
        RelationKind.EXPLAINS,
        RelationKind.PREDICTS,
        RelationKind.OWNED_BY,
    ):
        return 0.45
    if kind in (RelationKind.CO_ACTIVATED, RelationKind.RESEMBLES, RelationKind.BELONGS_WITH):
        return 0.9
    return 0.65


def _band_lte(band: CognitiveDistance, limit: CognitiveDistance) -> bool:
    order = [
        CognitiveDistance.IMMEDIATE,
        CognitiveDistance.NEAR,
        CognitiveDistance.FAR,
        CognitiveDistance.WEAK,
        CognitiveDistance.UNEXPECTED,
        CognitiveDistance.DORMANT,
    ]
    try:
        return order.index(band) <= order.index(limit)
    except ValueError:
        return True
