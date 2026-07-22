"""Prediction organ — M11: Based upon memory, what is likely?"""

from __future__ import annotations

import re
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

_EXPLAIN_LIKELY = re.compile(
    r"\bwhy\s+do\s+you\s+think\s+that\s+is\s+likely\b|"
    r"\bwhy\s+(?:is|was)\s+that\s+likely\b",
    re.I,
)
_WORLD_WITHOUT_SELF = re.compile(
    r"\b(stock\s+market|nasdaq|s&p|crypto|bitcoin|weather\s+forecast|"
    r"interest\s+rates?|election\s+results?)\b",
    re.I,
)


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
        self._last_prediction_id = ""

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
        if _EXPLAIN_LIKELY.search(cue or ""):
            return self._explain_last_prediction(cue)

        prediction = self.predict(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        top = prediction.outcomes[:3]
        public = prediction.to_public()
        public["ambiguous"] = bool(prediction.metadata.get("ambiguous"))
        if not top:
            public["answer"] = "Memory does not yet support a clear likely outcome."
            return public

        if prediction.metadata.get("ambiguous"):
            conflict_labels = list(prediction.metadata.get("conflict_labels") or [])
            if len(conflict_labels) < 2:
                conflict_labels = [o.label for o in top[:2]]
            public["answer"] = (
                "Remembered evidence conflicts: "
                + " and ".join(conflict_labels[:2])
                + f". Confidence is reduced ({prediction.confidence:.0%})."
            )
            return public

        bits = [
            f"{o.label} (~{o.probability:.0%})" for o in top if o.probability > 0.05
        ]
        public["answer"] = "Likely from memory: " + "; ".join(bits)
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

        # Outside autobiographical memory: do not invent world forecasts.
        if _WORLD_WITHOUT_SELF.search(cue or "") and not re.search(
            r"\b(i|me|my|usually|saturday|weekend|coffee|breakfast)\b",
            cue or "",
            re.I,
        ):
            pred = Prediction(
                id=new_id("prd"),
                cue=cue[:160],
                outcomes=[],
                confidence=0.0,
                created=time(),
                metadata={"insufficient_autobiographical_evidence": True},
            )
            self.store.predictions[pred.id] = pred
            self._last_prediction_id = pred.id
            self._predictions += 1
            self.validation.record_prediction(
                action="predict",
                prediction_id=pred.id,
                cue=cue[:80],
                outcome_count=0,
                confidence=0.0,
                predict=1,
                top_probability=0.0,
            )
            return pred

        field = self.activation.activate(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        seeds = {s.target_id for s in field.seeds}
        ranked = field.ranked_concepts(limit=8)
        scores: dict[str, float] = {}
        support: dict[str, list[str]] = {}
        why: dict[str, list[str]] = {}
        labels: dict[str, str] = {}

        # Autobiographical recurring patterns (primary evidence for habit prediction).
        pattern_hits = self._score_predictive_patterns(cue)
        for key, payload in pattern_hits.items():
            scores[key] = scores.get(key, 0.0) + float(payload["score"])
            support.setdefault(key, []).extend(list(payload["support"]))
            why.setdefault(key, []).extend(list(payload["why"]))
            labels[key] = str(payload["label"])

        for node in ranked:
            cid = node.target_id
            base = max(0.05, node.energy)
            if self.attention is not None:
                base *= 0.7 + 0.3 * self.attention.priority_of(cid)
            if self.forgetting is not None:
                base *= 0.5 + 0.5 * self.forgetting.factor(cid)
            # Activation alone is weak without autobiographical predictive support.
            if key_has_pattern := (cid in scores):
                scores[cid] = scores.get(cid, 0.0) + base * 0.35
            else:
                scores[cid] = scores.get(cid, 0.0) + base * 0.15
            why.setdefault(cid, []).append("activation")
            _ = key_has_pattern

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
                    bonus = 0.55 * weight
                    tag = "predicts"
                    if (edge.metadata or {}).get("autobiographical") or (
                        edge.metadata or {}
                    ).get("predictive_pattern"):
                        bonus *= 1.35
                        tag = "autobiographical_predicts"
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
                if neighbor.labels:
                    labels.setdefault(neighbor.id, neighbor.labels[0])

        # Prefer autobiographical pattern outcomes when present.
        if pattern_hits:
            scores = {k: float(v["score"]) for k, v in pattern_hits.items()}
            support = {k: list(v["support"]) for k, v in pattern_hits.items()}
            why = {k: list(v["why"]) for k, v in pattern_hits.items()}
            labels = {k: str(v["label"]) for k, v in pattern_hits.items()}
            # Merge autobiographical PREDICTS edges that match the same consequents.
            for cid in list(seeds)[:12]:
                for edge, neighbor in self.store.neighbors(cid):
                    if edge.relation != RelationKind.PREDICTS:
                        continue
                    meta = edge.metadata or {}
                    if not (
                        meta.get("autobiographical") or meta.get("predictive_pattern")
                    ):
                        continue
                    label = neighbor.labels[0] if neighbor.labels else ""
                    if not label:
                        continue
                    key = f"pattern:{label.casefold()}"
                    if key not in scores and label.casefold() not in {
                        str(v).casefold() for v in labels.values()
                    }:
                        continue
                    target_key = key if key in scores else next(
                        (
                            k
                            for k, lab in labels.items()
                            if lab.casefold() == label.casefold()
                        ),
                        "",
                    )
                    if not target_key:
                        continue
                    scores[target_key] = scores.get(target_key, 0.0) + 0.2 * edge.strength_forward
                    support.setdefault(target_key, []).append(edge.id)
                    why.setdefault(target_key, []).append("autobiographical_predicts")

        total = sum(max(0.0, v) for v in scores.values()) or 1.0
        outcomes: list[PredictedOutcome] = []
        for cid, raw in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8]:
            concept = self.store.concepts.get(cid)
            label = labels.get(cid, "")
            if not label and concept is not None and concept.labels:
                label = concept.labels[0]
            if not label and cid.startswith("pattern:"):
                label = cid.split(":", 1)[-1]
            if not label:
                continue
            prob = max(0.0, raw) / total
            prob = min(0.85, prob)
            outcomes.append(
                PredictedOutcome(
                    concept_id=cid,
                    label=label,
                    probability=prob,
                    support=list(dict.fromkeys(support.get(cid, [])))[:8],
                    why=list(dict.fromkeys(why.get(cid, [])))[:8],
                )
            )

        # Detect conflicting consequents for the same antecedent family.
        ambiguous = False
        conflict_labels: list[str] = []
        if any("opposing" in why.get(k, []) for k in pattern_hits):
            ambiguous = True
            neg = next(
                (
                    labels[k]
                    for k in pattern_hits
                    if "opposing_negative" in why.get(k, [])
                ),
                "",
            )
            pos = next(
                (
                    labels[k]
                    for k in pattern_hits
                    if "opposing_positive" in why.get(k, [])
                ),
                "",
            )
            conflict_labels = [x for x in (neg, pos) if x]
        elif len(outcomes) >= 2:
            top_labels = {o.label.casefold() for o in outcomes[:3]}
            if len(top_labels) >= 2 and any(
                "conflict" in w or "opposing" in w
                for oid in scores
                for w in why.get(oid, [])
            ):
                ambiguous = True
                conflict_labels = [o.label for o in outcomes[:2]]

        # Renormalize after cap
        s = sum(o.probability for o in outcomes) or 1.0
        for o in outcomes:
            o.probability = o.probability / s

        confidence = 0.0
        if outcomes:
            support_n = sum(len(o.support) for o in outcomes[:3])
            confidence = min(
                0.9,
                outcomes[0].probability * 0.55
                + min(0.25, support_n * 0.06)
                + (len(pattern_hits) * 0.05),
            )
            ad_n = len(self.store.adaptations)
            confidence = min(0.92, confidence + min(0.08, ad_n * 0.01))
            if ambiguous:
                confidence = min(confidence, 0.45)
        # No autobiographical predictive grounding → empty (honest unknown).
        has_autobio = bool(pattern_hits) or any(
            "autobiographical_predicts" in why.get(o.concept_id or "", [])
            or "predictive_pattern" in why.get(o.concept_id or "", [])
            or any(x.startswith("pattern") for x in o.why)
            for o in outcomes
        )
        if outcomes and not has_autobio and not any(
            "predicts" in o.why for o in outcomes
        ):
            outcomes = []
            confidence = 0.0

        pred = Prediction(
            id=new_id("prd"),
            cue=cue[:160],
            outcomes=outcomes,
            confidence=confidence,
            created=time(),
            source_concept_ids=[n.target_id for n in ranked[:6]],
            metadata={
                "ambiguous": ambiguous,
                "pattern_hit_count": len(pattern_hits),
                "conflict_labels": conflict_labels,
            },
        )
        self.store.predictions[pred.id] = pred
        self._last_prediction_id = pred.id
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

    def _score_predictive_patterns(self, cue: str) -> dict[str, dict[str, Any]]:
        """Score remembered predictive experiences against the cue."""
        cue_l = (cue or "").lower()
        cue_tokens = {
            tok
            for tok in re.findall(r"[a-z0-9]+", cue_l)
            if len(tok) > 2
            and tok
            not in {
                "likely",
                "what",
                "when",
                "will",
                "happen",
                "think",
                "that",
                "this",
                "have",
                "does",
                "most",
                "next",
                "after",
                "from",
                "memory",
                "based",
                "upon",
            }
        }
        grouped: dict[str, dict[str, Any]] = {}
        for exp in self.store.experiences.values():
            meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
            if not isinstance(meta, dict) or meta.get("predictive") != "1":
                continue
            ante = str(meta.get("pattern_antecedent") or "").strip()
            cons = str(meta.get("pattern_consequent") or "").strip()
            if not ante or not cons:
                continue
            try:
                strength = float(meta.get("pattern_strength") or 0.65)
            except (TypeError, ValueError):
                strength = 0.65
            ante_l = ante.lower()
            cons_l = cons.lower()
            ante_tokens = {
                tok for tok in re.findall(r"[a-z0-9]+", ante_l) if len(tok) > 2
            }
            cons_tokens = {
                tok for tok in re.findall(r"[a-z0-9]+", cons_l) if len(tok) > 2
            }
            overlap = cue_tokens & (ante_tokens | cons_tokens)

            # Habit schedule / productivity / coffee / rain cue bridges.
            # Saturday cues prefer Saturday habits; weekend-only habits do not tie.
            if "saturday" in cue_l and "saturday" in ante_l:
                overlap.add("saturday")
                strength = min(0.98, strength + 0.2)
            elif "weekend" in cue_l and "weekend" in ante_l:
                overlap.add("weekend")
                strength = min(0.98, strength + 0.12)
            elif (
                "saturday" in cue_l
                and "weekend" in ante_l
                and "saturday" not in ante_l
            ):
                # Do not treat weekend habits as Saturday predictions.
                continue
            if re.search(r"\bproductive|work\s+done\b", cue_l) and (
                "morning" in ante_l or "work" in cons_l
            ):
                overlap.add("productive")
                if "morning" in ante_l:
                    strength = min(0.98, strength + 0.12)
            if "coffee" in cue_l and "coffee" in ante_l:
                overlap.add("coffee")
                strength = min(0.98, strength + 0.12)
            if "breakfast" in cue_l and "breakfast" in ante_l:
                overlap.add("breakfast")
            if "rain" in cue_l and ("rain" in ante_l or "rain" in cons_l):
                overlap.add("rain")
                strength = min(0.98, strength + 0.15)
            if "sleep" in cue_l and ("sleep" in cons_l or "insomni" in cons_l):
                overlap.add("sleep")

            if not overlap:
                continue

            key = f"pattern:{cons.casefold()}"
            score = strength * (0.7 + 0.2 * len(overlap))
            polarity = "supports"
            if "sleep" in cons_l or "insomni" in cons_l or "help" in cons_l:
                if re.search(r"\b(helps?|better|easier)\b", cons_l):
                    polarity = "opposing_positive"
                else:
                    polarity = "opposing_negative"
            entry = grouped.setdefault(
                key,
                {
                    "score": 0.0,
                    "support": [],
                    "why": ["predictive_pattern"],
                    "label": cons,
                    "polarities": set(),
                },
            )
            entry["score"] = float(entry["score"]) + score
            entry["support"].append(exp.id)
            entry["why"].append(polarity)
            entry["polarities"].add(polarity)
            if len(entry["support"]) > 1:
                entry["score"] = float(entry["score"]) + 0.15

        polarities = {
            pol
            for payload in grouped.values()
            for pol in payload.get("polarities", set())
        }
        if "opposing_positive" in polarities and "opposing_negative" in polarities:
            for payload in grouped.values():
                payload["why"].append("opposing")
                payload["score"] = float(payload["score"]) * 0.7

        for payload in grouped.values():
            payload.pop("polarities", None)
        return grouped

    def _explain_last_prediction(self, cue: str) -> dict[str, Any]:
        pred = None
        if self._last_prediction_id:
            pred = self.store.predictions.get(self._last_prediction_id)
        if pred is None:
            recent = sorted(
                self.store.predictions.values(), key=lambda p: p.created, reverse=True
            )
            pred = recent[0] if recent else None
        if pred is None or not pred.outcomes:
            return {
                "id": "",
                "question": "Based upon memory, what is likely?",
                "cue": cue[:160],
                "outcomes": [],
                "confidence": 0.0,
                "answer": "Memory does not yet support a clear likely outcome.",
                "ambiguous": False,
                "plans": False,
                "decides": False,
                "source_concept_ids": [],
            }
        evidence_bits: list[str] = []
        for outcome in pred.outcomes[:3]:
            for sid in outcome.support:
                exp = self.store.experiences.get(sid)
                if exp is not None:
                    meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
                    raw = ""
                    if isinstance(meta, dict):
                        raw = str(meta.get("evidence") or "")
                    evidence_bits.append((raw or exp.summary or "").strip())
                    continue
                assoc = self.store.associations.get(sid)
                if assoc is None:
                    continue
                for eid in list(getattr(assoc, "evidence_ids", []) or [])[:2]:
                    exp = self.store.experiences.get(eid)
                    if exp is None:
                        continue
                    meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
                    raw = ""
                    if isinstance(meta, dict):
                        raw = str(meta.get("evidence") or "")
                    evidence_bits.append((raw or exp.summary or "").strip())
        evidence_bits = [b for b in dict.fromkeys(evidence_bits) if b][:4]
        if not evidence_bits:
            answer = (
                f"I predicted '{pred.outcomes[0].label}' from remembered associative "
                "structure, but I do not have a direct teaching quote on hand."
            )
        else:
            taught = "; ".join(evidence_bits)
            answer = (
                f"I predicted '{pred.outcomes[0].label}' because you previously taught me: "
                f"{taught}"
            )
            if pred.metadata.get("ambiguous"):
                answer += " Competing remembered outcomes reduced confidence."
        public = pred.to_public()
        public["answer"] = answer
        public["ambiguous"] = bool(pred.metadata.get("ambiguous"))
        return public

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
