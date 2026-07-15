"""Cognitive Routing Engine — intent → primary organ ownership.

The language model NEVER chooses which organ answers. Routing is determined
exclusively from Cognitive Intent Classification (D039).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from acm.authority.classification import MemoryRequestClassification, classify_memory_request
from acm.authority.taxonomy import (
    ORGAN_ASSOCIATIONS,
    ORGAN_CONCEPTS,
    ORGAN_CONFIDENCE,
    ORGAN_CONTEXT,
    ORGAN_EXPERIENCES,
    ORGAN_GOALS,
    ORGAN_IDENTITY,
    ORGAN_LEARNING,
    ORGAN_NONE,
    ORGAN_RECONCILIATION,
    ORGAN_REFLECTION,
    ORGAN_REMEMBERING,
    ORGAN_WORKING,
    CognitiveIntent,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine


@dataclass(frozen=True)
class CognitiveOwnership:
    """Exactly one primary cognitive owner; supporting organs may contribute."""

    intent: CognitiveIntent
    primary_organ: str
    supporting_organs: tuple[str, ...] = ()
    uncertain: bool = False
    confidence: float = 1.0
    rationale: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "primary_organ": self.primary_organ,
            "supporting_organs": list(self.supporting_organs),
            "uncertain": self.uncertain,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "schema": "cognitive_ownership.v1",
        }


_OWNERSHIP_TABLE: dict[CognitiveIntent, tuple[str, tuple[str, ...], str]] = {
    CognitiveIntent.ASSISTANT_IDENTITY: (
        ORGAN_IDENTITY,
        (),
        "assistant self-schema via Identity Organ",
    ),
    CognitiveIntent.USER_IDENTITY: (
        ORGAN_IDENTITY,
        (ORGAN_REMEMBERING, ORGAN_EXPERIENCES),
        "user identity schema; remembering supplements biography",
    ),
    CognitiveIntent.IDENTITY: (
        ORGAN_IDENTITY,
        (ORGAN_REMEMBERING,),
        "generic identity — Identity Organ primary",
    ),
    CognitiveIntent.AUTOBIOGRAPHY: (
        ORGAN_REMEMBERING,
        (ORGAN_IDENTITY, ORGAN_EXPERIENCES),
        "autobiographical reconstruction",
    ),
    CognitiveIntent.EXPERIENCE: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES,),
        "episodic experience retrieval",
    ),
    CognitiveIntent.REMEMBERING: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES, ORGAN_CONCEPTS),
        "Remembering Organ owns reconstruction",
    ),
    CognitiveIntent.LONG_TERM_MEMORY: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES,),
        "long-term retrieval via Remembering",
    ),
    CognitiveIntent.WORKING_MEMORY: (
        ORGAN_WORKING,
        (ORGAN_CONTEXT,),
        "working memory / attention residue",
    ),
    CognitiveIntent.CURRENT_CONTEXT: (
        ORGAN_CONTEXT,
        (ORGAN_WORKING,),
        "current context frame",
    ),
    CognitiveIntent.HISTORY: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES,),
        "conversational / session history as experiences",
    ),
    CognitiveIntent.DECISION_HISTORY: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES, ORGAN_REFLECTION),
        "past decisions as experienced memories",
    ),
    CognitiveIntent.PROJECT: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES, ORGAN_CONCEPTS, ORGAN_IDENTITY, ORGAN_GOALS),
        "project memory via remembering + identity project schema",
    ),
    CognitiveIntent.PATTERN: (
        ORGAN_REMEMBERING,
        (ORGAN_LEARNING,),
        "habitual / pattern memory",
    ),
    CognitiveIntent.GENERAL_MEMORY: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES, ORGAN_CONCEPTS),
        "unspecialized cognitive recall — Remembering primary",
    ),
    CognitiveIntent.CONCEPT: (
        ORGAN_CONCEPTS,
        (ORGAN_REMEMBERING, ORGAN_ASSOCIATIONS),
        "Concept Organ with remembering support",
    ),
    CognitiveIntent.ASSOCIATION: (
        ORGAN_ASSOCIATIONS,
        (ORGAN_CONCEPTS, ORGAN_REMEMBERING),
        "Association Organ owns relational answers",
    ),
    CognitiveIntent.PREFERENCE: (
        ORGAN_REMEMBERING,
        (ORGAN_EXPERIENCES,),
        "preferences reconstructed as remembered experiences",
    ),
    CognitiveIntent.GOAL: (
        ORGAN_GOALS,
        (ORGAN_REMEMBERING, ORGAN_IDENTITY, ORGAN_EXPERIENCES),
        "active goals + goal-biased remembering",
    ),
    CognitiveIntent.REFLECTION: (
        ORGAN_REFLECTION,
        (ORGAN_REMEMBERING,),
        "Reflection Organ",
    ),
    CognitiveIntent.LEARNING: (
        ORGAN_LEARNING,
        (ORGAN_REMEMBERING,),
        "Learning Organ",
    ),
    CognitiveIntent.CONFIDENCE: (
        ORGAN_CONFIDENCE,
        (ORGAN_REFLECTION,),
        "Confidence Organ / metacognitive certainty",
    ),
    CognitiveIntent.RECONCILIATION: (
        ORGAN_RECONCILIATION,
        (ORGAN_REMEMBERING,),
        "Reconciliation Organ",
    ),
    CognitiveIntent.UNCERTAIN: (
        ORGAN_REMEMBERING,
        (),
        "uncertain intent — conservative remembering route; LM does not own",
    ),
    CognitiveIntent.PROCEDURAL: (ORGAN_NONE, (), "host procedural task"),
    CognitiveIntent.REASONING: (ORGAN_NONE, (), "host reasoning"),
    CognitiveIntent.PLANNING: (ORGAN_NONE, (), "host planning (non-stored goals)"),
    CognitiveIntent.TOOL_REQUEST: (ORGAN_NONE, (), "host tool execution"),
    CognitiveIntent.GENERAL_KNOWLEDGE: (ORGAN_NONE, (), "host general knowledge"),
    CognitiveIntent.CONVERSATION_MANAGEMENT: (ORGAN_NONE, (), "host conversation mgmt"),
    CognitiveIntent.NOT_MEMORY: (ORGAN_NONE, (), "non-cognitive"),
}


def ownership_for_intent(
    intent: CognitiveIntent,
    *,
    uncertain: bool = False,
    confidence: float = 1.0,
) -> CognitiveOwnership:
    primary, supporting, rationale = _OWNERSHIP_TABLE.get(
        intent,
        (ORGAN_REMEMBERING, (), "fallback remembering"),
    )
    return CognitiveOwnership(
        intent=intent,
        primary_organ=primary,
        supporting_organs=supporting,
        uncertain=uncertain,
        confidence=confidence,
        rationale=rationale,
    )


@dataclass
class RoutingDecision:
    """Full classify → own → ready-to-execute decision."""

    classification: MemoryRequestClassification
    ownership: CognitiveOwnership
    reasoning_path: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "classification": self.classification.to_public(),
            "ownership": self.ownership.to_public(),
            "reasoning_path": list(self.reasoning_path),
            "schema": "cognitive_routing_decision.v1",
        }


class CognitiveRoutingEngine:
    """Classify request → determine cognitive owner → execute owning organ(s)."""

    def __init__(self, engine: CognitiveEngine) -> None:
        self.engine = engine

    def decide(self, request: str) -> RoutingDecision:
        path = ["classify_request"]
        classification = classify_memory_request(request)
        path.append(f"intent:{classification.intent.value}")
        if classification.uncertain:
            path.append("uncertain_classification")
        ownership = ownership_for_intent(
            classification.intent,
            uncertain=classification.uncertain,
            confidence=classification.confidence,
        )
        path.append(f"owner:{ownership.primary_organ}")
        for org in ownership.supporting_organs:
            path.append(f"support:{org}")
        return RoutingDecision(
            classification=classification,
            ownership=ownership,
            reasoning_path=path,
        )

    def execute(self, request: str) -> tuple[RoutingDecision, dict[str, Any]]:
        """Route to the primary organ and return organ payload + decision."""
        decision = self.decide(request)
        path = list(decision.reasoning_path)
        if decision.ownership.primary_organ == ORGAN_NONE:
            path.append("host_execution")
            decision.reasoning_path = path
            return decision, {
                "memory": None,
                "confidence": decision.classification.confidence,
                "explanation_class": "unknown",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": False,
                "experiences": [],
                "associations": [],
                "raw": {"host_owned": True},
            }

        payload = self._invoke(decision.ownership, request, path)
        decision.reasoning_path = path
        return decision, payload

    def _invoke(
        self,
        ownership: CognitiveOwnership,
        request: str,
        path: list[str],
    ) -> dict[str, Any]:
        intent = ownership.intent
        organ = ownership.primary_organ
        engine = self.engine

        if organ == ORGAN_IDENTITY:
            if intent == CognitiveIntent.USER_IDENTITY:
                path.append("user_identity_reconstruct")
                return self._user_identity(request)
            path.append("who_am_i")
            who = engine.who_am_i()
            return {
                "memory": who.get("answer"),
                "confidence": float(who.get("confidence") or 0.0),
                "explanation_class": who.get("explanation_class") or "experience",
                "ambiguous": False,
                "concepts": who.get("central_concepts") or [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": who,
            }

        if organ == ORGAN_LEARNING:
            path.append("learn")
            learned = engine.learn(cue=request)
            adaptations = learned.get("adaptations") or []
            lessons = learned.get("lessons") or []
            answer = learned.get("answer")
            conf = 0.75 if adaptations or lessons else 0.0
            if not answer and adaptations:
                answer = "; ".join(str(a) for a in lessons[:3]) or "Learned adaptations recorded."
            return {
                "memory": answer if adaptations or lessons else None,
                "confidence": conf,
                "explanation_class": "experience" if adaptations else "unknown",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": bool(adaptations or lessons),
                "experiences": [],
                "associations": [],
                "learning": adaptations or lessons,
                "raw": learned,
            }

        if organ == ORGAN_CONFIDENCE:
            path.append("how_certain_am_i")
            certain = engine.how_certain_am_i(request)
            return {
                "memory": certain.get("answer"),
                "confidence": float(certain.get("overall_confidence") or 0.0),
                "explanation_class": "experience",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": certain,
            }

        if organ == ORGAN_REFLECTION:
            path.append("what_do_i_think")
            thought = engine.what_do_i_think(request)
            return {
                "memory": thought.get("summary") or thought.get("answer"),
                "confidence": float(thought.get("confidence") or 0.5),
                "explanation_class": (
                    "unknown" if thought.get("insufficient_evidence") else "experience"
                ),
                "ambiguous": bool(thought.get("hypotheses")),
                "concepts": [],
                "cue_matched": not bool(thought.get("insufficient_evidence")),
                "experiences": [],
                "associations": [],
                "reflective": thought.get("outcomes") or [],
                "raw": thought,
            }

        if organ == ORGAN_RECONCILIATION:
            path.append("how_should_memory_reconcile")
            recon = engine.how_should_memory_reconcile(request)
            return {
                "memory": recon.get("answer"),
                "confidence": float((recon.get("reconciliation") or {}).get("confidence") or 0.4),
                "explanation_class": "contested",
                "ambiguous": True,
                "concepts": [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": recon,
            }

        if organ == ORGAN_ASSOCIATIONS:
            path.append("how_related")
            return self._associations(request)

        if organ == ORGAN_GOALS:
            path.append("active_goals")
            return self._goals(request)

        if organ in (ORGAN_WORKING, ORGAN_CONTEXT):
            path.append("working_or_context")
            return self._working_context(request)

        if organ == ORGAN_CONCEPTS:
            path.append("remember_concepts")
            # Concept answers currently via remembering reconstruction + labels.
            return self._remember(request)

        # Default: Remembering Organ (projects, prefs, experience, uncertain, …)
        path.append("remember")
        if intent == CognitiveIntent.PROJECT and ORGAN_IDENTITY in ownership.supporting_organs:
            path.append("project_schema_support")
            project_bits = self._project_support()
            base = self._remember(request)
            if project_bits.get("memory") and not base.get("memory"):
                return project_bits
            if project_bits.get("memory") and base.get("memory"):
                base["memory"] = f"{project_bits['memory']} {base['memory']}".strip()
                base["confidence"] = max(
                    float(base.get("confidence") or 0),
                    float(project_bits.get("confidence") or 0),
                )
                base["cue_matched"] = True
            return base
        return self._remember(request)

    def _user_identity(self, request: str) -> dict[str, Any]:
        engine = self.engine
        engine.identity.ensure_schemas()
        user = engine.identity.schema_concept("user")
        lines: list[str] = []
        for attr in user.attributes:
            if not attr.active:
                continue
            if attr.key == "name":
                lines.append(f"Your name is {attr.value}.")
            elif attr.key == "role":
                lines.append(f"You are {attr.value}.")
            elif attr.key == "statement":
                lines.append(str(attr.value).rstrip(".") + ".")
            else:
                lines.append(f"{attr.key}: {attr.value}.")
        remembered = engine.remember(request)
        mem = (remembered.answer or "").strip()
        if lines:
            text = " ".join(lines)
            if mem and mem.lower() not in text.lower():
                text = f"{text} {mem}".strip()
            conf = max(float(user.confidence or 0.4), float(remembered.confidence or 0))
            return {
                "memory": text,
                "confidence": conf,
                "explanation_class": "experience",
                "ambiguous": bool(remembered.ambiguous),
                "concepts": [{"id": user.id}],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": {"user_schema": user.id, "remember": remembered.answer},
            }
        return self._remember(request)

    def _goals(self, request: str) -> dict[str, Any]:
        engine = self.engine
        goals = list(engine.store.active_goals())
        if goals:
            titles = [g.title for g in goals[:8]]
            text = "Active goals: " + "; ".join(titles) + "."
            return {
                "memory": text,
                "confidence": 0.85,
                "explanation_class": "experience",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": {"goal_ids": [g.id for g in goals]},
            }
        # No open goals — try remembering for goal-related experiences.
        return self._remember(request)

    def _project_support(self) -> dict[str, Any]:
        engine = self.engine
        engine.identity.ensure_schemas()
        project = engine.identity.schema_concept("project")
        attrs = [a for a in project.attributes if a.active]
        if not attrs and not project.labels:
            return {"memory": None, "confidence": 0.0}
        bits = [f"{a.key}: {a.value}" for a in attrs[:6]]
        label = project.labels[0] if project.labels else "project"
        text = f"Project ({label}): " + "; ".join(bits) if bits else f"Tracked project: {label}."
        return {
            "memory": text,
            "confidence": float(project.confidence or 0.5),
            "explanation_class": "experience",
            "ambiguous": False,
            "concepts": [{"id": project.id}],
            "cue_matched": True,
            "experiences": [],
            "associations": [],
            "raw": {"project_id": project.id},
        }

    def _associations(self, request: str) -> dict[str, Any]:
        engine = self.engine
        left, right = _extract_relation_pair(request)
        if left and right:
            related = engine.how_related(left, right)
            answer = related.get("answer") or related.get("summary")
            return {
                "memory": answer,
                "confidence": float(related.get("confidence") or 0.5),
                "explanation_class": "experience" if answer else "unknown",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": bool(answer),
                "experiences": [],
                "associations": related.get("associations") or [],
                "raw": related,
            }
        return self._remember(request)

    def _working_context(self, request: str) -> dict[str, Any]:
        engine = self.engine
        tags = list(engine.context.tags) if engine.context else []
        activity = getattr(engine.context, "activity", "") if engine.context else ""
        place = getattr(engine.context, "place", "") if engine.context else ""
        parts: list[str] = []
        if activity:
            parts.append(f"Current activity: {activity}.")
        if place:
            parts.append(f"Place: {place}.")
        if tags:
            parts.append("Context tags: " + ", ".join(str(t) for t in tags[:12]) + ".")
        if parts:
            return {
                "memory": " ".join(parts),
                "confidence": 0.7,
                "explanation_class": "experience",
                "ambiguous": False,
                "concepts": [],
                "cue_matched": True,
                "experiences": [],
                "associations": [],
                "raw": {"tags": tags, "activity": activity, "place": place},
            }
        return self._remember(request)

    def _remember(self, request: str) -> dict[str, Any]:
        engine = self.engine
        remembered = engine.remember(request)
        recon = remembered.reconstruction or {}
        cue = request.lower()
        cue_tokens = [t for t in cue.split() if len(t) > 2]
        memory_text = (remembered.answer or "").strip()
        primary_label = str(recon.get("primary_label") or "")
        cue_matched = bool(memory_text) and (
            any(tok in memory_text.lower() for tok in cue_tokens)
            or any(tok in primary_label.lower() for tok in cue_tokens)
            or remembered.explanation_class.value == "preference"
            or bool(recon.get("identity_influenced"))
        )
        concepts = [{"id": cid} for cid in (remembered.activated_concept_ids or [])[:8]]
        experiences = [
            {"id": eid, "summary": summary}
            for eid, summary in zip(
                recon.get("experience_ids") or [],
                recon.get("experience_summaries") or [],
                strict=False,
            )
        ]
        associations = [{"id": aid} for aid in (recon.get("association_ids") or [])[:8]]
        return {
            "memory": memory_text or None,
            "confidence": float(remembered.confidence),
            "explanation_class": remembered.explanation_class.value,
            "ambiguous": bool(remembered.ambiguous),
            "concepts": concepts,
            "cue_matched": cue_matched,
            "experiences": experiences,
            "associations": associations,
            "raw": recon,
        }


_REL_PATTERNS = (
    re.compile(
        r"how\s+(?:are|is)\s+(.+?)\s+(?:and|to|with)\s+(.+?)\s+related",
        re.I,
    ),
    re.compile(
        r"relationship\s+between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
        re.I,
    ),
    re.compile(
        r"how\s+do(?:es)?\s+(.+?)\s+relate\s+to\s+(.+?)(?:\?|$)",
        re.I,
    ),
)


def _extract_relation_pair(request: str) -> tuple[str | None, str | None]:
    for pat in _REL_PATTERNS:
        m = pat.search(request or "")
        if m:
            return m.group(1).strip(" .?,"), m.group(2).strip(" .?,")
    return None, None
