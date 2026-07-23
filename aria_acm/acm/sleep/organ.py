"""Offline Cognition — Sleep & Consolidation organ."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from acm.experiences.kinds import CognitiveKind
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.attention.organ import AttentionOrgan
    from acm.confidence.organ import ConfidenceOrgan
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.learning.organ import LearningOrgan
    from acm.validation.harness import ValidationHarness


class OfflineCognitionOrgan:
    """Answers: What should become long-term memory?

    Functional consolidation — not biological sleep simulation.
    Never invents Experiences. Never modifies Experience content.
    """

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        learning: LearningOrgan,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
        confidence: ConfidenceOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.learning = learning
        self.activation = activation
        self.attention = attention
        self.forgetting = forgetting
        self.confidence = confidence
        self._batches = 0
        self._replays = 0
        self._stabilizations = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
        confidence: ConfidenceOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting
        if confidence is not None:
            self.confidence = confidence

    def consolidate(self, *, apply_low_impact: bool = True) -> dict[str, Any]:
        """Cognitive question M8: What should become long-term memory?"""
        batch_id = new_id("slp")
        self._batches += 1
        replayed: list[str] = []
        adaptations_applied = 0
        proposals: list[str] = []
        cooled = 0
        stabilized = 0

        # Replay Reflective Experiences (recent first)
        reflections = [
            e
            for e in self.store.experiences.values()
            if e.cognitive_kind == CognitiveKind.REFLECTION
        ]
        reflections.sort(key=lambda e: e.t_encoded, reverse=True)
        for exp in reflections[:12]:
            replayed.append(exp.id)
            self._replays += 1
            ads = self.learning.learn_from_reflection(exp.id, sleep_batch_id=batch_id)
            adaptations_applied += sum(1 for a in ads if a.applied)
            for a in ads:
                if a.governance.value == "proposed":
                    proposals.append(a.id)
            self.validation.record_offline(
                action="replay",
                reflective_experience_id=exp.id,
                sleep_batch_id=batch_id,
                replay=1,
            )

        # Priority-ranked replay candidates from Attention (or fallback hot list)
        if self.attention is not None:
            hot_ids = self.attention.replay_candidates(limit=8)
            hot = [self.store.concepts[i] for i in hot_ids if i in self.store.concepts]
        else:
            hot = sorted(
                (c for c in self.store.concepts.values() if c.active and not c.identity),
                key=lambda c: c.access_count * c.strength,
                reverse=True,
            )[:8]
        if self.activation is not None:
            for concept in hot:
                if not concept.active:
                    continue
                label = concept.labels[0] if concept.labels else concept.id
                field = self.activation.activate(label, attention_weight=0.4)
                # Reinforce associations that carried energy in this replay field
                for aid in list(field.associations.keys())[:4]:
                    ads = self.learning.stabilize_association(
                        aid,
                        delta=0.03,
                        reflective_ids=replayed[:1],
                        sleep_batch_id=batch_id,
                    )
                    if ads:
                        adaptations_applied += 1
                        stabilized += 1
                        self._stabilizations += 1
                self.validation.record_offline(
                    action="neighborhood_replay",
                    concept_id=concept.id,
                    sleep_batch_id=batch_id,
                    replay=1,
                )

        # Cool very weak associations — Forgetting owns application
        if apply_low_impact:
            if self.forgetting is not None:
                cooled_ids = self.forgetting.cool_weak_associations(threshold=0.12)
                cooled = len(cooled_ids)
            else:
                for edge in list(self.store.associations.values()):
                    if edge.active and max(edge.strength_forward, edge.strength_backward) < 0.12:
                        edge.active = False
                        cooled += 1
                        self.validation.record_offline(
                            action="cool",
                            association_id=edge.id,
                            sleep_batch_id=batch_id,
                            cool=1,
                        )
            if cooled:
                self.validation.record_offline(
                    action="cool_batch",
                    sleep_batch_id=batch_id,
                    cool=cooled,
                    cooled=cooled,
                )

        # Abstraction proposals: duplicate labels (never auto-merge)
        label_map: dict[str, list[str]] = {}
        for c in self.store.concepts.values():
            if not c.active or not c.labels:
                continue
            label_map.setdefault(c.labels[0].lower(), []).append(c.id)
        for label, ids in label_map.items():
            if len(ids) > 1:
                proposals.append(f"merge_candidate:{label}:{','.join(ids)}")
                self.validation.record_offline(
                    action="abstraction_proposal",
                    label=label,
                    proposal=1,
                    sleep_batch_id=batch_id,
                )
            identity_ids = [
                i
                for i in ids
                if self.store.concepts.get(i) and self.store.concepts[i].identity
            ]
            if len(identity_ids) > 1:
                proposals.append(
                    f"identity_merge_requires_assent:{label}:{','.join(identity_ids)}"
                )

        # Hierarchy proposals from clustering (Concept organ owns taxonomy; never auto-invent).
        concepts = getattr(self.learning, "concepts", None)
        if concepts is not None:
            for prop in concepts.propose_hierarchy_from_clusters(
                min_cluster=2, max_proposals=6
            ):
                parent = (prop.metadata or {}).get("parent_id", "")
                kids = (prop.metadata or {}).get("child_ids") or []
                proposals.append(
                    f"hierarchy_candidate:{parent}:{','.join(kids[:6])}:{prop.id}"
                )
                self.validation.record_offline(
                    action="hierarchy_proposal",
                    proposal=1,
                    sleep_batch_id=batch_id,
                    proposal_id=prop.id,
                )
            # Cap4: derive evidenced multi-level abstractions (no invented Experiences).
            derived = concepts.derive_abstractions_from_hierarchy()
            if derived:
                proposals.append(f"abstraction_derived:{len(derived)}")
                self.validation.record_offline(
                    action="abstraction_derive",
                    proposal=1,
                    sleep_batch_id=batch_id,
                    derived_count=len(derived),
                )

        # Identity stabilization: slight confidence toward mean of evidence mass
        for c in self.store.concepts.values():
            if not c.identity or not c.active:
                continue
            if len(c.evidence_ids) >= 2 and 0.35 < c.confidence < 0.85:
                before = c.confidence
                # stabilize toward 0.55–0.75 band
                target = min(0.75, max(0.55, c.confidence))
                c.confidence = c.confidence * 0.85 + target * 0.15
                if abs(c.confidence - before) > 1e-6:
                    stabilized += 1
                    self._stabilizations += 1
                    self.validation.record_offline(
                        action="identity_stabilize",
                        concept_id=c.id,
                        sleep_batch_id=batch_id,
                        stabilize=1,
                        confidence_before=before,
                        confidence_after=c.confidence,
                    )

        # M5 Cap2 — evidence aging / stale detection (never deletes provenance).
        aging: dict[str, Any] = {}
        if self.confidence is not None:
            aging = self.confidence.age_evidence_pass()
            for c in list(self.store.concepts.values())[:40]:
                if c.active and not c.identity and len(c.evidence_ids) >= 2:
                    self.confidence.stabilize_confidence(c.id)

        # M5 Cap5 — temporal patterns weaken when unobserved.
        pattern_aging = self.learning.age_temporal_patterns()

        payload = {
            "question": "What should become long-term memory?",
            "sleep_batch_id": batch_id,
            "replayed_reflections": replayed,
            "replay_count": len(replayed),
            "adaptations_applied": adaptations_applied,
            "cooled_associations": cooled,
            "stabilizations": stabilized,
            "evidence_aging": aging,
            "temporal_pattern_aging": pattern_aging,
            "proposals": proposals,
            "applied_low_impact": apply_low_impact,
            # backward compatible keys for older sleep tests
            "pruned_edges": cooled,
        }
        self.validation.record_offline(
            action="consolidate",
            sleep_batch_id=batch_id,
            consolidate=1,
            replay_count=len(replayed),
            adaptations_applied=adaptations_applied,
            cooled=cooled,
            stabilize=stabilized,
        )
        self.validation.record_sleep(**payload)
        return payload

    def observables(self) -> dict[str, Any]:
        return {
            "batches": self._batches,
            "replays": self._replays,
            "stabilizations": self._stabilizations,
        }
