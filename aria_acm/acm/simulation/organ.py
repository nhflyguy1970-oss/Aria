"""Mental Simulation organ — M12: What possible futures can memory imagine?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.simulation.model import HypotheticalStep, Simulation
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.prediction.organ import PredictionOrgan
    from acm.validation.harness import ValidationHarness


class SimulationOrgan:
    """Hypothetical memory recombination. Never creates historical Experiences."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        prediction: PredictionOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.attention = attention
        self.prediction = prediction
        self._simulations = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        prediction: PredictionOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if attention is not None:
            self.attention = attention
        if prediction is not None:
            self.prediction = prediction

    def what_futures_can_memory_imagine(
        self,
        cue: str,
        *,
        branches: int = 3,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.5,
    ) -> dict[str, Any]:
        """Cognitive question M12."""
        sims = self.simulate(
            cue,
            branches=branches,
            context_tags=context_tags,
            attention_weight=attention_weight,
        )
        if not sims:
            answer = "Memory cannot yet imagine alternative futures from this cue."
        else:
            bits = []
            for s in sims[:3]:
                path = " → ".join(st.label for st in s.steps[:4])
                bits.append(f"[hypothetical] {path}")
            answer = "Possible imagined futures: " + " | ".join(bits)
        return {
            "question": "What possible futures can memory imagine?",
            "answer": answer,
            "simulations": [s.to_public() for s in sims],
            "hypothetical": True,
            "historical_experiences_created": 0,
            "plans": False,
            "decides": False,
        }

    def simulate(
        self,
        cue: str,
        *,
        branches: int = 3,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.5,
        max_steps: int = 4,
    ) -> list[Simulation]:
        if self.activation is None:
            raise RuntimeError("Simulation requires ActivationEngine")
        before_exp = len(self.store.experiences)
        field = self.activation.activate(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        ranked = field.ranked_concepts(limit=10)
        seed_ids = [n.target_id for n in ranked]

        # Optional: prediction supplies likely anchors, simulation fans out alternatives
        pred_id = ""
        pred_order: list[str] = []
        if self.prediction is not None:
            pred = self.prediction.predict(
                cue, context_tags=context_tags, attention_weight=attention_weight
            )
            pred_id = pred.id
            pred_order = [o.concept_id for o in pred.outcomes]

        # Candidate pool: activated + neighbors (recombination, not invention)
        pool: list[str] = list(seed_ids)
        for cid in seed_ids[:5]:
            for _edge, neighbor in self.store.neighbors(cid):
                if neighbor.id not in pool and neighbor.labels:
                    pool.append(neighbor.id)
        # Deduplicate preserve order
        seen: set[str] = set()
        ordered: list[str] = []
        for cid in pred_order + pool:
            if cid not in seen and cid in self.store.concepts:
                seen.add(cid)
                ordered.append(cid)

        sims: list[Simulation] = []
        n_branches = max(1, min(5, branches))
        for b in range(n_branches):
            steps: list[HypotheticalStep] = []
            # Rotate / skip to form divergent hypothetical paths
            path_ids = ordered[b:] + ordered[:b]
            path_ids = path_ids[:max_steps]
            if not path_ids and seed_ids:
                path_ids = seed_ids[:max_steps]
            for i, cid in enumerate(path_ids):
                concept = self.store.concepts.get(cid)
                if concept is None:
                    continue
                evid = list(concept.evidence_ids[-3:])
                label = concept.labels[0] if concept.labels else cid
                summary = (
                    f"Hypothetical step: if memory continues via '{label}' "
                    f"(recombined from prior structure; not an Experience)."
                )
                steps.append(
                    HypotheticalStep(
                        index=i,
                        concept_id=cid,
                        label=label,
                        summary=summary,
                        source_experience_ids=evid,
                        hypothetical=True,
                    )
                )
            conf = 0.35
            if steps:
                conf = min(
                    0.8,
                    0.3
                    + 0.1 * len(steps)
                    + (0.15 if pred_id else 0.0)
                    + (0.05 * len(seed_ids)),
                )
                if self.attention is not None:
                    conf = min(
                        0.85,
                        conf
                        + 0.1 * self.attention.priority_of(steps[0].concept_id),
                    )
            sim = Simulation(
                id=new_id("sim"),
                cue=cue[:160],
                branch=b,
                steps=steps,
                confidence=conf,
                created=time(),
                source_concept_ids=list(seed_ids[:6]),
                prediction_id=pred_id,
                hypothetical=True,
                metadata={"counterfactual": b > 0},
            )
            self.store.simulations[sim.id] = sim
            sims.append(sim)
            self._simulations += 1
            self.validation.record_simulation(
                action="simulate",
                simulation_id=sim.id,
                branch=b,
                steps=len(steps),
                confidence=conf,
                simulate=1,
                hypothetical=1,
                prediction_id=pred_id or "",
            )

        if len(self.store.experiences) != before_exp:
            raise RuntimeError("Simulation must never birth historical Experiences")
        return sims

    def observables(self) -> dict[str, Any]:
        return {
            "simulations": self._simulations,
            "stored": len(self.store.simulations),
            "hypothetical_steps": sum(
                len(s.steps) for s in self.store.simulations.values()
            ),
        }
