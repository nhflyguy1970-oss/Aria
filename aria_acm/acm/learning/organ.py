"""Learning organ — answers: What have I learned?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.experiences.kinds import CognitiveKind
from acm.learning.model import (
    Adaptation,
    AdaptationKind,
    AdaptationTarget,
    GovernanceClass,
)
from acm.types import ConceptRole, new_id
from acm.validation.harness import ConfidenceDelta

if TYPE_CHECKING:
    from acm.associations.organ import AssociationOrgan
    from acm.concepts.organ import ConceptOrgan
    from acm.core.store import CognitiveStore
    from acm.experiences.model import Experience
    from acm.identity.organ import IdentityOrgan
    from acm.validation.harness import ValidationHarness


# Automatic magnitude caps (governance class A) — architecture constants for M7
CAP_CONCEPT_STRENGTH = 0.08
CAP_CONCEPT_CONFIDENCE = 0.06
CAP_ASSOC_STRENGTH = 0.05
CAP_PREF_CONFIDENCE = 0.05
CAP_IDENTITY_CONFIDENCE = 0.03
CAP_GOAL_IMPORTANCE = 0.04


class LearningOrgan:
    """Durable adaptation of living structures. Never rewrites Experiences."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        concepts: ConceptOrgan | None = None,
        associations: AssociationOrgan | None = None,
        identity: IdentityOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.concepts = concepts
        self.associations = associations
        self.identity = identity
        self._applied = 0
        self._proposed = 0
        self._abstained = 0
        self._rollbacks = 0

    def bind(
        self,
        *,
        concepts: ConceptOrgan | None = None,
        associations: AssociationOrgan | None = None,
        identity: IdentityOrgan | None = None,
    ) -> None:
        if concepts is not None:
            self.concepts = concepts
        if associations is not None:
            self.associations = associations
        if identity is not None:
            self.identity = identity

    def what_have_i_learned(self, cue: str = "") -> dict[str, Any]:
        """Cognitive question M7: What have I learned?"""
        items = list(self.store.adaptations.values())
        items.sort(key=lambda a: a.created, reverse=True)
        if cue:
            q = cue.lower()
            tokens = [t for t in q.split() if len(t) > 2]
            filtered: list[Adaptation] = []
            for a in items:
                if any(tok in a.summary.lower() for tok in tokens):
                    filtered.append(a)
                    continue
                target = self.store.concepts.get(a.target_id)
                if target and any(
                    tok in " ".join(target.labels).lower() for tok in tokens
                ):
                    filtered.append(a)
            items = filtered
        applied = [a for a in items if a.applied and a.governance != GovernanceClass.ABSTAINED]
        lessons = [a.to_public() for a in applied[:20]]
        if not lessons:
            answer = "I have not formed durable lessons about that yet."
        else:
            bits = [a.summary for a in applied[:5] if a.summary]
            answer = "I have learned: " + "; ".join(bits)
        return {
            "question": "What have I learned?",
            "answer": answer,
            "lesson_count": len(applied),
            "lessons": lessons,
            "pending_proposals": [
                a.to_public()
                for a in items
                if a.governance == GovernanceClass.PROPOSED and not a.applied
            ][:10],
        }

    def learn_from_reflection(
        self,
        reflective_experience_id: str,
        *,
        sleep_batch_id: str = "",
    ) -> list[Adaptation]:
        exp = self.store.experiences.get(reflective_experience_id)
        if exp is None:
            return []
        if exp.cognitive_kind != CognitiveKind.REFLECTION:
            return []
        outcomes = _outcomes_from_meta(exp)
        if not outcomes:
            outcomes = ["insight"]

        # Honest abstention when uncertainty / insufficient alone dominate
        hard_stop = {"uncertainty", "insufficient_evidence", "unknown"}
        if hard_stop.intersection(outcomes) and not (
            {"sufficient", "consistency", "pattern", "contradiction"} & set(outcomes)
        ):
            abstain = self._record_abstain(exp, sleep_batch_id=sleep_batch_id)
            return [abstain]

        created: list[Adaptation] = []
        concept_ids = list(exp.concept_ids)[:8]
        evidence = [exp.reflects_on_id] if exp.reflects_on_id else []

        reinforce = bool({"sufficient", "consistency", "pattern", "insight"} & set(outcomes))
        weaken = "contradiction" in outcomes

        if reinforce:
            for cid in concept_ids:
                ad = self._adapt_concept(
                    cid,
                    strength_delta=CAP_CONCEPT_STRENGTH * 0.6,
                    confidence_delta=CAP_CONCEPT_CONFIDENCE * 0.5,
                    kind=AdaptationKind.REINFORCE,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                    summary="Reinforced understanding of concept from reflection.",
                )
                if ad:
                    created.append(ad)
            for aid in self._assoc_among(concept_ids)[:6]:
                ad = self._adapt_association(
                    aid,
                    delta=CAP_ASSOC_STRENGTH * 0.7,
                    kind=AdaptationKind.REINFORCE,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                    summary="Reinforced association along reflective neighborhood.",
                )
                if ad:
                    created.append(ad)
            # Preference attribute confidence
            for cid in concept_ids:
                ads = self._adapt_preferences(
                    cid,
                    delta=CAP_PREF_CONFIDENCE * 0.6,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                )
                created.extend(ads)
            # Identity low-impact confidence
            for cid in concept_ids:
                concept = self.store.concepts.get(cid)
                if concept and concept.identity:
                    ad = self._adapt_identity_confidence(
                        cid,
                        delta=CAP_IDENTITY_CONFIDENCE * 0.5,
                        reflective_ids=[exp.id],
                        evidence_ids=evidence,
                        sleep_batch_id=sleep_batch_id,
                    )
                    if ad:
                        created.append(ad)
            if "pattern" in outcomes and len(concept_ids) >= 2:
                # Mild generalization: extra association reinforce among top pair
                pair = self._assoc_among(concept_ids[:3])
                for aid in pair[:2]:
                    ad = self._adapt_association(
                        aid,
                        delta=CAP_ASSOC_STRENGTH * 0.4,
                        kind=AdaptationKind.GENERALIZE,
                        reflective_ids=[exp.id],
                        evidence_ids=evidence,
                        sleep_batch_id=sleep_batch_id,
                        summary="Generalized pattern across related concepts.",
                    )
                    if ad:
                        created.append(ad)

        if weaken:
            for cid in concept_ids[:4]:
                ad = self._adapt_concept(
                    cid,
                    strength_delta=-CAP_CONCEPT_STRENGTH * 0.5,
                    confidence_delta=-CAP_CONCEPT_CONFIDENCE * 0.6,
                    kind=AdaptationKind.WEAKEN,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                    summary="Reduced confidence after reflective contradiction.",
                )
                if ad:
                    created.append(ad)
            for aid in self._assoc_among(concept_ids)[:4]:
                ad = self._adapt_association(
                    aid,
                    delta=-CAP_ASSOC_STRENGTH * 0.6,
                    kind=AdaptationKind.WEAKEN,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                    summary="Weakened association after contradiction.",
                )
                if ad:
                    created.append(ad)

        # High-impact proposals: identity merge-like signals stay proposed
        if weaken and any(
            (self.store.concepts[c].identity if c in self.store.concepts else False)
            for c in concept_ids
        ):
            prop = self._propose(
                target_kind=AdaptationTarget.IDENTITY_CONCEPT,
                target_id=concept_ids[0],
                kind=AdaptationKind.WEAKEN,
                reflective_ids=[exp.id],
                summary="High-impact identity contest requires assent.",
                sleep_batch_id=sleep_batch_id,
            )
            created.append(prop)

        return created

    def learn_from_cue(self, cue: str, *, reflective_experience_id: str = "") -> dict[str, Any]:
        """Apply learning from an existing Reflective Experience id (caller runs Reflection)."""
        if not reflective_experience_id:
            return {
                "question": "What have I learned?",
                "answer": "No Reflective Experience provided to learn from.",
                "adaptations": [],
            }
        adaptations = self.learn_from_reflection(reflective_experience_id)
        return {
            "cue": cue,
            "reflective_experience_id": reflective_experience_id,
            "adaptations": [a.to_public() for a in adaptations],
            "applied": sum(1 for a in adaptations if a.applied),
            "proposed": sum(
                1 for a in adaptations if a.governance == GovernanceClass.PROPOSED
            ),
            "abstained": sum(
                1 for a in adaptations if a.governance == GovernanceClass.ABSTAINED
            ),
        }

    def assent_adaptation(self, adaptation_id: str) -> dict[str, Any]:
        ad = self.store.adaptations.get(adaptation_id)
        if ad is None:
            return {"status": "missing"}
        if ad.governance != GovernanceClass.PROPOSED:
            return {"status": "not_proposed", "adaptation": ad.to_public()}
        # High-impact assent does not auto-mutate identity/concepts beyond recording assent
        ad.governance = GovernanceClass.ASSENTED
        ad.applied = True
        ad.metadata["assented_at"] = time()
        self.validation.record_learning(
            action="assent",
            adaptation_id=ad.id,
            target_kind=ad.target_kind.value,
            governance=ad.governance.value,
            assent=1,
        )
        return {"status": "assented", "adaptation": ad.to_public()}

    def reject_adaptation(self, adaptation_id: str) -> dict[str, Any]:
        ad = self.store.adaptations.get(adaptation_id)
        if ad is None:
            return {"status": "missing"}
        ad.governance = GovernanceClass.REJECTED
        ad.applied = False
        self.validation.record_learning(
            action="reject",
            adaptation_id=ad.id,
            reject=1,
        )
        return {"status": "rejected", "adaptation": ad.to_public()}

    def rollback_adaptation(self, adaptation_id: str) -> Adaptation | None:
        ad = self.store.adaptations.get(adaptation_id)
        if ad is None or not ad.applied or ad.governance == GovernanceClass.ABSTAINED:
            return None
        restored = self._restore(ad)
        if restored is None:
            return None
        self._rollbacks += 1
        return restored

    def stabilize_association(
        self,
        association_id: str,
        *,
        delta: float = 0.03,
        reflective_ids: list[str] | None = None,
        sleep_batch_id: str = "",
    ) -> Adaptation | None:
        """Offline/online helper — low-impact association stabilize via Learning."""
        return self._adapt_association(
            association_id,
            delta=delta,
            kind=AdaptationKind.STABILIZE,
            reflective_ids=list(reflective_ids or []),
            evidence_ids=[],
            sleep_batch_id=sleep_batch_id,
            summary="Stabilized association.",
        )

    def observables(self) -> dict[str, Any]:
        return {
            "adaptation_count": len(self.store.adaptations),
            "applied": self._applied,
            "proposed": self._proposed,
            "abstained": self._abstained,
            "rollbacks": self._rollbacks,
        }

    # --- internals ------------------------------------------------------------

    def _record_abstain(self, exp: Experience, *, sleep_batch_id: str) -> Adaptation:
        ad = Adaptation(
            id=new_id("adp"),
            kind=AdaptationKind.ABSTAIN,
            target_kind=AdaptationTarget.CONCEPT,
            target_id="",
            governance=GovernanceClass.ABSTAINED,
            reflective_experience_ids=[exp.id],
            evidence_experience_ids=[exp.reflects_on_id] if exp.reflects_on_id else [],
            sleep_batch_id=sleep_batch_id,
            summary="Abstained from adaptation due to insufficient evidence or uncertainty.",
            created=time(),
            applied=False,
        )
        self.store.adaptations[ad.id] = ad
        self._abstained += 1
        self.validation.record_learning(
            action="abstain",
            adaptation_id=ad.id,
            abstain=1,
            reflective_experience_id=exp.id,
        )
        return ad

    def _propose(
        self,
        *,
        target_kind: AdaptationTarget,
        target_id: str,
        kind: AdaptationKind,
        reflective_ids: list[str],
        summary: str,
        sleep_batch_id: str = "",
    ) -> Adaptation:
        ad = Adaptation(
            id=new_id("adp"),
            kind=kind,
            target_kind=target_kind,
            target_id=target_id,
            governance=GovernanceClass.PROPOSED,
            reflective_experience_ids=list(reflective_ids),
            sleep_batch_id=sleep_batch_id,
            summary=summary,
            created=time(),
            applied=False,
        )
        self.store.adaptations[ad.id] = ad
        self._proposed += 1
        self.validation.record_learning(
            action="propose",
            adaptation_id=ad.id,
            target_kind=target_kind.value,
            propose=1,
            governance="proposed",
        )
        return ad

    def _adapt_concept(
        self,
        concept_id: str,
        *,
        strength_delta: float,
        confidence_delta: float,
        kind: AdaptationKind,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
        summary: str,
    ) -> Adaptation | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None or not concept.active:
            return None
        strength_delta = max(-CAP_CONCEPT_STRENGTH, min(CAP_CONCEPT_STRENGTH, strength_delta))
        confidence_delta = max(
            -CAP_CONCEPT_CONFIDENCE, min(CAP_CONCEPT_CONFIDENCE, confidence_delta)
        )
        before = {"strength": concept.strength, "confidence": concept.confidence}
        concept.strength = max(0.0, min(1.0, concept.strength + strength_delta))
        concept.confidence = max(0.05, min(1.0, concept.confidence + confidence_delta))
        after = {"strength": concept.strength, "confidence": concept.confidence}
        ad = Adaptation(
            id=new_id("adp"),
            kind=kind,
            target_kind=AdaptationTarget.CONCEPT,
            target_id=concept_id,
            governance=GovernanceClass.AUTOMATIC,
            before=before,
            after=after,
            reflective_experience_ids=list(reflective_ids),
            evidence_experience_ids=list(evidence_ids),
            sleep_batch_id=sleep_batch_id,
            summary=summary,
            created=time(),
            applied=True,
        )
        self.store.adaptations[ad.id] = ad
        self._applied += 1
        self.validation.record_learning(
            action="apply",
            adaptation_id=ad.id,
            target_kind="concept",
            target_id=concept_id,
            kind=kind.value,
            apply=1,
            concept_evolution=1,
            confidence_evolution=1 if confidence_delta else 0,
            generalization=1 if kind == AdaptationKind.GENERALIZE else 0,
            sleep_batch_id=sleep_batch_id or "",
        )
        self.validation.record_confidence(
            ConfidenceDelta(
                time(),
                concept_id,
                "concept",
                before["confidence"],
                after["confidence"],
                "learning",
            )
        )
        return ad

    def _adapt_association(
        self,
        association_id: str,
        *,
        delta: float,
        kind: AdaptationKind,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
        summary: str,
    ) -> Adaptation | None:
        assoc = self.store.associations.get(association_id)
        if assoc is None or not assoc.active:
            return None
        delta = max(-CAP_ASSOC_STRENGTH, min(CAP_ASSOC_STRENGTH, delta))
        before = {
            "strength_forward": assoc.strength_forward,
            "strength_backward": assoc.strength_backward,
        }
        assoc.strength_forward = max(0.0, min(1.0, assoc.strength_forward + delta))
        assoc.strength_backward = max(0.0, min(1.0, assoc.strength_backward + delta * 0.8))
        sign = 1 if delta > 0 else -1
        assoc.confidence = max(
            0.05, min(1.0, assoc.confidence + abs(delta) * 0.3 * sign)
        )
        after = {
            "strength_forward": assoc.strength_forward,
            "strength_backward": assoc.strength_backward,
        }
        ad = Adaptation(
            id=new_id("adp"),
            kind=kind,
            target_kind=AdaptationTarget.ASSOCIATION,
            target_id=association_id,
            governance=GovernanceClass.AUTOMATIC,
            before=before,
            after=after,
            reflective_experience_ids=list(reflective_ids),
            evidence_experience_ids=list(evidence_ids),
            sleep_batch_id=sleep_batch_id,
            summary=summary,
            created=time(),
            applied=True,
        )
        self.store.adaptations[ad.id] = ad
        self._applied += 1
        self.validation.record_learning(
            action="apply",
            adaptation_id=ad.id,
            target_kind="association",
            target_id=association_id,
            kind=kind.value,
            apply=1,
            association_evolution=1,
            sleep_batch_id=sleep_batch_id or "",
        )
        return ad

    def _adapt_preferences(
        self,
        concept_id: str,
        *,
        delta: float,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
    ) -> list[Adaptation]:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return []
        if concept.role != ConceptRole.PREFERENCE and not any(
            a.key.startswith("favorite_") for a in concept.attributes if a.active
        ):
            return []
        out: list[Adaptation] = []
        delta = max(-CAP_PREF_CONFIDENCE, min(CAP_PREF_CONFIDENCE, delta))
        for attr in concept.attributes:
            if not attr.active:
                continue
            if not (
                attr.key.startswith("favorite_") or concept.role == ConceptRole.PREFERENCE
            ):
                continue
            before = {"confidence": attr.confidence}
            attr.confidence = max(0.05, min(1.0, attr.confidence + delta))
            after = {"confidence": attr.confidence}
            ad = Adaptation(
                id=new_id("adp"),
                kind=AdaptationKind.CONFIDENCE,
                target_kind=AdaptationTarget.PREFERENCE_ATTRIBUTE,
                target_id=concept_id,
                governance=GovernanceClass.AUTOMATIC,
                before=before,
                after=after,
                reflective_experience_ids=list(reflective_ids),
                evidence_experience_ids=list(evidence_ids),
                sleep_batch_id=sleep_batch_id,
                summary=f"Adjusted preference confidence for {attr.key}.",
                attribute_key=attr.key,
                created=time(),
                applied=True,
            )
            self.store.adaptations[ad.id] = ad
            self._applied += 1
            self.validation.record_learning(
                action="apply",
                adaptation_id=ad.id,
                target_kind="preference_attribute",
                apply=1,
                confidence_evolution=1,
            )
            out.append(ad)
            break  # one attribute per concept per reflection
        return out

    def _adapt_identity_confidence(
        self,
        concept_id: str,
        *,
        delta: float,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
    ) -> Adaptation | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None or not concept.identity:
            return None
        delta = max(-CAP_IDENTITY_CONFIDENCE, min(CAP_IDENTITY_CONFIDENCE, delta))
        before = {"confidence": concept.confidence}
        concept.confidence = max(0.05, min(1.0, concept.confidence + delta))
        after = {"confidence": concept.confidence}
        ad = Adaptation(
            id=new_id("adp"),
            kind=AdaptationKind.CONFIDENCE,
            target_kind=AdaptationTarget.IDENTITY_CONCEPT,
            target_id=concept_id,
            governance=GovernanceClass.AUTOMATIC,
            before=before,
            after=after,
            reflective_experience_ids=list(reflective_ids),
            evidence_experience_ids=list(evidence_ids),
            sleep_batch_id=sleep_batch_id,
            summary="Stabilized identity concept confidence from reflection.",
            created=time(),
            applied=True,
        )
        self.store.adaptations[ad.id] = ad
        self._applied += 1
        self.validation.record_learning(
            action="apply",
            adaptation_id=ad.id,
            target_kind="identity_concept",
            apply=1,
            identity_evolution=1,
            confidence_evolution=1,
        )
        return ad

    def _restore(self, ad: Adaptation) -> Adaptation | None:
        before = ad.before
        if ad.target_kind == AdaptationTarget.CONCEPT:
            c = self.store.concepts.get(ad.target_id)
            if c is None:
                return None
            cur = {"strength": c.strength, "confidence": c.confidence}
            c.strength = before.get("strength", c.strength)
            c.confidence = before.get("confidence", c.confidence)
        elif ad.target_kind == AdaptationTarget.ASSOCIATION:
            a = self.store.associations.get(ad.target_id)
            if a is None:
                return None
            cur = {
                "strength_forward": a.strength_forward,
                "strength_backward": a.strength_backward,
            }
            a.strength_forward = before.get("strength_forward", a.strength_forward)
            a.strength_backward = before.get("strength_backward", a.strength_backward)
        elif ad.target_kind == AdaptationTarget.PREFERENCE_ATTRIBUTE:
            c = self.store.concepts.get(ad.target_id)
            if c is None:
                return None
            attr = next((x for x in c.attributes if x.key == ad.attribute_key), None)
            if attr is None:
                return None
            cur = {"confidence": attr.confidence}
            attr.confidence = before.get("confidence", attr.confidence)
        elif ad.target_kind == AdaptationTarget.IDENTITY_CONCEPT:
            c = self.store.concepts.get(ad.target_id)
            if c is None:
                return None
            cur = {"confidence": c.confidence}
            c.confidence = before.get("confidence", c.confidence)
        else:
            return None
        rb = Adaptation(
            id=new_id("adp"),
            kind=AdaptationKind.ROLLBACK,
            target_kind=ad.target_kind,
            target_id=ad.target_id,
            governance=GovernanceClass.ROLLED_BACK,
            before=cur,
            after=dict(before),
            reflective_experience_ids=list(ad.reflective_experience_ids),
            summary=f"Rollback of {ad.id}",
            attribute_key=ad.attribute_key,
            created=time(),
            applied=True,
            metadata={"rolls_back": ad.id},
        )
        ad.governance = GovernanceClass.ROLLED_BACK
        self.store.adaptations[rb.id] = rb
        self.validation.record_learning(
            action="rollback",
            adaptation_id=rb.id,
            rollback=1,
            rolls_back=ad.id,
        )
        return rb

    def _assoc_among(self, concept_ids: list[str]) -> list[str]:
        ids = set(concept_ids)
        scored: list[tuple[float, str]] = []
        for a in self.store.associations.values():
            if a.source_id in ids and a.target_id in ids and a.active:
                scored.append((max(a.strength_forward, a.strength_backward), a.id))
        scored.sort(reverse=True)
        return [i for _, i in scored]


def _outcomes_from_meta(exp: Experience) -> list[str]:
    meta = exp.meta_dict()
    raw = meta.get("reflection_outcomes", "")
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]
