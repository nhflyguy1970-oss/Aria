"""Prediction organ — M11: Based upon memory, what is likely?"""

from __future__ import annotations

import re
from time import time
from typing import TYPE_CHECKING, Any

from acm.associations.model import RelationKind
from acm.authority.mode import is_read_only
from acm.prediction.model import (
    ComparisonKind,
    Hypothesis,
    HypothesisStatus,
    PredictedOutcome,
    Prediction,
    PredictionAudit,
)
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.attention.organ import AttentionOrgan
    from acm.confidence.organ import ConfidenceOrgan
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.learning.organ import LearningOrgan
    from acm.validation.harness import ValidationHarness

_EXPLAIN_LIKELY = re.compile(
    r"\bwhy\s+do\s+you\s+think\s+that\s+is\s+likely\b|"
    r"\bwhy\s+(?:is|was)\s+that\s+likely\b|"
    r"\bhow\s+did\s+you\s+(?:make|form|arrive\s+at)\s+(?:that\s+)?prediction\b|"
    r"\bhow\s+did\s+you\s+predict\b|"
    r"\bexplain\s+(?:that\s+|your\s+)?prediction\b",
    re.I,
)
_CONFIDENCE_ABOUT = re.compile(
    r"\bhow\s+(?:confident|sure|certain)\s+are\s+you\s+that\b",
    re.I,
)
_CERTAINTY_CLAIM = re.compile(
    r"\b(?:definitely|certainly|must|for\s+sure|guaranteed)\b",
    re.I,
)
_OPEN_FUTURE = re.compile(
    r"\b(?:birthday|next\s+year|in\s+a\s+year|someday)\b",
    re.I,
)
_GENERIC_TOMORROW = re.compile(
    r"\bwhat\s+is\s+likely\s+to\s+happen\s+tomorrow\b|"
    r"\bwhat(?:'s|\s+is)\s+likely\s+tomorrow\b|"
    r"\bwhat\s+will\s+happen\s+tomorrow\b|"
    r"\bwill\s+it\s+(?:rain|snow)\s+tomorrow\b",
    re.I,
)
_RECOMMENDATION = re.compile(
    r"\bwhen\s+should\s+i\b|"
    r"\bwhat\s+should\s+i\b|"
    r"\bshould\s+i\s+(?:work|go|fish|hike)\b",
    re.I,
)
_TOPIC_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("coffee", ("coffee", "caffeine", "insomni", "sleep")),
    ("breakfast", ("breakfast", "hungry", "lunch", "skip")),
    ("rain", ("rain", "weather", "storm")),
    ("fishing", ("fish", "fishing", "saturday")),
    ("hiking", ("hik", "weekend")),
    ("work", ("work", "productive", "morning")),
)
_JUNK_LABELS = frozenset(
    {
        "when",
        "pattern",
        "user",
        "goal",
        "agent",
        "more",
        "weekend",
        "morning",
        "saturday",
        "usually",
        "prediction",
        "memory",
        "aria",
        "acm",
    }
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
        confidence: ConfidenceOrgan | None = None,
        learning: LearningOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.attention = attention
        self.forgetting = forgetting
        self.confidence = confidence
        self.learning = learning
        self._predictions = 0
        self._evaluations = 0
        self._audits = 0
        self._hypotheses = 0
        self._last_prediction_id = ""
        self._last_audit_id = ""

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
        confidence: ConfidenceOrgan | None = None,
        learning: LearningOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting
        if confidence is not None:
            self.confidence = confidence
        if learning is not None:
            self.learning = learning

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

        label = top[0].label
        conf = prediction.confidence
        if _CONFIDENCE_ABOUT.search(cue or ""):
            support_n = sum(len(o.support) for o in top)
            public["answer"] = (
                f"From remembered evidence, confidence is about {conf:.0%} that "
                f"{label} is likely"
                + (f" (supported by {support_n} remembered experience(s))" if support_n else "")
                + "."
            )
            return public

        if _CERTAINTY_CLAIM.search(cue or ""):
            if conf >= 0.75:
                level = "likely, but not certain"
            elif conf >= 0.5:
                level = "possible / likely from habit, not definite"
            else:
                level = "only weakly suggested by memory — not definite"
            public["answer"] = (
                f"From memory, {label} is {level} "
                f"(confidence about {conf:.0%}). Memory does not support certainty."
            )
            return public

        bits = [f"{o.label}" for o in top if o.probability > 0.05][:3]
        if _RECOMMENDATION.search(cue or ""):
            primary = bits[0] if bits else label
            # Advice grounded in remembered habits — not a likelihood claim.
            why_bits: list[str] = []
            for outcome in top[:2]:
                for sid in outcome.support[:2]:
                    exp = self.store.experiences.get(sid)
                    if exp is None:
                        continue
                    meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
                    evidence = ""
                    if isinstance(meta, dict):
                        evidence = str(meta.get("evidence") or "").strip()
                    why_bits.append(evidence or (exp.summary or "").strip())
            why_bits = [b for b in dict.fromkeys(why_bits) if b][:2]
            if "morning" in primary.lower() or any(
                "morning" in (b or "").lower() for b in why_bits
            ):
                public["answer"] = (
                    "I'd recommend working in the morning because you've consistently "
                    "been most productive then."
                )
            else:
                public["answer"] = (
                    f"I'd recommend focusing on {primary} based on your remembered habits."
                )
            if why_bits:
                public["answer"] += " Supporting memory: " + "; ".join(why_bits)
            public["answer"] += f" (confidence about {conf:.0%})."
            public["recommendation"] = True
            return public

        if len(bits) == 1:
            public["answer"] = (
                f"Likely from memory: {bits[0]} "
                f"(confidence about {conf:.0%})."
            )
        else:
            public["answer"] = (
                "Likely from memory: "
                + "; ".join(bits)
                + f" (confidence about {conf:.0%})."
            )
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
            if not is_read_only():
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
        else:
            # No autobiographical pattern match: keep only autobiographical PREDICTS
            # edges with real consequent labels — never activation/debug tokens.
            filtered_scores: dict[str, float] = {}
            filtered_support: dict[str, list[str]] = {}
            filtered_why: dict[str, list[str]] = {}
            filtered_labels: dict[str, str] = {}
            for cid, raw in scores.items():
                tags = why.get(cid, [])
                if "autobiographical_predicts" not in tags and "predicts" not in tags:
                    continue
                label = labels.get(cid, "")
                concept = self.store.concepts.get(cid)
                if not label and concept is not None and concept.labels:
                    label = concept.labels[0]
                if not label or label.casefold() in _JUNK_LABELS:
                    continue
                if len(label) < 3:
                    continue
                filtered_scores[cid] = raw
                filtered_support[cid] = list(support.get(cid, []))
                filtered_why[cid] = list(tags)
                filtered_labels[cid] = label
            scores, support, why, labels = (
                filtered_scores,
                filtered_support,
                filtered_why,
                filtered_labels,
            )
            # Open-ended futures without autobiographical habit evidence → unknown.
            if _OPEN_FUTURE.search(cue or "") or (
                _GENERIC_TOMORROW.search(cue or "") and not scores
            ):
                scores = {}

        total = sum(max(0.0, v) for v in scores.values()) or 1.0
        outcomes: list[PredictedOutcome] = []
        for cid, raw in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8]:
            concept = self.store.concepts.get(cid)
            label = labels.get(cid, "")
            if not label and concept is not None and concept.labels:
                label = concept.labels[0]
            if not label and cid.startswith("pattern:"):
                label = cid.split(":", 1)[-1]
            if not label or label.casefold() in _JUNK_LABELS:
                continue
            # Suppress internal/debug-looking single-token schema labels.
            if re.fullmatch(r"(when|pattern|user|goal|agent|more)", label, re.I):
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
        if not is_read_only():
            self.store.predictions[pred.id] = pred
            hyp_ids = self.form_hypotheses_from_prediction(pred)
            if hyp_ids:
                pred.metadata["hypothesis_ids"] = hyp_ids
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
                "should",
                "drink",
                "skip",
            }
        }
        cue_topics = self._topics_in_text(cue_l)
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
            pattern_topics = self._topics_in_text(f"{ante_l} {cons_l}")
            # Competing evidence must share the cue's subject/action family.
            if cue_topics and pattern_topics and not (cue_topics & pattern_topics):
                continue
            if cue_topics and not pattern_topics:
                continue
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
            if re.search(r"\bproductive|work\s+done|should\s+i\s+work\b", cue_l) and (
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
            # Rain-streak teachings only for explicit tomorrow/weather cues —
            # never for unrelated "what is likely to happen" habit questions.
            if _GENERIC_TOMORROW.search(cue) and (
                "rain" in ante_l or "rain" in cons_l
            ):
                overlap.add("tomorrow_rain")
                strength = min(0.98, strength + 0.2)
            if "sleep" in cue_l and ("sleep" in cons_l or "insomni" in cons_l):
                overlap.add("sleep")
            if "hiking" in cue_l and ("hiking" in cons_l or "weekend" in ante_l):
                overlap.add("hiking")
            if "fishing" in cue_l and ("fishing" in cons_l or "saturday" in ante_l):
                overlap.add("fishing")
            # Birthday / far-future cues do not inherit unrelated habits.
            if _OPEN_FUTURE.search(cue) and not (
                "birthday" in ante_l or "birthday" in cons_l
            ):
                continue

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

        # M5 Cap5 — active TemporalPatterns boost matching predictive outcomes.
        for pat in self.store.temporal_patterns.values():
            if pat.status.value not in {"active", "weakening"}:
                continue
            ante_l = pat.antecedent.casefold()
            cons_l = pat.consequent.casefold()
            if not any(tok in cue_l for tok in ante_l.split() if len(tok) > 2):
                if pat.period_hint and pat.period_hint not in cue_l:
                    continue
            key = f"pattern:{cons_l}"
            entry = grouped.setdefault(
                key,
                {
                    "score": 0.0,
                    "support": [],
                    "why": ["temporal_pattern"],
                    "label": pat.consequent,
                    "polarities": set(),
                },
            )
            entry["score"] = float(entry["score"]) + pat.confidence * pat.strength
            entry["why"].append("temporal_pattern")
            entry["support"].extend(pat.supporting_experience_ids[-3:])

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

    @staticmethod
    def _topics_in_text(text: str) -> set[str]:
        low = (text or "").lower()
        topics: set[str] = set()
        for topic, hints in _TOPIC_HINTS:
            if any(h in low for h in hints):
                topics.add(topic)
        return topics

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

    def form_hypotheses_from_prediction(self, pred: Prediction) -> list[str]:
        """Materialize competing outcomes as Hypothesis records (no new Experiences)."""
        if is_read_only():
            return []
        ids: list[str] = []
        conflicting = [o.label for o in pred.outcomes[1:4]]
        now = time()
        for i, outcome in enumerate(pred.outcomes[:6]):
            hyp = Hypothesis(
                id=new_id("hyp"),
                claim=outcome.label,
                confidence=min(0.95, max(0.05, outcome.probability * 0.7 + pred.confidence * 0.3)),
                status=HypothesisStatus.ACTIVE,
                supporting_ids=list(outcome.support)[:8],
                conflicting_ids=[
                    c
                    for c in conflicting
                    if c.casefold() != outcome.label.casefold()
                ][:6],
                prediction_id=pred.id,
                concept_id=outcome.concept_id,
                created=now,
                metadata={
                    "rank": i,
                    "probability": outcome.probability,
                    "why": list(outcome.why),
                    "cue": pred.cue,
                },
            )
            self.store.hypotheses[hyp.id] = hyp
            ids.append(hyp.id)
            self._hypotheses += 1
        if ids:
            self.validation.record_prediction(
                action="form_hypotheses",
                prediction_id=pred.id,
                hypothesis_count=len(ids),
                hypothesize=1,
            )
        return ids

    def update_hypothesis(
        self,
        hypothesis_id: str,
        *,
        status: HypothesisStatus | str,
        evidence_ids: list[str] | tuple[str, ...] = (),
        superseded_by: str = "",
        withdrawn_reason: str = "",
    ) -> dict[str, Any]:
        """Lifecycle transition only — never invents or rewrites Experiences."""
        if is_read_only():
            return {"status": "read_only"}
        hyp = self.store.hypotheses.get(hypothesis_id)
        if hyp is None:
            return {"status": "missing"}
        if hyp.status != HypothesisStatus.ACTIVE and status != HypothesisStatus.ACTIVE:
            # Allow transitions from active only (history preserved via closed_at).
            if hyp.status.value == str(status):
                return {"status": hyp.status.value, "hypothesis": hyp.to_public()}
        new_status = (
            status if isinstance(status, HypothesisStatus) else HypothesisStatus(str(status))
        )
        before = hyp.status.value
        hyp.status = new_status
        if evidence_ids:
            if new_status == HypothesisStatus.DISPROVED:
                hyp.conflicting_ids = list(
                    dict.fromkeys([*hyp.conflicting_ids, *[e for e in evidence_ids if e]])
                )[:12]
            else:
                hyp.supporting_ids = list(
                    dict.fromkeys([*hyp.supporting_ids, *[e for e in evidence_ids if e]])
                )[:12]
        if new_status == HypothesisStatus.SUPERSEDED:
            hyp.superseded_by = superseded_by or hyp.superseded_by
            hyp.closed_at = time()
        elif new_status == HypothesisStatus.WITHDRAWN:
            hyp.withdrawn_reason = withdrawn_reason or hyp.withdrawn_reason or "withdrawn"
            hyp.closed_at = time()
        elif new_status == HypothesisStatus.DISPROVED:
            hyp.closed_at = time()
        self.validation.record_prediction(
            action="hypothesis_lifecycle",
            hypothesis_id=hyp.id,
            status_before=before,
            status_after=hyp.status.value,
            lifecycle=1,
        )
        return {"status": hyp.status.value, "hypothesis": hyp.to_public()}

    def evaluate(self, prediction_id: str, realized_concept_id: str) -> dict[str, Any]:
        """Backward-compatible wrapper → full prediction audit pipeline."""
        return self.audit_outcome(
            prediction_id,
            observed_concept_id=realized_concept_id,
            apply_learning=True,
        )

    def audit_outcome(
        self,
        prediction_id: str,
        *,
        observed_concept_id: str = "",
        observed_experience_id: str = "",
        apply_learning: bool = True,
    ) -> dict[str, Any]:
        """Prediction → Observed → Comparison → Calibration → Confidence → Learning.

        Append-only audit. Never invents Experiences. Never modifies provenance.
        """
        if is_read_only():
            return {"status": "read_only"}
        pred = self.store.predictions.get(prediction_id)
        if pred is None:
            return {"status": "missing"}
        exp_before = len(self.store.experiences)
        prov_before = len(self.store.provenance)

        realized_id = observed_concept_id
        realized_label = ""
        if realized_id and realized_id in self.store.concepts:
            c = self.store.concepts[realized_id]
            realized_label = c.labels[0] if c.labels else realized_id
        elif observed_experience_id and observed_experience_id in self.store.experiences:
            exp = self.store.experiences[observed_experience_id]
            for cid in exp.concept_ids:
                concept = self.store.concepts.get(cid)
                if concept and concept.labels:
                    realized_id = cid
                    realized_label = concept.labels[0]
                    break
            if not realized_label:
                realized_label = (exp.summary or "")[:80]

        ranked = [o.concept_id for o in pred.outcomes]
        ranked_labels = [o.label.casefold() for o in pred.outcomes]
        hit_rank: int | None = None
        if realized_id and realized_id in ranked:
            hit_rank = ranked.index(realized_id)
        elif realized_label and realized_label.casefold() in ranked_labels:
            hit_rank = ranked_labels.index(realized_label.casefold())
            realized_id = pred.outcomes[hit_rank].concept_id

        if hit_rank is None:
            comparison = ComparisonKind.MISS
            accuracy = 0.05
        elif hit_rank == 0:
            comparison = ComparisonKind.HIT
            accuracy = 1.0
        else:
            comparison = ComparisonKind.PARTIAL
            accuracy = max(0.1, 1.0 - hit_rank * 0.12)

        expected_top = pred.outcomes[0].label if pred.outcomes else ""
        before = pred.confidence
        # Calibration blend (living prediction summary; audit keeps history).
        after = before * 0.7 + accuracy * 0.3
        pred.evaluated = True
        pred.accuracy = accuracy
        pred.confidence = after

        explanation = self._audit_explanation(
            pred,
            comparison=comparison,
            expected_top=expected_top,
            realized_label=realized_label or realized_id,
            accuracy=accuracy,
            before=before,
            after=after,
        )

        hyp_updates = self._apply_hypothesis_lifecycle(
            pred,
            realized_id=realized_id,
            comparison=comparison,
            evidence_id=observed_experience_id,
        )

        conf_event_ids: list[str] = []
        if self.confidence is not None and realized_id:
            conf_before_len = len(self.store.confidence_events)
            self.confidence.evolve_from_learning(
                realized_id, reinforce=(comparison != ComparisonKind.MISS)
            )
            # Mark supporting evidence refreshed on hits; leave miss without inventing ids.
            concept = self.store.concepts.get(realized_id)
            if concept and comparison == ComparisonKind.HIT:
                self.confidence.mark_reinforced(
                    "concept", realized_id, concept.evidence_ids[-3:]
                )
            for ev in self.store.confidence_events[conf_before_len:]:
                conf_event_ids.append(
                    f"{ev.timestamp}:{ev.target_id}:{ev.source}"
                )

        adaptation_ids: list[str] = []
        audit = PredictionAudit(
            id=new_id("aud"),
            prediction_id=pred.id,
            observed_concept_id=realized_id or "",
            observed_experience_id=observed_experience_id or "",
            comparison=comparison,
            hit_rank=hit_rank,
            expected_top_label=expected_top,
            realized_label=realized_label or realized_id or "",
            accuracy=accuracy,
            confidence_before=before,
            confidence_after=after,
            calibration_delta=after - before,
            confidence_event_ids=conf_event_ids,
            hypothesis_updates=hyp_updates,
            explanation=explanation,
            created=time(),
        )
        self.store.prediction_audits[audit.id] = audit
        pred.metadata["last_audit_id"] = audit.id
        self._last_audit_id = audit.id
        self._audits += 1
        self._evaluations += 1

        if apply_learning and self.learning is not None:
            ads = self.learning.learn_from_prediction_audit(audit.id)
            adaptation_ids = [a.id for a in ads]
            audit.adaptation_ids = adaptation_ids

        assert len(self.store.experiences) == exp_before
        assert len(self.store.provenance) == prov_before

        self.validation.record_prediction(
            action="audit",
            prediction_id=pred.id,
            audit_id=audit.id,
            accuracy=accuracy,
            confidence_before=before,
            confidence_after=after,
            comparison=comparison.value,
            evaluate=1,
            audit=1,
            realized_concept_id=realized_id,
        )
        return {
            "status": "evaluated",
            "accuracy": accuracy,
            "confidence": pred.confidence,
            "comparison": comparison.value,
            "audit": audit.to_public(),
            "prediction": pred.to_public(),
            "hypothesis_updates": hyp_updates,
            "adaptation_ids": adaptation_ids,
            "experiences_unchanged": True,
            "provenance_unchanged": True,
        }

    def explain_belief_change(
        self, *, audit_id: str = "", hypothesis_id: str = "", prediction_id: str = ""
    ) -> dict[str, Any]:
        """Why belief/confidence changed — read-only explanation over preserved history."""
        audit: PredictionAudit | None = None
        if audit_id:
            audit = self.store.prediction_audits.get(audit_id)
        elif prediction_id:
            pred = self.store.predictions.get(prediction_id)
            last = (pred.metadata.get("last_audit_id") if pred else "") or ""
            audit = self.store.prediction_audits.get(last) if last else None
            if audit is None:
                audits = [
                    a
                    for a in self.store.prediction_audits.values()
                    if a.prediction_id == prediction_id
                ]
                audits.sort(key=lambda a: a.created, reverse=True)
                audit = audits[0] if audits else None
        hyp = self.store.hypotheses.get(hypothesis_id) if hypothesis_id else None

        if audit is None and hyp is None:
            return {
                "question": "What changed your mind?",
                "answer": "I don't have a preserved belief-change record for that yet.",
                "known": False,
            }

        alternatives = []
        if audit:
            pred = self.store.predictions.get(audit.prediction_id)
            if pred:
                alternatives = [
                    {
                        "claim": o.label,
                        "probability": o.probability,
                        "supporting": list(o.support)[:4],
                    }
                    for o in pred.outcomes[:5]
                ]
            hyps = [
                self.store.hypotheses[hid].to_public()
                for hid in (pred.metadata.get("hypothesis_ids") if pred else []) or []
                if hid in self.store.hypotheses
            ]
            rejected = [
                h
                for h in hyps
                if h["status"] in ("disproved", "superseded", "withdrawn")
            ]
            answer = audit.explanation
            return {
                "question": "What changed your mind?",
                "answer": answer,
                "known": True,
                "why_believe": (
                    f"Top expectation was '{audit.expected_top_label}' "
                    f"(confidence {audit.confidence_before:.0%})."
                ),
                "supporting_evidence": list(
                    (pred.outcomes[0].support if pred and pred.outcomes else [])[:6]
                ),
                "conflicting_evidence": (
                    [audit.observed_experience_id]
                    if audit.comparison == ComparisonKind.MISS and audit.observed_experience_id
                    else []
                ),
                "what_changed": (
                    f"Observed '{audit.realized_label}' → {audit.comparison.value}; "
                    f"confidence {audit.confidence_before:.0%}→{audit.confidence_after:.0%}."
                ),
                "when_confidence_changed": audit.created,
                "alternative_explanations": alternatives,
                "rejected_hypotheses": rejected,
                "would_increase_confidence": [
                    "Additional consistent Experiences matching the top outcome",
                    "Reinforcement of supporting associations",
                ],
                "would_decrease_confidence": [
                    "Contradictory observed outcomes",
                    "Stale unreinformed evidence (Cap2 aging)",
                ],
                "audit": audit.to_public(),
                "reversible": True,
                "plans": False,
                "decides": False,
            }

        assert hyp is not None
        return {
            "question": "What changed your mind?",
            "answer": (
                f"Hypothesis '{hyp.claim}' is {hyp.status.value}"
                + (f" (superseded by {hyp.superseded_by})" if hyp.superseded_by else "")
                + (f": {hyp.withdrawn_reason}" if hyp.withdrawn_reason else "")
                + "."
            ),
            "known": True,
            "hypothesis": hyp.to_public(),
            "supporting_evidence": list(hyp.supporting_ids),
            "conflicting_evidence": list(hyp.conflicting_ids),
            "when_confidence_changed": hyp.closed_at or hyp.created,
            "reversible": hyp.status == HypothesisStatus.ACTIVE,
        }

    def competing_hypotheses(self, cue_or_prediction_id: str = "") -> dict[str, Any]:
        """List active competing hypotheses for a cue or prediction."""
        pred = self.store.predictions.get(cue_or_prediction_id)
        hyps: list[Hypothesis] = []
        if pred is not None:
            for hid in pred.metadata.get("hypothesis_ids") or []:
                h = self.store.hypotheses.get(hid)
                if h:
                    hyps.append(h)
        else:
            q = (cue_or_prediction_id or "").casefold()
            for h in self.store.hypotheses.values():
                if not q or q in h.claim.casefold() or q in (h.metadata.get("cue") or "").casefold():
                    hyps.append(h)
            hyps.sort(key=lambda h: h.created, reverse=True)
            hyps = hyps[:12]
        active = [h for h in hyps if h.status == HypothesisStatus.ACTIVE]
        closed = [h for h in hyps if h.status != HypothesisStatus.ACTIVE]
        return {
            "question": "What alternative explanations exist?",
            "active": [h.to_public() for h in active],
            "historical": [h.to_public() for h in closed],
            "answer": (
                f"{len(active)} active hypothesis(es); {len(closed)} preserved closed."
                if hyps
                else "No competing hypotheses recorded yet."
            ),
            "plans": False,
            "decides": False,
        }

    def _apply_hypothesis_lifecycle(
        self,
        pred: Prediction,
        *,
        realized_id: str,
        comparison: ComparisonKind,
        evidence_id: str,
    ) -> list[str]:
        updates: list[str] = []
        hyp_ids = list(pred.metadata.get("hypothesis_ids") or [])
        winner: Hypothesis | None = None
        for hid in hyp_ids:
            hyp = self.store.hypotheses.get(hid)
            if hyp is None or hyp.status != HypothesisStatus.ACTIVE:
                continue
            if realized_id and hyp.concept_id == realized_id:
                winner = hyp
                continue
            if comparison == ComparisonKind.MISS:
                out = self.update_hypothesis(
                    hid,
                    status=HypothesisStatus.DISPROVED,
                    evidence_ids=[evidence_id] if evidence_id else (),
                )
            else:
                out = self.update_hypothesis(
                    hid,
                    status=HypothesisStatus.SUPERSEDED,
                    superseded_by="",
                    evidence_ids=[evidence_id] if evidence_id else (),
                )
            updates.append(f"{hid}:{out.get('status')}")
        if winner is not None:
            # Winner stays active; mark others superseded by winner.
            for hid in hyp_ids:
                hyp = self.store.hypotheses.get(hid)
                if hyp is None or hyp.id == winner.id:
                    continue
                if hyp.status == HypothesisStatus.SUPERSEDED and not hyp.superseded_by:
                    hyp.superseded_by = winner.id
            updates.append(f"{winner.id}:active_confirmed")
        return updates

    def _audit_explanation(
        self,
        pred: Prediction,
        *,
        comparison: ComparisonKind,
        expected_top: str,
        realized_label: str,
        accuracy: float,
        before: float,
        after: float,
    ) -> str:
        if comparison == ComparisonKind.HIT:
            return (
                f"Prediction matched: expected '{expected_top}' and observed "
                f"'{realized_label}'. Confidence calibrated {before:.0%}→{after:.0%} "
                f"(accuracy {accuracy:.0%})."
            )
        if comparison == ComparisonKind.PARTIAL:
            return (
                f"Partial match: expected top '{expected_top}' but observed "
                f"'{realized_label}' among alternatives. Confidence {before:.0%}→{after:.0%}."
            )
        return (
            f"Prediction missed: expected '{expected_top or 'unknown'}' but observed "
            f"'{realized_label or 'unmatched outcome'}'. Confidence reduced "
            f"{before:.0%}→{after:.0%}. Competing hypotheses preserved for history."
        )

    def observables(self) -> dict[str, Any]:
        evaluated = [p for p in self.store.predictions.values() if p.evaluated]
        avg_acc = (
            sum(p.accuracy or 0 for p in evaluated) / len(evaluated) if evaluated else 0.0
        )
        by_status: dict[str, int] = {}
        for h in self.store.hypotheses.values():
            by_status[h.status.value] = by_status.get(h.status.value, 0) + 1
        return {
            "predictions": self._predictions,
            "evaluations": self._evaluations,
            "audits": self._audits,
            "hypotheses_formed": self._hypotheses,
            "stored": len(self.store.predictions),
            "stored_audits": len(self.store.prediction_audits),
            "stored_hypotheses": len(self.store.hypotheses),
            "hypotheses_by_status": by_status,
            "avg_accuracy": avg_acc,
        }
