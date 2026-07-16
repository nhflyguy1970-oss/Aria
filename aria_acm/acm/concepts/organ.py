"""Concept organ — answers: What is this?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from acm.concepts.extract import ConceptCue, extract_cues
from acm.concepts.model import (
    Concept,
    ConceptProposal,
    ConceptStage,
    HierarchyEdge,
    HierarchyKind,
)
from acm.types import Attribute, ConceptRole, new_id
from acm.validation.harness import ConfidenceDelta

if TYPE_CHECKING:
    from acm.associations.organ import AssociationOrgan
    from acm.core.store import CognitiveStore
    from acm.experiences.model import Experience
    from acm.validation.harness import ValidationHarness

_GROWING_EVIDENCE = 2
_STABLE_STRENGTH = 0.65
_STABLE_CONF = 0.6
_STABLE_EVIDENCE = 3
_MATURE_STRENGTH = 0.8
_MATURE_CONF = 0.75
_MATURE_EVIDENCE = 5


class ConceptOrgan:
    """Emergent meaning structures over Experiences."""

    def __init__(self, store: CognitiveStore, validation: ValidationHarness) -> None:
        self.store = store
        self.validation = validation
        self.hierarchy: dict[str, HierarchyEdge] = {}
        self.proposals: dict[str, ConceptProposal] = {}
        self.associations: AssociationOrgan | None = None
        self._births = 0
        self._strengthenings = 0
        self._weakenings = 0
        self._abstractions = 0
        self._stage_changes = 0

    def bind_associations(self, associations: AssociationOrgan) -> None:
        self.associations = associations

    # --- public cognitive surface ----------------------------------------------

    def ingest_from_encode(
        self,
        text: str,
        *,
        encode_kind: str,
        weight: float,
        context_tags: tuple[str, ...] = (),
    ) -> tuple[Concept, list[str]]:
        """Create/reinforce Concepts from text prior to Experience birth."""
        cues = extract_cues(text, encode_kind=encode_kind)
        primary: Concept | None = None
        touched: list[Concept] = []
        for cue in cues:
            concept = self._upsert_from_cue(cue, weight=weight, context_tags=context_tags)
            touched.append(concept)
            if primary is None:
                primary = concept
            elif cue.role in (ConceptRole.PREFERENCE, ConceptRole.IDENTITY):
                primary = concept
            elif cue.is_instance and primary and primary.role != ConceptRole.PREFERENCE:
                primary = concept
        assert primary is not None
        for cue in cues:
            if cue.parent_label:
                child = self._find_by_label(cue.label)
                parent = self._find_by_label(cue.parent_label)
                if child and parent:
                    self.link_is_a(child.id, parent.id, weight=min(1.0, 0.4 + weight * 0.4))
        self._maybe_propose_merges(touched)
        # unique ids preserve order
        ids: list[str] = []
        for c in touched:
            if c.id not in ids:
                ids.append(c.id)
        return primary, ids

    def bind_experience(self, experience: Experience, concept_ids: list[str] | None = None) -> None:
        """Attach Experience evidence; reinforce listed Concepts (or those on the Experience)."""
        ids = list(concept_ids or experience.concept_ids)
        # Also emerge extra token nuclei already partially handled in ingest
        for cid in ids:
            concept = self.store.concepts.get(cid)
            if concept is None:
                continue
            self._add_evidence(concept, experience.id)
            self._reinforce(concept, weight=experience.importance, reason="experience_bind")
            self._update_prototype(concept, experience.summary)
            self._add_exemplar(concept, experience.id)
            self._recompute_stage(concept)

    def what_is_this(self, cue: str) -> dict[str, Any]:
        """Cognitive question M3: What is this?"""
        matches = self.recognize(cue, limit=5)
        if not matches:
            return {
                "question": "What is this?",
                "answer": "I don't have a stable concept for that yet.",
                "seen_before": False,
                "confidence": 0.0,
                "matches": [],
            }
        top = matches[0]
        concept = self.store.concepts[top["concept_id"]]
        parents = [self._label_of(p) for p in concept.parent_ids if p in self.store.concepts]
        children = [self._label_of(c) for c in concept.child_ids if c in self.store.concepts]
        kind_phrase = concept.labels[0]
        if parents:
            answer = f"This appears to be {kind_phrase}, a kind of {parents[0]}."
        else:
            answer = f"This appears to be {kind_phrase}."
        if concept.stage == ConceptStage.NUCLEUS:
            answer += " (emerging nucleus)"
        return {
            "question": "What is this?",
            "answer": answer,
            "seen_before": len(concept.evidence_ids) > 0,
            "confidence": concept.confidence,
            "concept": concept.to_public(),
            "hierarchy": {"parents": parents, "children": children},
            "prototype": concept.prototype.to_public(),
            "exemplars": list(concept.exemplar_ids[-8:]),
            "matches": matches,
            "stage": concept.stage.value,
        }

    def recognize(self, cue: str, *, limit: int = 5) -> list[dict[str, Any]]:
        """Future recognition hook — not Remembering; similarity over Concepts only."""
        q = (cue or "").lower().strip()
        scored: list[tuple[float, Concept]] = []
        for concept in self.store.concepts.values():
            if concept.stage == ConceptStage.RETIRED:
                continue
            if not concept.active and concept.stage != ConceptStage.DORMANT:
                continue
            score = 0.0
            for lab in concept.labels:
                lab_l = lab.lower()
                if q == lab_l:
                    score += 5.0
                elif q in lab_l or lab_l in q:
                    score += 3.0
                else:
                    overlap = set(q.split()) & set(lab_l.split())
                    score += 1.2 * len(overlap)
            for attr in concept.attributes:
                if not attr.active:
                    continue
                if q in attr.value.lower() or q in attr.key:
                    score += 2.0 * attr.confidence
            for feat, val in concept.prototype.features.items():
                if q in feat or q in val.lower():
                    score += 1.5 * concept.prototype.feature_weights.get(feat, 0.5)
            # Prefer mature meanings
            stage_bonus = {
                ConceptStage.NUCLEUS: 0.2,
                ConceptStage.GROWING: 0.5,
                ConceptStage.STABLE: 1.0,
                ConceptStage.MATURE: 1.3,
                ConceptStage.DORMANT: 0.1,
                ConceptStage.RETIRED: 0.0,
            }[concept.stage]
            score *= 0.5 + 0.5 * concept.confidence
            score *= 0.5 + 0.5 * concept.strength
            score += stage_bonus
            if score > 0.5:
                scored.append((score, concept))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for score, concept in scored[:limit]:
            out.append(
                {
                    "concept_id": concept.id,
                    "label": concept.labels[0],
                    "score": round(score, 3),
                    "stage": concept.stage.value,
                    "confidence": concept.confidence,
                    "seen_before": len(concept.evidence_ids) > 0,
                }
            )
        return out

    def link_is_a(
        self, child_id: str, parent_id: str, *, weight: float = 0.5
    ) -> HierarchyEdge | None:
        if child_id == parent_id:
            return None
        child = self.store.concepts.get(child_id)
        parent = self.store.concepts.get(parent_id)
        if not child or not parent:
            return None
        for edge in self.hierarchy.values():
            if edge.child_id == child_id and edge.parent_id == parent_id:
                return edge
        edge = HierarchyEdge(
            id=new_id("hier"),
            child_id=child_id,
            parent_id=parent_id,
            kind=HierarchyKind.IS_A,
            weight=weight,
        )
        self.hierarchy[edge.id] = edge
        if parent_id not in child.parent_ids:
            child.parent_ids.append(parent_id)
        if child_id not in parent.child_ids:
            parent.child_ids.append(child_id)
        if child_id not in parent.instance_ids and child.metadata.get("is_instance"):
            parent.instance_ids.append(child_id)
        self._abstractions += 1
        self.validation.record_concept(
            action="abstraction",
            child_id=child_id,
            parent_id=parent_id,
            hierarchy=1,
            abstraction=1,
        )
        # Parent gains gentle abstraction reinforcement
        self._reinforce(parent, weight=weight * 0.4, reason="abstraction_parent")
        if self.associations is not None:
            self.associations.absorb_hierarchy_edge(child_id, parent_id, weight=weight)
            self.associations.absorb_siblings(parent_id)
        return edge

    def weaken(self, concept_id: str, *, amount: float = 0.05) -> Concept | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return None
        before = concept.strength
        concept.strength = max(0.0, concept.strength - amount)
        concept.confidence = max(0.05, concept.confidence - amount * 0.5)
        self._weakenings += 1
        self.validation.record_concept(
            action="weaken",
            concept_id=concept.id,
            strength_before=before,
            strength_after=concept.strength,
            weakening=1,
        )
        self._recompute_stage(concept)
        return concept

    def resurrect(self, concept_id: str) -> Concept | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return None
        if concept.stage in (ConceptStage.DORMANT, ConceptStage.RETIRED):
            concept.active = True
            concept.stage = ConceptStage.GROWING if concept.evidence_ids else ConceptStage.NUCLEUS
            concept.provisional = concept.stage == ConceptStage.NUCLEUS
            self._stage_changes += 1
            self.validation.record_concept(
                action="resurrect",
                concept_id=concept.id,
                stage=concept.stage.value,
                lifecycle=1,
            )
        return concept

    def pending_proposals(self) -> list[dict[str, Any]]:
        return [
            {
                "id": p.id,
                "kind": p.kind,
                "concept_ids": list(p.concept_ids),
                "reason": p.reason,
                "status": p.status,
            }
            for p in self.proposals.values()
            if p.status == "pending"
        ]

    def observables(self) -> dict[str, Any]:
        by_stage: dict[str, int] = {}
        for c in self.store.concepts.values():
            by_stage[c.stage.value] = by_stage.get(c.stage.value, 0) + 1
        return {
            "concept_count": len(self.store.concepts),
            "hierarchy_edges": len(self.hierarchy),
            "nuclei": by_stage.get(ConceptStage.NUCLEUS.value, 0),
            "mature": by_stage.get(ConceptStage.MATURE.value, 0),
            "births": self._births,
            "strengthenings": self._strengthenings,
            "weakenings": self._weakenings,
            "abstractions": self._abstractions,
            "stage_changes": self._stage_changes,
            "by_stage": by_stage,
            "pending_proposals": len(self.pending_proposals()),
        }

    def register_existing(self, concept: Concept) -> None:
        """Track Concepts created outside ingest (e.g. Identity schema anchors)."""
        if not concept.evidence_ids and concept.stage == ConceptStage.NUCLEUS:
            pass
        self.validation.record_concept(
            action="register",
            concept_id=concept.id,
            stage=concept.stage.value,
            label=concept.labels[0] if concept.labels else "",
        )

    # --- internals --------------------------------------------------------------

    def _upsert_from_cue(
        self,
        cue: ConceptCue,
        *,
        weight: float,
        context_tags: tuple[str, ...],
    ) -> Concept:
        existing = self._find_by_label(cue.label)
        # Only preference keys are globally unique identity keys for upsert
        if existing is None and cue.attr_key.startswith("favorite_"):
            for c in self.store.concepts.values():
                if any(a.key == cue.attr_key and a.active for a in c.attributes):
                    existing = c
                    break

        if existing is None:
            concept = self.store.add_concept(
                cue.label,
                role=cue.role,
                identity=cue.identity,
                provisional=True,
                importance=max(0.35, weight * 0.9),
                confidence=min(0.7, 0.35 + weight * 0.35),
                strength=min(0.55, 0.25 + weight * 0.35),
                stage=ConceptStage.NUCLEUS,
            )
            concept.metadata["is_instance"] = cue.is_instance
            concept.attributes.append(
                Attribute(
                    key=cue.attr_key,
                    value=cue.attr_value,
                    confidence=min(0.85, 0.4 + weight * 0.4),
                    importance=weight,
                    context_tags=context_tags,
                )
            )
            self._births += 1
            self.validation.record_concept(
                action="birth",
                concept_id=concept.id,
                stage=concept.stage.value,
                label=cue.label,
                nucleus=1,
                birth=1,
            )
            return concept

        # Privileged identity schemas must not absorb token-nucleus noise
        # (e.g. cue label "user" from "User name is Jeff" → mentioned=user).
        if (
            existing.identity
            and existing.metadata.get("schema")
            and not cue.identity
            and cue.attr_key in ("mentioned", "statement", "category")
        ):
            return existing

        # Reinforce + attribute update
        self._apply_attribute(existing, cue, weight=weight, context_tags=context_tags)
        self._reinforce(existing, weight=weight * 0.8, reason="cue_match")
        if cue.is_instance:
            existing.metadata["is_instance"] = True
        self._recompute_stage(existing)
        return existing

    def _apply_attribute(
        self,
        concept: Concept,
        cue: ConceptCue,
        *,
        weight: float,
        context_tags: tuple[str, ...],
    ) -> None:
        for attr in concept.attributes:
            if attr.key == cue.attr_key and attr.active:
                if attr.value.lower() != cue.attr_value.lower():
                    attr.active = False
                    concept.attributes.append(
                        Attribute(
                            key=cue.attr_key,
                            value=cue.attr_value,
                            confidence=min(0.95, attr.confidence + 0.08),
                            importance=weight,
                            context_tags=context_tags,
                            version=attr.version + 1,
                        )
                    )
                    self.validation.record_reconsolidation(
                        concept_id=concept.id,
                        attribute_key=cue.attr_key,
                        kind="supersede",
                        previous=attr.value,
                        current=cue.attr_value,
                    )
                    concept.confidence = max(0.2, concept.confidence - 0.05)
                else:
                    before = attr.confidence
                    attr.confidence = min(1.0, attr.confidence + 0.05)
                    self.validation.record_confidence(
                        ConfidenceDelta(
                            time(),
                            concept.id,
                            cue.attr_key,
                            before,
                            attr.confidence,
                            "concept_reinforce",
                        )
                    )
                return
        concept.attributes.append(
            Attribute(
                key=cue.attr_key,
                value=cue.attr_value,
                confidence=min(0.85, 0.4 + weight * 0.4),
                importance=weight,
                context_tags=context_tags,
            )
        )

    def _reinforce(self, concept: Concept, *, weight: float, reason: str) -> None:
        before_s = concept.strength
        before_c = concept.confidence
        concept.strength = min(1.0, concept.strength + 0.07 * weight)
        concept.confidence = min(1.0, concept.confidence + 0.05 * weight)
        concept.importance = max(concept.importance, weight * 0.9)
        concept.access_count += 1
        concept.last_activated = time()
        concept.active = True
        if concept.stage == ConceptStage.DORMANT:
            self.resurrect(concept.id)
        self._strengthenings += 1
        self.validation.record_concept(
            action="strengthen",
            concept_id=concept.id,
            reason=reason,
            strength_before=before_s,
            strength_after=concept.strength,
            confidence_before=before_c,
            confidence_after=concept.confidence,
            strengthening=1,
        )
        self.validation.record_confidence(
            ConfidenceDelta(
                time(),
                concept.id,
                "concept",
                before_c,
                concept.confidence,
                reason,
            )
        )
        self._recompute_stage(concept)

    def _add_evidence(self, concept: Concept, experience_id: str) -> None:
        if experience_id and experience_id not in concept.evidence_ids:
            concept.evidence_ids.append(experience_id)

    def _add_exemplar(self, concept: Concept, experience_id: str) -> None:
        if not experience_id:
            return
        if experience_id in concept.exemplar_ids:
            return
        concept.exemplar_ids.append(experience_id)
        if len(concept.exemplar_ids) > 24:
            del concept.exemplar_ids[:-24]

    def _update_prototype(self, concept: Concept, summary: str) -> None:
        # Lightweight: fold active attributes into prototype features
        for attr in concept.attributes:
            if not attr.active:
                continue
            key = attr.key
            prev_w = concept.prototype.feature_weights.get(key, 0.0)
            new_w = prev_w + attr.confidence
            # Keep value with higher cumulative weight
            if key not in concept.prototype.features or new_w >= prev_w:
                concept.prototype.features[key] = attr.value
            concept.prototype.feature_weights[key] = min(10.0, new_w)
        # Mention token as a soft feature
        token = summary.strip().split()[:3]
        if token:
            feat = "surface"
            concept.prototype.features.setdefault(feat, " ".join(token).lower())
            concept.prototype.feature_weights[feat] = min(
                5.0, concept.prototype.feature_weights.get(feat, 0.0) + 0.2
            )
        self.validation.record_concept(
            action="prototype_update",
            concept_id=concept.id,
            prototype=1,
        )

    def _recompute_stage(self, concept: Concept) -> None:
        if concept.stage == ConceptStage.RETIRED:
            return
        old = concept.stage
        n = len(concept.evidence_ids)
        if concept.strength < 0.15 and n <= 1 and not concept.identity:
            concept.stage = ConceptStage.DORMANT
            concept.active = False
            concept.provisional = True
        elif (
            concept.strength >= _MATURE_STRENGTH
            and concept.confidence >= _MATURE_CONF
            and n >= _MATURE_EVIDENCE
        ):
            concept.stage = ConceptStage.MATURE
            concept.provisional = False
            concept.active = True
        elif (
            concept.strength >= _STABLE_STRENGTH
            and concept.confidence >= _STABLE_CONF
            and n >= _STABLE_EVIDENCE
        ):
            concept.stage = ConceptStage.STABLE
            concept.provisional = False
            concept.active = True
        elif n >= _GROWING_EVIDENCE or concept.strength >= 0.45:
            concept.stage = ConceptStage.GROWING
            concept.provisional = concept.strength < 0.6
            concept.active = True
        else:
            concept.stage = ConceptStage.NUCLEUS
            concept.provisional = True
            concept.active = True
        if concept.stage != old:
            self._stage_changes += 1
            self.validation.record_concept(
                action="stage_change",
                concept_id=concept.id,
                stage_before=old.value,
                stage=concept.stage.value,
                maturity=1,
                lifecycle=1,
            )

    def _find_by_label(self, label: str) -> Concept | None:
        q = label.lower().strip()
        exact: Concept | None = None
        for c in self.store.concepts.values():
            if c.stage == ConceptStage.RETIRED:
                continue
            if any(lab.lower() == q for lab in c.labels):
                exact = c
                break
        if exact is not None:
            return exact
        # Conservative near-match: equal after stripping plural 's', not substring contain
        stem = q[:-1] if q.endswith("s") and len(q) > 4 else q
        for c in self.store.concepts.values():
            if c.stage == ConceptStage.RETIRED:
                continue
            for lab in c.labels:
                lab_l = lab.lower()
                lab_stem = lab_l[:-1] if lab_l.endswith("s") and len(lab_l) > 4 else lab_l
                if lab_stem == stem:
                    return c
        return None

    def _label_of(self, concept_id: str) -> str:
        c = self.store.concepts.get(concept_id)
        return c.labels[0] if c and c.labels else concept_id

    def _maybe_propose_merges(self, concepts: list[Concept]) -> None:
        labels: dict[str, list[Concept]] = {}
        for c in concepts:
            key = c.labels[0].lower()
            labels.setdefault(key, []).append(c)
        # Cross-scan store for near-duplicate labels
        for c in list(self.store.concepts.values()):
            if c.stage in (ConceptStage.RETIRED, ConceptStage.DORMANT):
                continue
            for other in concepts:
                if other.id == c.id:
                    continue
                a, b = c.labels[0].lower(), other.labels[0].lower()
                if a == b or a in b or b in a:
                    if abs(len(a) - len(b)) <= 2 or a == b:
                        self._propose(
                            "merge",
                            (c.id, other.id),
                            reason=f"similar_labels:{a}|{b}",
                        )

    def _propose(self, kind: str, concept_ids: tuple[str, ...], *, reason: str) -> None:
        # Dedup pending
        key = (kind, tuple(sorted(concept_ids)))
        for p in self.proposals.values():
            if p.status == "pending" and p.kind == kind and tuple(sorted(p.concept_ids)) == key[1]:
                return
        prop = ConceptProposal(
            id=f"cprop_{uuid4().hex[:10]}",
            kind=kind,
            concept_ids=tuple(sorted(concept_ids)),
            reason=reason,
        )
        self.proposals[prop.id] = prop
        self.validation.record_concept(
            action="proposal",
            proposal_id=prop.id,
            kind=kind,
            concept_ids=list(prop.concept_ids),
            merge=1 if kind == "merge" else 0,
            split=1 if kind == "split" else 0,
        )
