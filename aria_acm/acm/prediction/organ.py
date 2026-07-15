"""Prediction organ — M11: Based upon memory, what is likely?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.associations.model import RelationKind
from acm.prediction.model import PredictedOutcome, Prediction
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.validation.harness import ValidationHarness


class PredictionOrgan:
    """Estimates probable future memory outcomes. Never plans or decides."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.attention = attention
        self.forgetting = forgetting
        self._predictions = 0
        self._evaluations = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting

    def what_is_likely(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
    ) -> dict[str, Any]:
        """Cognitive question M11."""
        prediction = self.predict(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        top = prediction.outcomes[:3]
        if not top:
            answer = "Memory does not yet support a clear likely outcome."
        else:
            bits = [
                f"{o.label} (~{o.probability:.0%})" for o in top if o.probability > 0.05
            ]
            answer = "Likely from memory: " + "; ".join(bits)
        public = prediction.to_public()
        public["answer"] = answer
        return public

    def predict(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
    ) -> Prediction:
        if self.activation is None:
            raise RuntimeError("Prediction requires ActivationEngine")
        field = self.activation.activate(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        seeds = {s.target_id for s in field.seeds}
        ranked = field.ranked_concepts(limit=8)
        scores: dict[str, float] = {}
        support: dict[str, list[str]] = {}
        why: dict[str, list[str]] = {}

        for node in ranked:
            cid = node.target_id
            base = max(0.05, node.energy)
            if self.attention is not None:
                base *= 0.7 + 0.3 * self.attention.priority_of(cid)
            if self.forgetting is not None:
                base *= 0.5 + 0.5 * self.forgetting.factor(cid)
            scores[cid] = scores.get(cid, 0.0) + base
            why.setdefault(cid, []).append("activation")

        # Association-based anticipation (forward relation / predicts / precedes)
        for cid in list(seeds)[:12]:
            for edge, neighbor in self.store.neighbors(cid):
                if not neighbor.active and neighbor.stage.value == "retired":
                    continue
                rel = edge.relation
                weight = edge.strength_forward
                bonus = 0.0
                tag = "association"
                if rel == RelationKind.PREDICTS:
                    bonus = 0.45 * weight
                    tag = "predicts"
                elif rel in (RelationKind.PRECEDES, RelationKind.FOLLOWS):
                    bonus = 0.3 * weight
                    tag = "temporal"
                elif rel in (RelationKind.CO_ACTIVATED, RelationKind.BELONGS_WITH):
                    bonus = 0.22 * weight
                    tag = "coactivation"
                elif rel == RelationKind.SUPPORTS:
                    bonus = 0.18 * weight
                    tag = "supports"
                else:
                    bonus = 0.1 * weight
                if bonus <= 0:
                    continue
                if self.attention is not None:
                    bonus *= 0.75 + 0.25 * self.attention.priority_of(neighbor.id)
                if self.forgetting is not None:
                    bonus *= max(0.15, self.forgetting.factor(neighbor.id))
                scores[neighbor.id] = scores.get(neighbor.id, 0.0) + bonus
                support.setdefault(neighbor.id, []).append(edge.id)
                why.setdefault(neighbor.id, []).append(tag)

        # Softmax-like normalize to probabilistic distribution
        total = sum(max(0.0, v) for v in scores.values()) or 1.0
        outcomes: list[PredictedOutcome] = []
        for cid, raw in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8]:
            concept = self.store.concepts.get(cid)
            if concept is None:
                continue
            prob = max(0.0, raw) / total
            # temperature soften — never deterministic certainty
            prob = min(0.85, prob)
            outcomes.append(
                PredictedOutcome(
                    concept_id=cid,
                    label=concept.labels[0] if concept.labels else cid,
                    probability=prob,
                    support=list(dict.fromkeys(support.get(cid, [])))[:6],
                    why=list(dict.fromkeys(why.get(cid, [])))[:6],
                )
            )
        # Renormalize after cap
        s = sum(o.probability for o in outcomes) or 1.0
        for o in outcomes:
            o.probability = o.probability / s

        confidence = 0.0
        if outcomes:
            confidence = min(0.9, outcomes[0].probability * 0.6 + (len(outcomes) / 8) * 0.2)
            # Learning residue: more adaptations → slightly higher confidence
            ad_n = len(self.store.adaptations)
            confidence = min(0.92, confidence + min(0.12, ad_n * 0.01))
            # Sleep batches / offline improve predictive structure
            access_boost = min(0.08, len(self.store.accessibility_events) * 0.002)
            confidence = min(0.95, confidence + access_boost)

        pred = Prediction(
            id=new_id("prd"),
            cue=cue[:160],
            outcomes=outcomes,
            confidence=confidence,
            created=time(),
            source_concept_ids=[n.target_id for n in ranked[:6]],
        )
        self.store.predictions[pred.id] = pred
        self._predictions += 1
        self.validation.record_prediction(
            action="predict",
            prediction_id=pred.id,
            cue=cue[:80],
            outcome_count=len(outcomes),
            confidence=confidence,
            predict=1,
            top_probability=outcomes[0].probability if outcomes else 0.0,
        )
        return pred

    def evaluate(self, prediction_id: str, realized_concept_id: str) -> dict[str, Any]:
        """Update prediction accuracy from a later memory outcome (not a plan reward)."""
        pred = self.store.predictions.get(prediction_id)
        if pred is None:
            return {"status": "missing"}
        ranked = [o.concept_id for o in pred.outcomes]
        if realized_concept_id in ranked:
            idx = ranked.index(realized_concept_id)
            # higher if closer to top
            accuracy = max(0.1, 1.0 - idx * 0.12)
        else:
            accuracy = 0.05
        pred.evaluated = True
        pred.accuracy = accuracy
        # Confidence evolution toward observed accuracy
        before = pred.confidence
        pred.confidence = pred.confidence * 0.7 + accuracy * 0.3
        self._evaluations += 1
        self.validation.record_prediction(
            action="evaluate",
            prediction_id=pred.id,
            accuracy=accuracy,
            confidence_before=before,
            confidence_after=pred.confidence,
            evaluate=1,
            realized_concept_id=realized_concept_id,
        )
        return {
            "status": "evaluated",
            "accuracy": accuracy,
            "confidence": pred.confidence,
            "prediction": pred.to_public(),
        }

    def observables(self) -> dict[str, Any]:
        evaluated = [p for p in self.store.predictions.values() if p.evaluated]
        avg_acc = (
            sum(p.accuracy or 0 for p in evaluated) / len(evaluated) if evaluated else 0.0
        )
        return {
            "predictions": self._predictions,
            "evaluations": self._evaluations,
            "stored": len(self.store.predictions),
            "avg_accuracy": avg_acc,
        }
