"""Memory Recombination organ — M13."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.recombination.model import RecombinedFragment, RecombinedMemory
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.prediction.organ import PredictionOrgan
    from acm.simulation.organ import SimulationOrgan
    from acm.validation.harness import ValidationHarness


class RecombinationOrgan:
    """Answers: What new memories can emerge by recombining existing memories?"""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        prediction: PredictionOrgan | None = None,
        simulation: SimulationOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.attention = attention
        self.prediction = prediction
        self.simulation = simulation
        self._recombinations = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        prediction: PredictionOrgan | None = None,
        simulation: SimulationOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if attention is not None:
            self.attention = attention
        if prediction is not None:
            self.prediction = prediction
        if simulation is not None:
            self.simulation = simulation

    def what_new_memories_can_emerge(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.5,
        blends: int = 3,
    ) -> dict[str, Any]:
        """Cognitive question M13."""
        items = self.recombine(
            cue,
            context_tags=context_tags,
            attention_weight=attention_weight,
            blends=blends,
        )
        if not items:
            answer = "No novel recombinations emerge from current memory yet."
        else:
            bits = [r.summary for r in items[:3] if r.summary]
            answer = "Recombined memories: " + " | ".join(bits)
        return {
            "question": "What new memories can emerge by recombining existing memories?",
            "answer": answer,
            "recombinations": [r.to_public() for r in items],
            "historical_experiences_created": 0,
            "plans": False,
            "decides": False,
        }

    def recombine(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.5,
        blends: int = 3,
    ) -> list[RecombinedMemory]:
        if self.activation is None:
            raise RuntimeError("Recombination requires ActivationEngine")
        before = len(self.store.experiences)
        field = self.activation.activate(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        ranked = field.ranked_concepts(limit=10)
        seed_ids = [n.target_id for n in ranked]

        pred_id = ""
        sim_id = ""
        extra: list[str] = []
        if self.prediction is not None:
            pred = self.prediction.predict(
                cue, context_tags=context_tags, attention_weight=attention_weight
            )
            pred_id = pred.id
            extra.extend(o.concept_id for o in pred.outcomes[:4])
        if self.simulation is not None:
            sims = self.simulation.simulate(
                cue,
                branches=1,
                context_tags=context_tags,
                attention_weight=attention_weight,
                max_steps=3,
            )
            if sims:
                sim_id = sims[0].id
                extra.extend(s.concept_id for s in sims[0].steps)

        # Neighbor bridges for cross-domain blend
        bridges: list[str] = []
        for cid in seed_ids[:5]:
            for _edge, neighbor in self.store.neighbors(cid):
                if neighbor.id not in seed_ids and neighbor.labels:
                    bridges.append(neighbor.id)

        pool = list(dict.fromkeys(seed_ids + extra + bridges))
        domains = self._domains(pool)
        out: list[RecombinedMemory] = []
        n = max(1, min(5, blends))
        for i in range(n):
            # Rotate pool to form distinct blends
            rotated = pool[i:] + pool[:i]
            picks = rotated[: min(4, len(rotated))]
            if len(picks) < 2 and len(pool) >= 2:
                picks = pool[:2]
            if len(picks) < 2:
                continue
            fragments: list[RecombinedFragment] = []
            for j, cid in enumerate(picks):
                concept = self.store.concepts.get(cid)
                if concept is None:
                    continue
                role = "seed" if j == 0 else ("bridge" if cid in bridges else "blend")
                fragments.append(
                    RecombinedFragment(
                        concept_id=cid,
                        label=concept.labels[0] if concept.labels else cid,
                        role=role,
                        source_experience_ids=list(concept.evidence_ids[-3:]),
                    )
                )
            if len(fragments) < 2:
                continue
            novelty = self._novelty(fragments, domains)
            conf = min(0.85, 0.35 + 0.1 * len(fragments) + 0.15 * novelty)
            if self.attention is not None:
                conf = min(
                    0.9,
                    conf + 0.08 * self.attention.priority_of(fragments[0].concept_id),
                )
            labels = [f.label for f in fragments]
            summary = (
                f"Recombined: {' + '.join(labels)} "
                f"(novel blend from existing memory; not an Experience)."
            )
            item = RecombinedMemory(
                id=new_id("rcb"),
                cue=cue[:160],
                fragments=fragments,
                novelty=novelty,
                confidence=conf,
                created=time(),
                summary=summary,
                domains=domains,
                simulation_id=sim_id,
                prediction_id=pred_id,
            )
            self.store.recombinations[item.id] = item
            out.append(item)
            self._recombinations += 1
            self.validation.record_recombination(
                action="recombine",
                recombination_id=item.id,
                fragment_count=len(fragments),
                novelty=novelty,
                confidence=conf,
                recombine=1,
                domains=len(domains),
                prediction_id=pred_id or "",
                simulation_id=sim_id or "",
            )
        if len(self.store.experiences) != before:
            raise RuntimeError("Recombination must never birth Experiences")
        return out

    def observables(self) -> dict[str, Any]:
        return {
            "recombinations": self._recombinations,
            "stored": len(self.store.recombinations),
            "avg_novelty": (
                sum(r.novelty for r in self.store.recombinations.values())
                / max(1, len(self.store.recombinations))
            ),
        }

    def _domains(self, concept_ids: list[str]) -> list[str]:
        tags: set[str] = set()
        for cid in concept_ids:
            c = self.store.concepts.get(cid)
            if c is None:
                continue
            tags.add(c.role.value)
            for pid in c.parent_ids[:2]:
                p = self.store.concepts.get(pid)
                if p and p.labels:
                    tags.add(p.labels[0].lower())
        return sorted(tags)[:8]

    def _novelty(
        self, fragments: list[RecombinedFragment], domains: list[str]
    ) -> float:
        # Higher when fragments span roles/domains and lack prior co-activation edge
        roles = {f.role for f in fragments}
        score = 0.2 * len(domains) + 0.15 * len(roles)
        ids = [f.concept_id for f in fragments]
        linked = 0
        pairs = 0
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                pairs += 1
                if any(
                    (e.source_id == a and e.target_id == b)
                    or (e.source_id == b and e.target_id == a)
                    for e in self.store.associations.values()
                    if e.active
                ):
                    linked += 1
        if pairs:
            # Fewer existing links → more novel combination
            score += 0.4 * (1.0 - linked / pairs)
        return max(0.05, min(1.0, score))
