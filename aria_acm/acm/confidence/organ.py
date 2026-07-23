"""Uncertainty & Confidence organ — M16."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.confidence.model import (
    ConfidenceEvent,
    ConfidenceSnapshot,
    EvidenceInfluence,
    EvidenceStatus,
    UncertaintyKind,
)
from acm.experiences.kinds import CognitiveKind
from acm.reconciliation.model import ReconciliationStatus
from acm.validation.harness import ConfidenceDelta

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.reconciliation.model import ReconciliationRecord
    from acm.validation.harness import ValidationHarness


class ConfidenceOrgan:
    """Answers: How certain am I that this memory is accurate?"""

    # Evidence influence policy (M5 Cap2) — seconds; tests may override via method args.
    DEFAULT_HALF_LIFE_S = 30 * 86400.0
    DEFAULT_STALE_IDLE_S = 14 * 86400.0
    WEIGHT_FLOOR = 0.05
    OBSOLETE_WEIGHT = 0.08

    def __init__(self, store: CognitiveStore, validation: ValidationHarness) -> None:
        self.store = store
        self.validation = validation
        self._events = 0
        self._recalibrations = 0
        self._aged = 0
        self._stale_marks = 0
        self._obsolete_marks = 0
        self._reinforcements = 0

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
        now = time()
        weights = [
            self.evidence_weight("concept", concept_id, eid, now=now)
            for eid in concept.evidence_ids
        ]
        mass = (sum(weights) / len(weights)) if weights else 0.0
        factors: dict[str, float] = {
            "stored": concept.confidence,
            "strength": concept.strength * 0.15,
            "evidence": min(0.2, len(concept.evidence_ids) * 0.04) * max(mass, 0.15),
            "evidence_mass": mass * 0.18,
        }
        kinds: list[str] = []
        if len(concept.evidence_ids) < 2:
            kinds.append(UncertaintyKind.EVIDENCE.value)
            factors["sparse_evidence"] = -0.08
        if concept.provisional:
            kinds.append(UncertaintyKind.LEARNING.value)
            factors["provisional"] = -0.05
        stale_n = obsolete_n = 0
        for eid in concept.evidence_ids:
            inf = self.store.evidence_influences.get(f"concept:{concept_id}:{eid}")
            if inf is None:
                continue
            if inf.status == EvidenceStatus.STALE:
                stale_n += 1
            elif inf.status == EvidenceStatus.OBSOLETE:
                obsolete_n += 1
        if stale_n:
            kinds.append(UncertaintyKind.STALE.value)
            factors["stale_evidence"] = -0.06 * min(3, stale_n)
        if obsolete_n:
            kinds.append(UncertaintyKind.OBSOLETE.value)
            factors["obsolete_evidence"] = -0.04 * min(3, obsolete_n)
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

    def evidence_weight(
        self,
        target_kind: str,
        target_id: str,
        experience_id: str,
        *,
        now: float | None = None,
    ) -> float:
        """Current influence weight for one evidence Experience on a living target."""
        inf = self._ensure_influence(target_kind, target_id, experience_id, now=now)
        return float(inf.weight)

    def mark_reinforced(
        self,
        target_kind: str,
        target_id: str,
        evidence_ids: list[str] | tuple[str, ...],
        *,
        at: float | None = None,
        boost: float = 0.15,
    ) -> int:
        """Refresh evidence influence after reinforcement. Never invents Experiences."""
        now = at if at is not None else time()
        n = 0
        for eid in evidence_ids:
            if not eid:
                continue
            inf = self._ensure_influence(target_kind, target_id, eid, now=now)
            inf.weight = min(1.0, max(inf.weight, 0.35) + boost)
            inf.last_reinforced = now
            inf.status = EvidenceStatus.ACTIVE
            self.store.evidence_influences[inf.key] = inf
            n += 1
            self._reinforcements += 1
        return n

    def detect_stale(
        self,
        target_kind: str,
        target_id: str,
        *,
        now: float | None = None,
        stale_idle_s: float | None = None,
    ) -> list[EvidenceInfluence]:
        now = now if now is not None else time()
        idle = stale_idle_s if stale_idle_s is not None else self.DEFAULT_STALE_IDLE_S
        out: list[EvidenceInfluence] = []
        prefix = f"{target_kind}:{target_id}:"
        for key, inf in self.store.evidence_influences.items():
            if not key.startswith(prefix):
                continue
            last = inf.last_reinforced or inf.created or now
            if (now - last) >= idle and inf.status != EvidenceStatus.OBSOLETE:
                out.append(inf)
        return out

    def detect_obsolete(
        self,
        target_kind: str,
        target_id: str,
    ) -> list[EvidenceInfluence]:
        out: list[EvidenceInfluence] = []
        prefix = f"{target_kind}:{target_id}:"
        for key, inf in self.store.evidence_influences.items():
            if not key.startswith(prefix):
                continue
            if inf.status == EvidenceStatus.OBSOLETE or inf.weight <= self.OBSOLETE_WEIGHT:
                out.append(inf)
        return out

    def age_evidence_pass(
        self,
        *,
        now: float | None = None,
        half_life_s: float | None = None,
        stale_idle_s: float | None = None,
        max_concepts: int = 200,
    ) -> dict[str, Any]:
        """Offline evidence aging — lowers influence; never deletes provenance or Experiences.

        Host-callable via sleep/consolidate. Deterministic given `now`.
        """
        now = now if now is not None else time()
        half = half_life_s if half_life_s is not None else self.DEFAULT_HALF_LIFE_S
        idle = stale_idle_s if stale_idle_s is not None else self.DEFAULT_STALE_IDLE_S
        aged = stale = obsolete = conf_adjusted = 0
        exp_before = len(self.store.experiences)
        prov_before = len(self.store.provenance)

        concepts = [c for c in self.store.concepts.values() if c.active][:max_concepts]
        for concept in concepts:
            # Ensure influences exist for all evidence_ids
            for eid in concept.evidence_ids:
                self._ensure_influence("concept", concept.id, eid, now=now)
            weights_before: list[float] = []
            weights_after: list[float] = []
            for eid in concept.evidence_ids:
                key = f"concept:{concept.id}:{eid}"
                inf = self.store.evidence_influences.get(key)
                if inf is None:
                    continue
                weights_before.append(inf.weight)
                last = inf.last_reinforced or inf.created or now
                age = max(0.0, now - last)
                # Exponential decay of influence unless recently reinforced
                decay = 0.5 ** (age / max(half, 1.0))
                new_w = max(self.WEIGHT_FLOOR, inf.weight * 0.92 + decay * 0.08)
                if abs(new_w - inf.weight) > 1e-6:
                    aged += 1
                    self._aged += 1
                inf.weight = new_w
                if age >= idle and inf.status != EvidenceStatus.OBSOLETE:
                    if inf.status != EvidenceStatus.STALE:
                        stale += 1
                        self._stale_marks += 1
                    inf.status = EvidenceStatus.STALE
                # Obsolete: very low influence after long neglect (keep evidence_ids)
                if inf.weight <= self.OBSOLETE_WEIGHT and age >= idle * 1.5:
                    if inf.status != EvidenceStatus.OBSOLETE:
                        obsolete += 1
                        self._obsolete_marks += 1
                    inf.status = EvidenceStatus.OBSOLETE
                self.store.evidence_influences[key] = inf
                weights_after.append(inf.weight)

            if weights_before and weights_after:
                mb = sum(weights_before) / len(weights_before)
                ma = sum(weights_after) / len(weights_after)
                if ma + 1e-9 < mb:
                    before = concept.confidence
                    # Gentle living confidence drift toward aged mass (stabilize band).
                    concept.confidence = max(
                        0.08,
                        min(0.98, concept.confidence * 0.92 + (0.35 + ma * 0.4) * 0.08),
                    )
                    if abs(concept.confidence - before) > 1e-6:
                        conf_adjusted += 1
                        self._record_event(
                            "concept",
                            concept.id,
                            before,
                            concept.confidence,
                            "evidence_aging",
                            ["age", "decay"],
                        )

        assert len(self.store.experiences) == exp_before
        assert len(self.store.provenance) == prov_before
        self.validation.record_confidence_organ(
            action="age_evidence_pass",
            aged=aged,
            stale=stale,
            obsolete=obsolete,
            confidence_adjusted=conf_adjusted,
            age=1,
        )
        return {
            "aged": aged,
            "stale": stale,
            "obsolete": obsolete,
            "confidence_adjusted": conf_adjusted,
            "experiences_unchanged": True,
            "provenance_unchanged": True,
        }

    def stabilize_confidence(self, concept_id: str, *, now: float | None = None) -> float | None:
        """Pull living confidence toward weighted evidence mass (non-destructive)."""
        concept = self.store.concepts.get(concept_id)
        if concept is None or not concept.active:
            return None
        snap = self.estimate_concept(concept_id)
        mass = float(snap.factors.get("evidence_mass", 0.0)) / 0.18 if snap.factors.get("evidence_mass") else 0.0
        target = min(0.85, max(0.25, 0.4 + mass * 0.4))
        before = concept.confidence
        concept.confidence = concept.confidence * 0.85 + target * 0.15
        if abs(concept.confidence - before) > 1e-6:
            self._record_event(
                "concept",
                concept_id,
                before,
                concept.confidence,
                "stabilize",
                ["stabilize", "evidence_mass"],
            )
        return concept.confidence

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
            self.mark_reinforced("concept", concept_id, concept.evidence_ids[-3:])
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
        if reinforce:
            self.mark_reinforced("concept", concept_id, concept.evidence_ids[-4:])
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
            "aged": self._aged,
            "stale_marks": self._stale_marks,
            "obsolete_marks": self._obsolete_marks,
            "reinforcements": self._reinforcements,
            "influence_records": len(self.store.evidence_influences),
        }

    def _ensure_influence(
        self,
        target_kind: str,
        target_id: str,
        experience_id: str,
        *,
        now: float | None = None,
    ) -> EvidenceInfluence:
        from acm.authority.mode import is_read_only

        now = now if now is not None else time()
        key = f"{target_kind}:{target_id}:{experience_id}"
        existing = self.store.evidence_influences.get(key)
        if existing is not None:
            return existing
        exp = self.store.experiences.get(experience_id)
        created = float(getattr(exp, "t_start", None) or now)
        inf = EvidenceInfluence(
            target_kind=target_kind,
            target_id=target_id,
            experience_id=experience_id,
            weight=1.0,
            last_reinforced=created,
            created=created,
            status=EvidenceStatus.ACTIVE,
        )
        # Inspect / READ_ONLY must not invent store records (zero-write façades).
        if not is_read_only():
            self.store.evidence_influences[key] = inf
        return inf

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
