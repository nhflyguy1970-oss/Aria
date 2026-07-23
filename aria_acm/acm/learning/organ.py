"""Learning organ — answers: What have I learned?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.authority.mode import is_read_only
from acm.experiences.kinds import CognitiveKind
from acm.learning.model import (
    Adaptation,
    AdaptationKind,
    AdaptationTarget,
    GovernanceClass,
)
from acm.learning.temporal_pattern import PatternKind, PatternStatus, TemporalPattern
from acm.learning.stability import LearningStabilityLimits
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
        self._temporal_patterns = 0
        self._min_pattern_observations = 2
        self.stability_limits = LearningStabilityLimits()
        self._stability_interventions = 0

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
        if is_read_only():
            return []
        exp = self.store.experiences.get(reflective_experience_id)
        if exp is None:
            return []
        if exp.cognitive_kind != CognitiveKind.REFLECTION:
            return []
        # Cap7 — no recursive re-learning from the same Reflective Experience.
        if any(
            reflective_experience_id in a.reflective_experience_ids and a.applied
            for a in self.store.adaptations.values()
        ):
            self.validation.record_learning(
                action="skip_recursive_reflection",
                reflective_experience_id=reflective_experience_id,
                learn=0,
            )
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
                # Evidence-based hierarchy deepening (Concept organ owns taxonomy).
                for ad in self._adapt_hierarchy_from_reflection(
                    concept_ids,
                    reflective_ids=[exp.id],
                    evidence_ids=evidence,
                    sleep_batch_id=sleep_batch_id,
                ):
                    created.append(ad)
            # Goal importance nudge when reflective cue overlaps an active goal
            for ad in self._adapt_goals_from_reflection(
                exp,
                reinforce=True,
                reflective_ids=[exp.id],
                evidence_ids=evidence,
                sleep_batch_id=sleep_batch_id,
            ):
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
        """Gate B: apply a proposed high-impact adaptation after host/user assent.

        Mutates living structure only (strengths/confidence). Never invents or
        rewrites Experiences. Reversible via ``rollback_adaptation``.
        """
        if is_read_only():
            return {"status": "read_only_blocked"}
        ad = self.store.adaptations.get(adaptation_id)
        if ad is None:
            return {"status": "missing"}
        if ad.governance != GovernanceClass.PROPOSED:
            return {"status": "not_proposed", "adaptation": ad.to_public()}
        if not self._apply_proposed(ad):
            return {"status": "apply_failed", "adaptation": ad.to_public()}
        ad.governance = GovernanceClass.ASSENTED
        ad.applied = True
        ad.metadata["assented_at"] = time()
        self._applied += 1
        self.validation.record_learning(
            action="assent",
            adaptation_id=ad.id,
            target_kind=ad.target_kind.value,
            governance=ad.governance.value,
            assent=1,
            apply=1,
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

    def learn_from_prediction_audit(self, audit_id: str) -> list[Adaptation]:
        """Reversible living-structure updates from a PredictionAudit (Cap3).

        Never invents Experiences. Cites audit + observed evidence only.
        """
        if is_read_only():
            return []
        from acm.prediction.model import ComparisonKind

        audit = self.store.prediction_audits.get(audit_id)
        if audit is None:
            return []
        created: list[Adaptation] = []
        reinforce = audit.comparison in (ComparisonKind.HIT, ComparisonKind.PARTIAL)
        evidence = [e for e in (audit.observed_experience_id,) if e]
        cid = audit.observed_concept_id
        if cid and cid in self.store.concepts:
            ad = self._adapt_concept(
                cid,
                strength_delta=CAP_CONCEPT_STRENGTH * (0.7 if reinforce else -0.6),
                confidence_delta=CAP_CONCEPT_CONFIDENCE * (0.6 if reinforce else -0.7),
                kind=AdaptationKind.REINFORCE if reinforce else AdaptationKind.WEAKEN,
                reflective_ids=[],
                evidence_ids=evidence,
                sleep_batch_id="",
                summary=(
                    f"Prediction audit {audit.comparison.value}: "
                    f"calibrated living confidence from observed outcome."
                ),
            )
            if ad:
                ad.metadata["prediction_audit_id"] = audit_id
                created.append(ad)
            # Soft association nudge among prediction source neighborhood
            pred = self.store.predictions.get(audit.prediction_id)
            if pred and reinforce:
                for aid in self._assoc_among([cid, *pred.source_concept_ids[:3]])[:3]:
                    a2 = self._adapt_association(
                        aid,
                        delta=CAP_ASSOC_STRENGTH * 0.5,
                        kind=AdaptationKind.REINFORCE,
                        reflective_ids=[],
                        evidence_ids=evidence,
                        sleep_batch_id="",
                        summary="Reinforced association after prediction hit.",
                    )
                    if a2:
                        a2.metadata["prediction_audit_id"] = audit_id
                        created.append(a2)
            # Cap4: prediction outcomes strengthen/weaken supporting abstractions
            if self.concepts is not None:
                for abs_rec in list(self.store.abstractions.values()):
                    if cid not in abs_rec.supporting_concept_ids:
                        continue
                    if abs_rec.status.value in {"retired", "merged", "split"}:
                        continue
                    before_conf = abs_rec.confidence
                    self.concepts.reinforce_abstraction(
                        abs_rec.id,
                        evidence_ids=evidence,
                        audit_id=audit_id,
                        strengthen=reinforce,
                    )
                    ad_abs = self._adapt_concept(
                        cid,
                        strength_delta=CAP_CONCEPT_STRENGTH * (0.3 if reinforce else -0.25),
                        confidence_delta=0.0,
                        kind=AdaptationKind.GENERALIZE if reinforce else AdaptationKind.WEAKEN,
                        reflective_ids=[],
                        evidence_ids=evidence,
                        sleep_batch_id="",
                        summary=(
                            f"Abstraction '{abs_rec.label}' "
                            f"{'reinforced' if reinforce else 'weakened'} "
                            f"by prediction audit ({before_conf:.2f}→"
                            f"{self.store.abstractions[abs_rec.id].confidence:.2f})."
                        ),
                    )
                    if ad_abs:
                        ad_abs.metadata["prediction_audit_id"] = audit_id
                        ad_abs.metadata["abstraction_id"] = abs_rec.id
                        created.append(ad_abs)
        self.validation.record_learning(
            action="prediction_audit_learn",
            audit_id=audit_id,
            adaptation_count=len(created),
            comparison=audit.comparison.value,
            learn=1,
        )
        return created

    # --- M5 Cap5: Temporal Pattern Recognition --------------------------------

    def observe_temporal_pattern(
        self,
        *,
        antecedent: str,
        consequent: str,
        experience_id: str = "",
        concept_ids: list[str] | tuple[str, ...] = (),
        period_hint: str = "",
        kind: PatternKind | str = PatternKind.HABIT,
        label: str = "",
        now: float | None = None,
    ) -> dict[str, Any]:
        """Upsert an evidence-based temporal pattern. Never invents Experiences."""
        if is_read_only():
            return {"status": "read_only"}
        ante = " ".join((antecedent or "").strip().split())
        cons = " ".join((consequent or "").strip().split())
        if not ante or not cons:
            return {"status": "rejected", "reason": "missing_endpoints"}
        if experience_id and experience_id not in self.store.experiences:
            return {"status": "rejected", "reason": "unknown_experience"}
        now = time() if now is None else float(now)
        period = (period_hint or self._infer_period_hint(f"{ante} {cons}")).lower()
        kind_v = kind if isinstance(kind, PatternKind) else PatternKind(str(kind))
        key = f"{ante.casefold()}=>{cons.casefold()}|{period}"
        existing = None
        for p in self.store.temporal_patterns.values():
            pk = f"{p.antecedent.casefold()}=>{p.consequent.casefold()}|{p.period_hint}"
            if pk == key:
                existing = p
                break
        lim = self.stability_limits
        if existing is None:
            active_n = sum(
                1
                for p in self.store.temporal_patterns.values()
                if p.status != PatternStatus.RETIRED
            )
            if active_n >= lim.max_temporal_patterns:
                return {
                    "status": "rejected",
                    "reason": "temporal_pattern_cap",
                    "invents_experiences": False,
                }
            pat = TemporalPattern(
                id=new_id("tpat"),
                label=label or f"{ante} → {cons}",
                kind=kind_v,
                status=PatternStatus.ACTIVE,
                antecedent=ante,
                consequent=cons,
                period_hint=period,
                confidence=0.35,
                strength=0.35,
                observation_count=1,
                supporting_experience_ids=[experience_id] if experience_id else [],
                supporting_concept_ids=[c for c in concept_ids if c in self.store.concepts][:8],
                first_observed=now,
                last_observed=now,
                metadata={"key": key},
            )
            self.store.temporal_patterns[pat.id] = pat
            self._temporal_patterns += 1
            self.validation.record_learning(
                action="temporal_pattern_observe",
                pattern_id=pat.id,
                observation_count=1,
                learn=1,
            )
            return {"status": "formed", "pattern": pat.to_public()}
        # Reinforce existing
        before = existing.confidence
        if experience_id and experience_id not in existing.supporting_experience_ids:
            existing.supporting_experience_ids.append(experience_id)
        for cid in concept_ids:
            if cid in self.store.concepts and cid not in existing.supporting_concept_ids:
                existing.supporting_concept_ids.append(cid)
        existing.observation_count += 1
        existing.last_observed = now
        # Pattern confidence stays slightly below hard stability max (calibration).
        existing.strength = min(0.95, min(lim.max_confidence, existing.strength + 0.08))
        existing.confidence = min(0.92, min(lim.max_confidence, existing.confidence + 0.06))

        if existing.status in {PatternStatus.WEAKENING, PatternStatus.DORMANT}:
            existing.status = PatternStatus.ACTIVE
        if (
            existing.observation_count >= self._min_pattern_observations
            and len(existing.supporting_experience_ids) >= 1
        ):
            existing.kind = kind_v if existing.kind == PatternKind.HABIT else existing.kind
        self.validation.record_learning(
            action="temporal_pattern_reinforce",
            pattern_id=existing.id,
            confidence_before=before,
            confidence_after=existing.confidence,
            learn=1,
        )
        return {
            "status": "reinforced",
            "pattern": existing.to_public(),
            "confidence_before": before,
            "confidence_after": existing.confidence,
        }

    def age_temporal_patterns(
        self,
        *,
        now: float | None = None,
        weaken_idle_s: float = 14 * 86400,
        dormant_idle_s: float = 45 * 86400,
        retire_idle_s: float = 120 * 86400,
    ) -> dict[str, Any]:
        """Weaken patterns no longer observed. Never deletes Experiences/provenance."""
        if is_read_only():
            return {"status": "read_only", "weakened": 0}
        now = time() if now is None else float(now)
        exp_before = len(self.store.experiences)
        prov_before = len(self.store.provenance)
        weakened = dormant = retired = 0
        for pat in self.store.temporal_patterns.values():
            if pat.status == PatternStatus.RETIRED:
                continue
            idle = now - float(pat.last_observed or pat.first_observed or now)
            if idle < weaken_idle_s:
                continue
            before = pat.confidence
            # Soft exponential-ish decay of strength/confidence
            steps = max(1, int(idle / max(weaken_idle_s, 1.0)))
            decay = min(0.5, 0.08 * steps)
            pat.strength = max(0.05, pat.strength - decay)
            pat.confidence = max(0.05, pat.confidence - decay * 0.9)
            pat.last_weakened = now
            if idle >= retire_idle_s and pat.confidence <= 0.15:
                pat.status = PatternStatus.RETIRED
                pat.retired_at = now
                retired += 1
            elif idle >= dormant_idle_s:
                pat.status = PatternStatus.DORMANT
                dormant += 1
            else:
                pat.status = PatternStatus.WEAKENING
                weakened += 1
            self.validation.record_learning(
                action="temporal_pattern_age",
                pattern_id=pat.id,
                confidence_before=before,
                confidence_after=pat.confidence,
                status=pat.status.value,
                learn=1,
            )
        assert len(self.store.experiences) == exp_before
        assert len(self.store.provenance) == prov_before
        return {
            "status": "aged",
            "weakened": weakened,
            "dormant": dormant,
            "retired": retired,
            "experiences_unchanged": True,
            "provenance_unchanged": True,
        }

    def explain_temporal_pattern(self, cue_or_id: str = "") -> dict[str, Any]:
        """Why does this routine/habit exist? Evidence and confidence trajectory."""
        pat = self.store.temporal_patterns.get(cue_or_id)
        if pat is None:
            q = (cue_or_id or "").casefold()
            matches = [
                p
                for p in self.store.temporal_patterns.values()
                if not q
                or q in p.label.casefold()
                or q in p.antecedent.casefold()
                or q in p.consequent.casefold()
                or q in p.period_hint
            ]
            matches.sort(key=lambda p: p.confidence, reverse=True)
            pat = matches[0] if matches else None
        if pat is None:
            return {
                "question": "What temporal pattern is this?",
                "known": False,
                "answer": "I don't have an evidence-based temporal pattern for that yet.",
                "invents_experiences": False,
            }
        return {
            "question": "What temporal pattern is this?",
            "known": True,
            "answer": (
                f"Pattern '{pat.label}' ({pat.kind.value}/{pat.status.value}): "
                f"when '{pat.antecedent}' then '{pat.consequent}'"
                + (f" ({pat.period_hint})" if pat.period_hint else "")
                + f" — confidence {pat.confidence:.0%} from "
                f"{pat.observation_count} observation(s)."
            ),
            "supporting_experiences": list(pat.supporting_experience_ids),
            "confidence": pat.confidence,
            "last_observed": pat.last_observed,
            "last_weakened": pat.last_weakened,
            "status": pat.status.value,
            "weakens_when_unobserved": True,
            "pattern": pat.to_public(),
            "invents_experiences": False,
        }

    def list_temporal_patterns(
        self, *, include_dormant: bool = False, cue: str = ""
    ) -> dict[str, Any]:
        items = list(self.store.temporal_patterns.values())
        if not include_dormant:
            items = [
                p
                for p in items
                if p.status in {PatternStatus.ACTIVE, PatternStatus.WEAKENING}
            ]
        if cue:
            q = cue.casefold()
            items = [
                p
                for p in items
                if q in p.label.casefold()
                or q in p.antecedent.casefold()
                or q in p.consequent.casefold()
                or q in p.period_hint
            ]
        items.sort(key=lambda p: (p.confidence, p.observation_count), reverse=True)
        return {
            "question": "What routines or temporal patterns do I have?",
            "patterns": [p.to_public() for p in items[:24]],
            "count": len(items),
            "answer": (
                "; ".join(p.label for p in items[:5])
                if items
                else "No active temporal patterns learned yet."
            ),
            "invents_experiences": False,
        }

    def discover_patterns_from_predictive_experiences(self) -> list[dict[str, Any]]:
        """Materialize TemporalPatterns from existing predictive Experiences (no invention)."""
        created: list[dict[str, Any]] = []
        for exp in self.store.experiences.values():
            meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
            if not isinstance(meta, dict) or meta.get("predictive") != "1":
                continue
            ante = str(meta.get("pattern_antecedent") or "").strip()
            cons = str(meta.get("pattern_consequent") or "").strip()
            if not ante or not cons:
                continue
            out = self.observe_temporal_pattern(
                antecedent=ante,
                consequent=cons,
                experience_id=exp.id,
                period_hint=self._infer_period_hint(f"{ante} {cons} {exp.summary or ''}"),
                kind=PatternKind.RECURRING,
                now=float(exp.t_start or exp.created or time()),
            )
            if out.get("status") in {"formed", "reinforced"}:
                created.append(out["pattern"])
        return created

    def _infer_period_hint(self, text: str) -> str:
        t = (text or "").casefold()
        for token, hint in (
            ("saturday", "saturday"),
            ("sunday", "sunday"),
            ("weekend", "weekend"),
            ("weekday", "weekday"),
            ("morning", "morning"),
            ("afternoon", "afternoon"),
            ("evening", "evening"),
            ("night", "night"),
            ("winter", "seasonal"),
            ("summer", "seasonal"),
            ("spring", "seasonal"),
            ("autumn", "seasonal"),
            ("fall", "seasonal"),
            ("every week", "weekly"),
            ("weekly", "weekly"),
            ("daily", "daily"),
            ("every day", "daily"),
            ("monthly", "monthly"),
        ):
            if token in t:
                return hint
        return "recurring"

    # --- M5 Cap6: Learning Explainability -------------------------------------

    def explain_learning(self, cue_or_id: str = "") -> dict[str, Any]:
        """Unified learning explainability — public language only, provenance preserved.

        Answers why a learned object exists using adaptations, evidence, confidence
        history, abstractions, predictions/hypotheses, temporal patterns, reflection,
        consolidation, and adoption — without exposing implementation internals.
        """
        concept = self._resolve_explain_concept(cue_or_id)
        if concept is None and cue_or_id:
            # Try abstraction / pattern / hypothesis / prediction ids directly
            direct = self._explain_by_artifact_id(cue_or_id)
            if direct is not None:
                return direct
        if concept is None:
            return {
                "question": "Why was this learned?",
                "known": False,
                "answer": "I don't have a learned object matching that yet.",
                "invents_experiences": False,
                "exposes_internals": False,
            }

        cid = concept.id
        label = concept.labels[0] if concept.labels else cid
        adaptations = [
            a
            for a in self.store.adaptations.values()
            if a.target_id == cid
            or cid in (a.metadata or {}).values()
            or any(
                cid == str(v)
                for v in (a.metadata or {}).values()
                if isinstance(v, str)
            )
        ]
        adaptations.sort(key=lambda a: a.created)
        conf_hist = [
            {
                "when": e.timestamp,
                "before": round(e.before, 4),
                "after": round(e.after, 4),
                "source": e.source,
                "summary": e.summary,
                "increased": e.after > e.before,
                "decreased": e.after < e.before,
            }
            for e in self.store.confidence_events
            if e.target_id == cid
        ][-24:]
        supporting_experiences = list(concept.evidence_ids)[-16:]
        conflicting: list[str] = []
        for a in adaptations:
            if a.kind.value == "weaken":
                conflicting.extend(a.evidence_experience_ids[-4:])
        conflicting = list(dict.fromkeys(conflicting))

        related_abs = [
            abs_rec.to_public()
            for abs_rec in self.store.abstractions.values()
            if cid in abs_rec.supporting_concept_ids
        ][:8]
        related_patterns = [
            p.to_public()
            for p in self.store.temporal_patterns.values()
            if cid in p.supporting_concept_ids
            or label.casefold() in p.consequent.casefold()
            or label.casefold() in p.antecedent.casefold()
        ][:8]
        related_hyps = [
            h.to_public()
            for h in self.store.hypotheses.values()
            if h.concept_id == cid
            or label.casefold() in h.claim.casefold()
        ][:8]
        related_audits = []
        for aud in self.store.prediction_audits.values():
            if aud.observed_concept_id == cid:
                related_audits.append(aud.to_public())
        related_audits = related_audits[-8:]
        related_preds = [
            p.to_public()
            for p in self.store.predictions.values()
            if cid in p.source_concept_ids
            or any(o.concept_id == cid for o in p.outcomes)
        ][-6:]

        reflective = []
        for a in adaptations:
            reflective.extend(a.reflective_experience_ids)
        reflective = list(dict.fromkeys(reflective))[:12]
        sleep_batches = list(
            dict.fromkeys(
                a.sleep_batch_id for a in adaptations if a.sleep_batch_id
            )
        )[:8]
        adopted = [
            a.to_public()
            for a in adaptations
            if (a.metadata or {}).get("adopted")
            or "adopt" in (a.summary or "").casefold()
            or (a.metadata or {}).get("knowledge_adoption")
        ][:6]
        # Provenance for supporting experiences
        provenance_ids = []
        for eid in supporting_experiences[:8]:
            for p in self.store.provenance_for(eid):
                provenance_ids.append(p.id)

        why = (
            f"'{label}' was learned from {len(supporting_experiences)} supporting "
            f"Experience(s)"
            + (
                f" and {len(adaptations)} learning adaptation(s)"
                if adaptations
                else ""
            )
            + f"; current confidence about {concept.confidence:.0%}."
        )
        if conf_hist:
            last = conf_hist[-1]
            why += (
                f" Confidence last changed {last['before']:.0%}→{last['after']:.0%}"
                f" ({last['source']})."
            )

        reversible = any(
            a.applied and a.kind.value != "abstain" for a in adaptations
        )
        return {
            "question": "Why was this learned?",
            "known": True,
            "answer": why,
            "why_exists": why,
            "label": label,
            "concept_id": cid,
            "supporting_evidence": supporting_experiences,
            "conflicting_evidence": conflicting,
            "supporting_experiences": supporting_experiences,
            "supporting_concepts": [cid],
            "supporting_abstractions": related_abs,
            "supporting_predictions": related_preds,
            "supporting_hypotheses": related_hyps,
            "prediction_history": related_audits,
            "hypothesis_history": related_hyps,
            "abstraction_history": related_abs,
            "confidence_history": conf_hist,
            "confidence": round(concept.confidence, 4),
            "confidence_increased": any(h["increased"] for h in conf_hist),
            "confidence_decreased": any(h["decreased"] for h in conf_hist),
            "temporal_pattern_influence": related_patterns,
            "knowledge_adoption_history": adopted,
            "reflection_influence": reflective,
            "consolidation_influence": sleep_batches,
            "adaptations": [a.to_public() for a in adaptations[-12:]],
            "provenance_ids": provenance_ids[:16],
            "has_evolved": len(adaptations) > 1 or len(conf_hist) > 1,
            "reversible": reversible,
            "why_reversible": (
                "Applied adaptations can be rolled back to prior living-structure "
                "snapshots; Experiences and provenance remain immutable."
                if reversible
                else "No reversible adaptation is recorded for this object yet."
            ),
            "invents_experiences": False,
            "exposes_internals": False,
            "plans": False,
            "decides": False,
        }

    def why_was_this_learned(self, cue_or_id: str = "") -> dict[str, Any]:
        """Cognitive alias for Cap6 explain_learning."""
        return self.explain_learning(cue_or_id)

    def _resolve_explain_concept(self, cue_or_id: str):
        if not cue_or_id:
            return None
        concept = self.store.concepts.get(cue_or_id)
        if concept is not None:
            return concept
        matches = self.store.find_concepts_by_label(cue_or_id)
        if matches:
            return matches[0]
        q = cue_or_id.casefold()
        for c in self.store.concepts.values():
            if any(q in lab.casefold() for lab in c.labels):
                return c
            if q in " ".join(c.labels).casefold():
                return c
        return None

    def _explain_by_artifact_id(self, artifact_id: str) -> dict[str, Any] | None:
        if artifact_id in self.store.abstractions and self.concepts is not None:
            return {
                **self.concepts.explain_abstraction(artifact_id),
                "question": "Why was this learned?",
                "exposes_internals": False,
            }
        if artifact_id in self.store.temporal_patterns:
            return {
                **self.explain_temporal_pattern(artifact_id),
                "question": "Why was this learned?",
                "exposes_internals": False,
            }
        if artifact_id in self.store.hypotheses:
            hyp = self.store.hypotheses[artifact_id]
            return {
                "question": "Why was this learned?",
                "known": True,
                "answer": (
                    f"Hypothesis '{hyp.claim}' is {hyp.status.value} "
                    f"(confidence {hyp.confidence:.0%})."
                ),
                "supporting_evidence": list(hyp.supporting_ids),
                "conflicting_evidence": list(hyp.conflicting_ids),
                "hypothesis_history": [hyp.to_public()],
                "invents_experiences": False,
                "exposes_internals": False,
            }
        if artifact_id in self.store.prediction_audits:
            aud = self.store.prediction_audits[artifact_id]
            return {
                "question": "Why was this learned?",
                "known": True,
                "answer": aud.explanation,
                "prediction_history": [aud.to_public()],
                "invents_experiences": False,
                "exposes_internals": False,
            }
        if artifact_id in self.store.adaptations:
            ad = self.store.adaptations[artifact_id]
            return {
                "question": "Why was this learned?",
                "known": True,
                "answer": ad.summary or f"Adaptation {ad.kind.value} recorded.",
                "adaptations": [ad.to_public()],
                "supporting_evidence": list(ad.evidence_experience_ids),
                "reflection_influence": list(ad.reflective_experience_ids),
                "consolidation_influence": [ad.sleep_batch_id] if ad.sleep_batch_id else [],
                "reversible": ad.applied,
                "invents_experiences": False,
                "exposes_internals": False,
            }
        return None

    def observables(self) -> dict[str, Any]:
        return {
            "adaptation_count": len(self.store.adaptations),
            "applied": self._applied,
            "proposed": self._proposed,
            "abstained": self._abstained,
            "rollbacks": self._rollbacks,
            "temporal_patterns": len(self.store.temporal_patterns),
            "temporal_pattern_ops": self._temporal_patterns,
            "stability_interventions": self._stability_interventions,
        }

    # --- M5 Cap7: Learning Stability ------------------------------------------

    def check_learning_stability(self) -> dict[str, Any]:
        """Read-only stability report — bounded confidence, growth, oscillation."""
        lim = self.stability_limits
        confidences = [
            c.confidence for c in self.store.concepts.values() if c.active
        ]
        over = sum(1 for v in confidences if v > lim.max_confidence + 1e-9)
        under = sum(1 for v in confidences if v < lim.min_confidence - 1e-9)
        flips: dict[str, int] = {}
        last_dir: dict[str, int] = {}
        for e in self.store.confidence_events[-400:]:
            delta = e.after - e.before
            if abs(delta) < lim.oscillation_epsilon:
                continue
            direction = 1 if delta > 0 else -1
            prev = last_dir.get(e.target_id)
            if prev is not None and prev != direction:
                flips[e.target_id] = flips.get(e.target_id, 0) + 1
            last_dir[e.target_id] = direction
        oscillating = {
            tid: n for tid, n in flips.items() if n >= lim.max_oscillation_flips
        }
        growth = {
            "concepts": len(self.store.concepts),
            "adaptations": len(self.store.adaptations),
            "abstractions": len(self.store.abstractions),
            "hypotheses": len(self.store.hypotheses),
            "temporal_patterns": len(self.store.temporal_patterns),
            "prediction_audits": len(self.store.prediction_audits),
        }
        breaches: list[str] = []
        if growth["concepts"] > lim.max_concepts:
            breaches.append("concepts")
        if growth["adaptations"] > lim.max_adaptations_total:
            breaches.append("adaptations")
        if growth["abstractions"] > lim.max_abstractions:
            breaches.append("abstractions")
        if growth["hypotheses"] > lim.max_hypotheses:
            breaches.append("hypotheses")
        if growth["temporal_patterns"] > lim.max_temporal_patterns:
            breaches.append("temporal_patterns")
        if growth["prediction_audits"] > lim.max_prediction_audits:
            breaches.append("prediction_audits")
        if over or under:
            breaches.append("confidence_bounds")
        if oscillating:
            breaches.append("oscillation")
        return {
            "question": "Is learning stable?",
            "stable": not breaches,
            "breaches": breaches,
            "growth": growth,
            "confidence_over_max": over,
            "confidence_under_min": under,
            "oscillating_targets": list(oscillating.keys())[:12],
            "limits": {
                "min_confidence": lim.min_confidence,
                "max_confidence": lim.max_confidence,
                "max_concepts": lim.max_concepts,
                "max_abstractions": lim.max_abstractions,
                "max_hypotheses": lim.max_hypotheses,
                "max_temporal_patterns": lim.max_temporal_patterns,
            },
            "invents_experiences": False,
            "experiences": len(self.store.experiences),
            "provenance": len(self.store.provenance),
            "exposes_internals": False,
        }

    def enforce_learning_stability(self) -> dict[str, Any]:
        """Clamp confidence and cool runaway living structure. Never invents Experiences."""
        if is_read_only():
            return {"status": "read_only"}
        lim = self.stability_limits
        exp_before = len(self.store.experiences)
        prov_before = len(self.store.provenance)
        clamped = 0
        cooled = 0
        for c in self.store.concepts.values():
            if not c.active:
                continue
            before = c.confidence
            c.confidence = max(lim.min_confidence, min(lim.max_confidence, c.confidence))
            if abs(c.confidence - before) > 1e-12:
                clamped += 1
        by_target: dict[str, list] = {}
        for a in self.store.adaptations.values():
            by_target.setdefault(a.target_id, []).append(a)
        for _tid, ads in by_target.items():
            if len(ads) <= lim.max_adaptations_per_target:
                continue
            ads.sort(key=lambda a: a.created)
            for a in ads[: -lim.max_adaptations_per_target]:
                a.metadata["stability_cooled"] = True
                cooled += 1
        pats = sorted(
            self.store.temporal_patterns.values(),
            key=lambda p: p.last_observed,
        )
        if len(pats) > lim.max_temporal_patterns:
            for p in pats[: len(pats) - lim.max_temporal_patterns]:
                if p.status != PatternStatus.RETIRED:
                    p.status = PatternStatus.RETIRED
                    p.retired_at = time()
                    cooled += 1
        hyps = list(self.store.hypotheses.values())
        if len(hyps) > lim.max_hypotheses:
            closed = [h for h in hyps if h.status.value != "active"]
            closed.sort(key=lambda h: h.created)
            for h in closed[: max(0, len(hyps) - lim.max_hypotheses)]:
                h.metadata["stability_cooled"] = True
                cooled += 1
        self._stability_interventions += 1
        assert len(self.store.experiences) == exp_before
        assert len(self.store.provenance) == prov_before
        report = self.check_learning_stability()
        return {
            "status": "enforced",
            "clamped_confidence": clamped,
            "cooled": cooled,
            "report": report,
            "experiences_unchanged": True,
            "provenance_unchanged": True,
            "invents_experiences": False,
            "exposes_internals": False,
        }

    def daily_learning_summary(self, since_ts: float = 0.0) -> dict[str, Any]:
        """Read-only aggregation of Adaptation Records since ``since_ts``.

        Hosts call this after ``sleep()``/``learn()``; no timer lives in ACM core.
        Never invents memories — reports existing adaptations only.
        """
        items = [
            a
            for a in self.store.adaptations.values()
            if float(a.created or 0.0) >= float(since_ts or 0.0)
        ]
        by_kind: dict[str, int] = {}
        by_gov: dict[str, int] = {}
        for a in items:
            by_kind[a.kind.value] = by_kind.get(a.kind.value, 0) + 1
            by_gov[a.governance.value] = by_gov.get(a.governance.value, 0) + 1
        return {
            "schema": "acm.daily_learning_summary.v1",
            "since_ts": float(since_ts or 0.0),
            "adaptation_count": len(items),
            "applied": sum(1 for a in items if a.applied),
            "proposed": sum(1 for a in items if a.governance == GovernanceClass.PROPOSED),
            "abstained": sum(1 for a in items if a.governance == GovernanceClass.ABSTAINED),
            "by_kind": by_kind,
            "by_governance": by_gov,
            "adaptation_ids": [a.id for a in sorted(items, key=lambda x: x.created)[:50]],
            "read_only": True,
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
        attribute_key: str = "",
    ) -> Adaptation:
        before, after = self._plan_proposal_delta(
            target_kind=target_kind,
            target_id=target_id,
            kind=kind,
            attribute_key=attribute_key,
        )
        ad = Adaptation(
            id=new_id("adp"),
            kind=kind,
            target_kind=target_kind,
            target_id=target_id,
            governance=GovernanceClass.PROPOSED,
            before=before,
            after=after,
            reflective_experience_ids=list(reflective_ids),
            sleep_batch_id=sleep_batch_id,
            summary=summary,
            attribute_key=attribute_key,
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

    def _plan_proposal_delta(
        self,
        *,
        target_kind: AdaptationTarget,
        target_id: str,
        kind: AdaptationKind,
        attribute_key: str = "",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Snapshot before + planned after for a high-impact proposal (no mutation)."""
        sign = -1.0 if kind in {AdaptationKind.WEAKEN} else 1.0
        if target_kind == AdaptationTarget.CONCEPT:
            c = self.store.concepts.get(target_id)
            if c is None:
                return {}, {}
            before = {"strength": float(c.strength), "confidence": float(c.confidence)}
            after = {
                "strength": max(0.0, min(1.0, c.strength + sign * CAP_CONCEPT_STRENGTH)),
                "confidence": max(0.05, min(1.0, c.confidence + sign * CAP_CONCEPT_CONFIDENCE)),
            }
            return before, after
        if target_kind == AdaptationTarget.ASSOCIATION:
            a = self.store.associations.get(target_id)
            if a is None:
                return {}, {}
            before = {
                "strength_forward": float(a.strength_forward),
                "strength_backward": float(a.strength_backward),
            }
            after = {
                "strength_forward": max(
                    0.0, min(1.0, a.strength_forward + sign * CAP_ASSOC_STRENGTH)
                ),
                "strength_backward": max(
                    0.0, min(1.0, a.strength_backward + sign * CAP_ASSOC_STRENGTH * 0.8)
                ),
            }
            return before, after
        if target_kind == AdaptationTarget.PREFERENCE_ATTRIBUTE:
            c = self.store.concepts.get(target_id)
            if c is None:
                return {}, {}
            attr = next((x for x in c.attributes if x.key == attribute_key and x.active), None)
            if attr is None:
                return {}, {}
            before = {"confidence": float(attr.confidence)}
            after = {
                "confidence": max(
                    0.05, min(1.0, attr.confidence + sign * CAP_PREF_CONFIDENCE)
                )
            }
            return before, after
        if target_kind == AdaptationTarget.IDENTITY_CONCEPT:
            c = self.store.concepts.get(target_id)
            if c is None:
                return {}, {}
            before = {"confidence": float(c.confidence)}
            after = {
                "confidence": max(
                    0.05, min(1.0, c.confidence + sign * CAP_IDENTITY_CONFIDENCE)
                )
            }
            return before, after
        if target_kind == AdaptationTarget.GOAL:
            goal = self.store.goals.get(target_id) if hasattr(self.store, "goals") else None
            if goal is None:
                return {}, {}
            importance = float(getattr(goal, "importance", 0.5) or 0.5)
            before = {"importance": importance}
            after = {
                "importance": max(0.0, min(1.0, importance + sign * CAP_GOAL_IMPORTANCE))
            }
            return before, after
        return {}, {}

    def _apply_proposed(self, ad: Adaptation) -> bool:
        """Apply planned ``after`` snapshot to the living target. Never births Experiences."""
        if not ad.after:
            before, after = self._plan_proposal_delta(
                target_kind=ad.target_kind,
                target_id=ad.target_id,
                kind=ad.kind,
                attribute_key=ad.attribute_key,
            )
            if not after:
                return False
            if not ad.before:
                ad.before = before
            ad.after = after

        if ad.target_kind == AdaptationTarget.CONCEPT:
            c = self.store.concepts.get(ad.target_id)
            if c is None or not c.active:
                return False
            if not ad.before:
                ad.before = {"strength": float(c.strength), "confidence": float(c.confidence)}
            c.strength = float(ad.after.get("strength", c.strength))
            c.confidence = float(ad.after.get("confidence", c.confidence))
            return True
        if ad.target_kind == AdaptationTarget.ASSOCIATION:
            a = self.store.associations.get(ad.target_id)
            if a is None or not a.active:
                return False
            if not ad.before:
                ad.before = {
                    "strength_forward": float(a.strength_forward),
                    "strength_backward": float(a.strength_backward),
                }
            a.strength_forward = float(ad.after.get("strength_forward", a.strength_forward))
            a.strength_backward = float(ad.after.get("strength_backward", a.strength_backward))
            return True
        if ad.target_kind == AdaptationTarget.PREFERENCE_ATTRIBUTE:
            c = self.store.concepts.get(ad.target_id)
            if c is None:
                return False
            attr = next((x for x in c.attributes if x.key == ad.attribute_key), None)
            if attr is None:
                return False
            if not ad.before:
                ad.before = {"confidence": float(attr.confidence)}
            attr.confidence = float(ad.after.get("confidence", attr.confidence))
            return True
        if ad.target_kind == AdaptationTarget.IDENTITY_CONCEPT:
            c = self.store.concepts.get(ad.target_id)
            if c is None:
                return False
            if not ad.before:
                ad.before = {"confidence": float(c.confidence)}
            c.confidence = float(ad.after.get("confidence", c.confidence))
            self.validation.record_confidence(
                ConfidenceDelta(
                    time(),
                    ad.target_id,
                    "identity_concept",
                    ad.before.get("confidence", c.confidence),
                    c.confidence,
                    "learning_assent",
                )
            )
            return True
        if ad.target_kind == AdaptationTarget.GOAL:
            goal = self.store.goals.get(ad.target_id) if hasattr(self.store, "goals") else None
            if goal is None:
                return False
            if not ad.before:
                ad.before = {"importance": float(getattr(goal, "importance", 0.5) or 0.5)}
            goal.importance = float(ad.after.get("importance", getattr(goal, "importance", 0.5)))
            return True
        return False

    def _adapt_goals_from_reflection(
        self,
        exp: Experience,
        *,
        reinforce: bool,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
    ) -> list[Adaptation]:
        """Nudge active goal importance when reflection text overlaps the goal title.

        Low-impact automatic (Gate A). Never invents goals or Experiences.
        """
        if not reinforce:
            return []
        meta = exp.metadata
        if isinstance(meta, dict):
            meta_blob = " ".join(str(v) for v in meta.values())
        else:
            meta_blob = str(meta or "")
        blob = f"{exp.summary or ''} {meta_blob}".lower()
        out: list[Adaptation] = []
        for goal in list(self.store.active_goals())[:8]:
            title = (goal.title or "").strip()
            if len(title) < 3:
                continue
            tokens = [t for t in title.lower().split() if len(t) >= 3]
            if not tokens:
                continue
            if not any(t in blob for t in tokens):
                continue
            ad = self._adapt_goal(
                goal.id,
                delta=CAP_GOAL_IMPORTANCE * 0.75,
                reflective_ids=reflective_ids,
                evidence_ids=evidence_ids,
                sleep_batch_id=sleep_batch_id,
                summary=f"Increased importance of goal '{title}' from reflection.",
            )
            if ad:
                out.append(ad)
                break
        return out

    def _adapt_goal(
        self,
        goal_id: str,
        *,
        delta: float,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
        summary: str,
    ) -> Adaptation | None:
        goal = self.store.goals.get(goal_id)
        if goal is None or getattr(goal, "status", "active") != "active":
            return None
        delta = max(-CAP_GOAL_IMPORTANCE, min(CAP_GOAL_IMPORTANCE, delta))
        before = {"importance": float(goal.importance)}
        goal.importance = max(0.0, min(1.0, float(goal.importance) + delta))
        after = {"importance": float(goal.importance)}
        ad = Adaptation(
            id=new_id("adp"),
            kind=AdaptationKind.REINFORCE if delta >= 0 else AdaptationKind.WEAKEN,
            target_kind=AdaptationTarget.GOAL,
            target_id=goal_id,
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
            target_kind="goal",
            target_id=goal_id,
            apply=1,
            goal_evolution=1,
            sleep_batch_id=sleep_batch_id or "",
        )
        return ad

    def _adapt_hierarchy_from_reflection(
        self,
        concept_ids: list[str],
        *,
        reflective_ids: list[str],
        evidence_ids: list[str],
        sleep_batch_id: str,
    ) -> list[Adaptation]:
        """Deepen taxonomy via ConceptOrgan when siblings share an evidenced parent.

        Learning coordinates only — never invents Concepts or Experiences.
        """
        if self.concepts is None:
            return []
        created: list[Adaptation] = []
        # Group by existing parents among the reflective neighborhood.
        by_parent: dict[str, list[str]] = {}
        orphans: list[str] = []
        for cid in concept_ids:
            concept = self.store.concepts.get(cid)
            if concept is None or not concept.active:
                continue
            if concept.parent_ids:
                for pid in concept.parent_ids[:2]:
                    by_parent.setdefault(pid, []).append(cid)
            else:
                orphans.append(cid)
        # Reinforce existing parent links with reflective evidence.
        for pid, kids in by_parent.items():
            if pid not in self.store.concepts:
                continue
            for kid in kids[:4]:
                before_edge = None
                for e in self.concepts.hierarchy.values():
                    if e.child_id == kid and e.parent_id == pid:
                        before_edge = e
                        break
                before_w = before_edge.weight if before_edge else 0.0
                edge = self.concepts.link_is_a(
                    kid,
                    pid,
                    weight=0.5,
                    evidence_ids=tuple(evidence_ids[-4:]),
                )
                if edge is None:
                    continue
                ad = Adaptation(
                    id=new_id("adp"),
                    kind=AdaptationKind.GENERALIZE,
                    target_kind=AdaptationTarget.CONCEPT,
                    target_id=kid,
                    governance=GovernanceClass.AUTOMATIC,
                    before={"hierarchy_weight": before_w},
                    after={"hierarchy_weight": edge.weight},
                    reflective_experience_ids=list(reflective_ids),
                    evidence_experience_ids=list(evidence_ids),
                    sleep_batch_id=sleep_batch_id,
                    summary=f"Reinforced is_a link under parent from reflective evidence.",
                    applied=True,
                    created=time(),
                    metadata={
                        "hierarchy_edge_id": edge.id,
                        "parent_id": pid,
                        "child_id": kid,
                    },
                )
                self.store.adaptations[ad.id] = ad
                self._applied += 1
                created.append(ad)
                self.validation.record_learning(
                    action="hierarchy_reinforce",
                    adaptation_id=ad.id,
                    target_id=kid,
                    parent_id=pid,
                    generalize=1,
                    apply=1,
                    sleep_batch_id=sleep_batch_id,
                )
            # Soft attribute inheritance for specialized children (evidence-gated).
            for kid in kids[:2]:
                inherited = self.concepts.inherit_attributes(
                    kid, pid, evidence_ids=tuple(evidence_ids[-3:])
                )
                if inherited:
                    ad = Adaptation(
                        id=new_id("adp"),
                        kind=AdaptationKind.GENERALIZE,
                        target_kind=AdaptationTarget.CONCEPT,
                        target_id=kid,
                        governance=GovernanceClass.AUTOMATIC,
                        before={"inherited_attrs": 0},
                        after={"inherited_attrs": float(len(inherited))},
                        reflective_experience_ids=list(reflective_ids),
                        evidence_experience_ids=list(evidence_ids),
                        sleep_batch_id=sleep_batch_id,
                        summary="Inherited parent attributes onto specialized child (evidence-gated).",
                        applied=True,
                        created=time(),
                        metadata={"inherited": inherited, "parent_id": pid},
                    )
                    self.store.adaptations[ad.id] = ad
                    self._applied += 1
                    created.append(ad)
        # Orphans that share a common parent already used by siblings — specialize under it.
        if orphans and by_parent:
            dominant_parent = max(by_parent, key=lambda p: len(by_parent[p]))
            for kid in orphans[:2]:
                edge = self.concepts.specialize(
                    kid,
                    dominant_parent,
                    evidence_ids=tuple(evidence_ids[-4:]),
                )
                if edge is None:
                    continue
                ad = Adaptation(
                    id=new_id("adp"),
                    kind=AdaptationKind.GENERALIZE,
                    target_kind=AdaptationTarget.CONCEPT,
                    target_id=kid,
                    governance=GovernanceClass.AUTOMATIC,
                    before={"hierarchy_weight": 0.0},
                    after={"hierarchy_weight": edge.weight},
                    reflective_experience_ids=list(reflective_ids),
                    evidence_experience_ids=list(evidence_ids),
                    sleep_batch_id=sleep_batch_id,
                    summary="Specialized orphan concept under evidenced shared parent.",
                    applied=True,
                    created=time(),
                    metadata={
                        "hierarchy_edge_id": edge.id,
                        "parent_id": dominant_parent,
                        "child_id": kid,
                    },
                )
                self.store.adaptations[ad.id] = ad
                self._applied += 1
                created.append(ad)
        return created

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
        lim = self.stability_limits
        before = {"strength": concept.strength, "confidence": concept.confidence}
        concept.strength = max(0.0, min(1.0, concept.strength + strength_delta))
        concept.confidence = max(
            lim.min_confidence,
            min(lim.max_confidence, concept.confidence + confidence_delta),
        )
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
        lim = self.stability_limits
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
            attr.confidence = max(
                lim.min_confidence, min(lim.max_confidence, attr.confidence + delta)
            )
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
        lim = self.stability_limits
        before = {"confidence": concept.confidence}
        concept.confidence = max(
            lim.min_confidence, min(lim.max_confidence, concept.confidence + delta)
        )
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
        elif ad.target_kind == AdaptationTarget.GOAL:
            goal = self.store.goals.get(ad.target_id)
            if goal is None:
                return None
            cur = {"importance": float(goal.importance)}
            goal.importance = before.get("importance", goal.importance)
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
