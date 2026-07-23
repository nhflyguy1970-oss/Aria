"""Uncertainty & Confidence organ — M16."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.confidence.model import ConfidenceEvent, ConfidenceSnapshot, UncertaintyKind
from acm.experiences.kinds import CognitiveKind
from acm.reconciliation.model import ReconciliationStatus
from acm.validation.harness import ConfidenceDelta

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.reconciliation.model import ReconciliationRecord
    from acm.validation.harness import ValidationHarness


class ConfidenceOrgan:
    """Answers: How certain am I that this memory is accurate?"""

    def __init__(self, store: CognitiveStore, validation: ValidationHarness) -> None:
        self.store = store
        self.validation = validation
        self._events = 0
        self._recalibrations = 0

    def how_certain_am_i(
        self,
        cue: str = "",
        *,
        concept_id: str = "",
    ) -> dict[str, Any]:
        """Cognitive question M16."""
        snaps: list[ConfidenceSnapshot] = []
        if concept_id and concept_id in self.store.concepts:
            snaps.append(self.estimate_concept(concept_id))
        else:
            matches = self.store.find_concepts_by_label(cue) if cue else []
            for c in matches[:6]:
                snaps.append(self.estimate_concept(c.id))
            if not snaps:
                # Top active concepts sample
                for c in list(self.store.concepts.values())[:8]:
                    if c.active and not c.identity:
                        snaps.append(self.estimate_concept(c.id))
                        if len(snaps) >= 5:
                            break
        if not snaps:
            answer = "No living memory target available for confidence estimation."
            overall = 0.0
        else:
            overall = sum(s.value for s in snaps) / len(snaps)
            bits = [
                f"{self._label(s.target_id)}={s.value:.2f}" for s in snaps[:4]
            ]
            # B05: include factor narrative from the strongest snapshot.
            top = max(snaps, key=lambda s: s.value)
            factor_bits = []
            for k, v in list((top.factors or {}).items())[:5]:
                if k == "stored":
                    continue
                sign = "+" if v >= 0 else ""
                factor_bits.append(f"{k}:{sign}{v:.2f}")
            explain = (top.explain or "").strip()
            answer = f"Memory confidence (~{overall:.0%}): " + "; ".join(bits)
            if factor_bits:
                answer += ". Factors: " + ", ".join(factor_bits)
            if explain:
                answer += f". {explain}"
        return {
            "question": "How certain am I that this memory is accurate?",
            "answer": answer,
            "overall_confidence": round(overall, 4),
            "snapshots": [s.to_public() for s in snaps],
            "uncertainty": self.global_uncertainty(),
            "plans": False,
            "decides": False,
        }

    def estimate_concept(self, concept_id: str) -> ConfidenceSnapshot:
        concept = self.store.concepts[concept_id]
        factors: dict[str, float] = {
            "stored": concept.confidence,
            "strength": concept.strength * 0.15,
            "evidence": min(0.2, len(concept.evidence_ids) * 0.04),
        }
        kinds: list[str] = []
        if len(concept.evidence_ids) < 2:
            kinds.append(UncertaintyKind.EVIDENCE.value)
            factors["sparse_evidence"] = -0.08
        if concept.provisional:
            kinds.append(UncertaintyKind.LEARNING.value)
            factors["provisional"] = -0.05
        # Reflection outcomes on evidence
        for eid in concept.evidence_ids[-5:]:
            exp = self.store.experiences.get(eid)
            if exp is None:
                continue
            if exp.cognitive_kind == CognitiveKind.REFLECTION:
                outcomes = exp.meta_dict().get("reflection_outcomes", "")
                if "contradiction" in outcomes or "uncertainty" in outcomes:
                    kinds.append(UncertaintyKind.REFLECTION.value)
                    factors["reflective_uncertainty"] = -0.1
                if "consistency" in outcomes or "sufficient" in outcomes:
                    factors["reflective_support"] = 0.06
        # Accessibility / priority soft effects
        access = self.store.accessibility.get(concept_id, "accessible")
        if access in ("dormant", "rarely_activated", "archived"):
            factors["low_accessibility"] = -0.06
            kinds.append(UncertaintyKind.KNOWN_UNKNOWN.value)
        factors["priority"] = (concept.importance - 0.5) * 0.08

        value = concept.confidence
        for k, v in factors.items():
            if k == "stored":
                continue
            value += v
        value = max(0.05, min(0.98, value))
        explain = (
            f"Confidence from stored={concept.confidence:.2f} adjusted by "
            f"{', '.join(f'{k}:{v:+.2f}' for k, v in factors.items() if k != 'stored')}."
        )
        return ConfidenceSnapshot(
            target_kind="concept",
            target_id=concept_id,
            value=value,
            uncertainty_kinds=list(dict.fromkeys(kinds)),
            factors=factors,
            explain=explain,
        )

    def apply_reconciliation(self, record: ReconciliationRecord) -> None:
        """Recalibrate living confidence from reconciliation without rewriting history."""
        delta = record.confidence_after - record.confidence_before
        # Cap propagation
        step = max(-0.12, min(0.1, delta))
        for sid in record.subject_ids[:8]:
            concept = self.store.concepts.get(sid)
            if concept is None or concept.identity:
                continue
            before = concept.confidence
            if record.status == ReconciliationStatus.REINFORCE:
                concept.confidence = min(0.98, concept.confidence + abs(step) * 0.8 + 0.03)
                factors = ["corroboration", "reconciliation"]
            elif record.status in (
                ReconciliationStatus.COMPETING,
                ReconciliationStatus.UNRESOLVED,
            ):
                concept.confidence = max(0.08, concept.confidence - abs(step) * 0.9)
                factors = ["conflict", "reconciliation"]
            elif record.status == ReconciliationStatus.CONTEXT_DEPENDENT:
                # Mild lowering of global certainty; contexts preserved
                concept.confidence = max(0.15, concept.confidence - 0.03)
                factors = ["context_dependent", "reconciliation"]
            else:
                concept.confidence = max(0.1, min(0.95, concept.confidence + step * 0.5))
                factors = ["reconciliation"]
            after = concept.confidence
            self._record_event("concept", sid, before, after, "reconciliation", factors)
            self._recalibrations += 1

    def evolve_from_encode(self, concept_id: str, *, success: bool = True) -> None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return
        before = concept.confidence
        if success:
            concept.confidence = min(0.98, concept.confidence + 0.02)
            factors = ["experience", "repeated_success"]
        else:
            concept.confidence = max(0.08, concept.confidence - 0.04)
            factors = ["experience", "repeated_failure"]
        self._record_event(
            "concept", concept_id, before, concept.confidence, "encode", factors
        )

    def evolve_from_learning(self, concept_id: str, *, reinforce: bool) -> None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return
        before = concept.confidence
        concept.confidence = (
            min(0.98, concept.confidence + 0.03)
            if reinforce
            else max(0.08, concept.confidence - 0.05)
        )
        self._record_event(
            "concept",
            concept_id,
            before,
            concept.confidence,
            "learning",
            ["learning", "reinforce" if reinforce else "weaken"],
        )

    def global_uncertainty(self) -> dict[str, Any]:
        kinds: dict[str, int] = {}
        low = 0
        for c in self.store.concepts.values():
            if not c.active:
                continue
            snap = self.estimate_concept(c.id)
            for k in snap.uncertainty_kinds:
                kinds[k] = kinds.get(k, 0) + 1
            if snap.value < 0.4:
                low += 1
        # Artifact-level
        for pred in self.store.predictions.values():
            if pred.confidence < 0.45:
                kinds[UncertaintyKind.PREDICTION.value] = (
                    kinds.get(UncertaintyKind.PREDICTION.value, 0) + 1
                )
        for _sim in self.store.simulations.values():
            kinds[UncertaintyKind.SIMULATION.value] = (
                kinds.get(UncertaintyKind.SIMULATION.value, 0) + 1
            )
        return {"kinds": kinds, "low_confidence_concepts": low}

    def observables(self) -> dict[str, Any]:
        return {
            "events": self._events,
            "recalibrations": self._recalibrations,
            "stored_events": len(self.store.confidence_events),
        }

    def _record_event(
        self,
        kind: str,
        target_id: str,
        before: float,
        after: float,
        source: str,
        factors: list[str],
    ) -> None:
        event = ConfidenceEvent(
            timestamp=time(),
            target_kind=kind,
            target_id=target_id,
            before=before,
            after=after,
            source=source,
            factors=factors,
            summary=f"{source}: {before:.3f}→{after:.3f}",
        )
        self.store.confidence_events.append(event)
        self._events += 1
        self.validation.record_confidence(
            ConfidenceDelta(time(), target_id, source, before, after, source)
        )
        self.validation.record_confidence_organ(
            action="evolve",
            target_id=target_id,
            before=before,
            after=after,
            source=source,
            evolve=1,
        )

    def _label(self, concept_id: str) -> str:
        c = self.store.concepts.get(concept_id)
        if c and c.labels:
            return c.labels[0]
        return concept_id
