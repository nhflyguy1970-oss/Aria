"""Memory Reconciliation organ — M15."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.associations.model import RelationKind
from acm.experiences.kinds import CognitiveKind
from acm.reconciliation.model import ReconciliationRecord, ReconciliationStatus
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.confidence.organ import ConfidenceOrgan
    from acm.core.store import CognitiveStore
    from acm.validation.harness import ValidationHarness


class ReconciliationOrgan:
    """Answers: When memories disagree, how should memory reconcile them?"""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        activation: ActivationEngine | None = None,
        confidence: ConfidenceOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.confidence = confidence
        self._reconciliations = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        confidence: ConfidenceOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if confidence is not None:
            self.confidence = confidence

    def how_should_memory_reconcile(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
    ) -> dict[str, Any]:
        """Cognitive question M15."""
        record = self.reconcile(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        return {
            "question": "When memories disagree, how should memory reconcile them?",
            "answer": record.summary,
            "reconciliation": record.to_public(),
            "historical_rewrite": False,
            "deleted": False,
            "plans": False,
        }

    def reconcile(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
    ) -> ReconciliationRecord:
        before_exp = len(self.store.experiences)
        subjects: list[str] = []
        supporting: list[str] = []
        conflicting: list[str] = []
        evidence: list[str] = []
        factors: list[str] = []
        conf_vals: list[float] = []

        if self.activation is not None:
            field = self.activation.activate(
                cue, context_tags=context_tags, attention_weight=attention_weight
            )
            for node in field.ranked_concepts(limit=8):
                subjects.append(node.target_id)
                concept = self.store.concepts.get(node.target_id)
                if concept is None:
                    continue
                conf_vals.append(concept.confidence)
                evidence.extend(concept.evidence_ids[-4:])
                # Attribute-level contest: low-confidence active attrs
                low = [a for a in concept.attributes if a.active and a.confidence < 0.45]
                high = [a for a in concept.attributes if a.active and a.confidence >= 0.65]
                if low and high:
                    conflicting.append(concept.id)
                    factors.append("attribute_contest")
                elif len(concept.evidence_ids) >= 2:
                    supporting.append(concept.id)
                    factors.append("multi_evidence")

        # Cue-label supplements — conflict/corroboration must not miss near matches
        for concept in self.store.find_concepts_by_label(cue)[:8]:
            if concept.id not in subjects:
                subjects.append(concept.id)
                conf_vals.append(concept.confidence)

        # Association conflicts (include cue-matched endpoints even if activation missed)
        for edge in self.store.associations.values():
            if not edge.active:
                continue
            if edge.relation != RelationKind.CONFLICTS_WITH:
                continue
            if edge.source_id in subjects or edge.target_id in subjects:
                conflicting.extend([edge.source_id, edge.target_id, edge.id])
                subjects.extend([edge.source_id, edge.target_id])
                factors.append("conflicts_with")
                # Conflict presence supersedes multi-evidence support on those nodes
                supporting = [s for s in supporting if s not in (edge.source_id, edge.target_id)]


        # Reflective contradiction / consistency
        for exp in self.store.experiences.values():
            if exp.cognitive_kind != CognitiveKind.REFLECTION:
                continue
            meta = exp.meta_dict()
            outcomes = meta.get("reflection_outcomes", "")
            if cue.lower()[:4] and cue.lower()[:4] not in (exp.summary or "").lower():
                # soft filter by cue token overlap
                if not any(
                    t in (exp.summary or "").lower()
                    for t in cue.lower().split()
                    if len(t) > 3
                ):
                    continue
            evidence.append(exp.id)
            if "contradiction" in outcomes:
                conflicting.append(exp.id)
                factors.append("reflective_contradiction")
            if "consistency" in outcomes or "sufficient" in outcomes:
                supporting.append(exp.id)
                factors.append("reflective_consistency")

        # Prediction dispersion among recent predictions for cue
        for pred in list(self.store.predictions.values())[-5:]:
            if not any(t in pred.cue.lower() for t in cue.lower().split() if len(t) > 3):
                continue
            if len(pred.outcomes) >= 2 and pred.outcomes[0].probability < 0.55:
                conflicting.append(pred.id)
                factors.append("prediction_dispersion")
            elif pred.outcomes:
                supporting.append(pred.id)
                factors.append("prediction_focus")

        supporting = list(dict.fromkeys(supporting))
        conflicting = list(dict.fromkeys(conflicting))
        evidence = list(dict.fromkeys(evidence))
        subjects = list(dict.fromkeys(subjects))
        factors = list(dict.fromkeys(factors))

        conf_before = sum(conf_vals) / len(conf_vals) if conf_vals else 0.5
        status, summary, conf_after = self._classify(
            supporting, conflicting, factors, conf_before, context_tags
        )

        # Context-dependent: different tags on competing subjects
        if status == ReconciliationStatus.COMPETING and context_tags:
            tag_sets = []
            for sid in subjects[:4]:
                c = self.store.concepts.get(sid)
                if c:
                    # use attribute context tags if any
                    ctx = set()
                    for a in c.attributes:
                        ctx.update(a.context_tags)
                    if ctx:
                        tag_sets.append(ctx)
            if len(tag_sets) >= 2 and not set.intersection(*tag_sets):
                status = ReconciliationStatus.CONTEXT_DEPENDENT
                summary = (
                    "Memories remain valid in different contexts; coexistence preserved."
                )
                factors.append("context_partition")

        record = ReconciliationRecord(
            id=new_id("rcl"),
            cue=cue[:160],
            status=status,
            subject_ids=subjects[:12],
            evidence_ids=evidence[:16],
            conflicting_ids=conflicting[:12],
            supporting_ids=supporting[:12],
            confidence_before=conf_before,
            confidence_after=conf_after,
            summary=summary,
            created=time(),
            context_tags=context_tags,
            factors=factors,
        )
        self.store.reconciliations[record.id] = record
        self._reconciliations += 1

        if self.confidence is not None:
            self.confidence.apply_reconciliation(record)

        self.validation.record_reconciliation(
            action="reconcile",
            reconciliation_id=record.id,
            status=status.value,
            conflict=1 if conflicting else 0,
            corroboration=1 if supporting and not conflicting else 0,
            confidence_before=conf_before,
            confidence_after=conf_after,
            reconcile=1,
        )
        if len(self.store.experiences) != before_exp:
            raise RuntimeError("Reconciliation must never rewrite Experience chronology")
        return record

    def observables(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for r in self.store.reconciliations.values():
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {
            "reconciliations": self._reconciliations,
            "stored": len(self.store.reconciliations),
            "by_status": by_status,
        }

    def _classify(
        self,
        supporting: list[str],
        conflicting: list[str],
        factors: list[str],
        conf_before: float,
        context_tags: tuple[str, ...],
    ) -> tuple[ReconciliationStatus, str, float]:
        if supporting and not conflicting:
            return (
                ReconciliationStatus.REINFORCE,
                "Memories corroborate; confidence strengthened without rewriting history.",
                min(0.95, conf_before + 0.08),
            )
        if conflicting and supporting:
            if context_tags:
                return (
                    ReconciliationStatus.CONTEXT_DEPENDENT,
                    "Supporting and conflicting traces coexist; context may select retrieval.",
                    max(0.2, conf_before - 0.05),
                )
            return (
                ReconciliationStatus.COMPETING,
                "Competing memories preserved with lineage; no silent discard.",
                max(0.15, conf_before - 0.12),
            )
        if conflicting and not supporting:
            return (
                ReconciliationStatus.UNRESOLVED,
                "Conflict detected without corroboration; uncertainty retained.",
                max(0.1, conf_before - 0.15),
            )
        if "reflective_contradiction" in factors:
            return (
                ReconciliationStatus.REVISED,
                "Reflective contradiction recorded as reconciliation artifact; Experiences intact.",
                max(0.2, conf_before - 0.1),
            )
        return (
            ReconciliationStatus.UNRESOLVED,
            "Insufficient conflict or corroboration signal to force a resolution.",
            conf_before,
        )
