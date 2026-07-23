"""Cognitive organ handlers — only organs may terminate cognitive requests.

Infrastructure (store substrate, indexes, persistence) may support organs but
never appear as the cognitive endpoint (D040).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from acm.authority.taxonomy import (
    ORGAN_ASSOCIATIONS,
    ORGAN_CONCEPTS,
    ORGAN_CONFIDENCE,
    ORGAN_CONTEXT,
    ORGAN_EXPERIENCES,
    ORGAN_GOALS,
    ORGAN_IDENTITY,
    ORGAN_LEARNING,
    ORGAN_PREDICTION,
    ORGAN_RECONCILIATION,
    ORGAN_REFLECTION,
    ORGAN_REMEMBERING,
    ORGAN_WORKING,
    CognitiveIntent,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

# Names that must never appear as terminated_at / cognitive authority.
FORBIDDEN_TERMINALS: frozenset[str] = frozenset(
    {
        "memory_store",
        "memorystore",
        "memory_engine",
        "memoryengine",
        "knowledge_engine",
        "knowledgeengine",
        "search_engine",
        "searchengine",
        "database",
        "index",
        "vector_store",
        "vectorstore",
        "cache",
        "provider",
        "language_model",
        "llm",
        "storage",
        "sqlite",
        "raw_store",
        "host",
    }
)

COGNITIVE_TERMINALS: frozenset[str] = frozenset(
    {
        ORGAN_IDENTITY,
        ORGAN_REMEMBERING,
        ORGAN_LEARNING,
        ORGAN_REFLECTION,
        ORGAN_ASSOCIATIONS,
        ORGAN_CONFIDENCE,
        ORGAN_RECONCILIATION,
        ORGAN_CONCEPTS,
        ORGAN_EXPERIENCES,
        ORGAN_GOALS,
        ORGAN_WORKING,
        ORGAN_CONTEXT,
        ORGAN_PREDICTION,
    }
)

_ASSISTANT_BLEED = re.compile(
    r"\bI am \w[\w\-]*\.?|\bMy role is\b|\bI am known as\b|\bCapabilities:\b",
    re.I,
)
_DICTISH = re.compile(r"^\s*[\{\[]")


@dataclass
class OrganContribution:
    """One organ's contribution to a cognitive reconstruction."""

    organ: str
    memory: str | None
    confidence: float
    explanation_class: str = "unknown"
    ambiguous: bool = False
    cue_matched: bool = False
    concepts: list[dict[str, Any]] = field(default_factory=list)
    experiences: list[dict[str, Any]] = field(default_factory=list)
    associations: list[dict[str, Any]] = field(default_factory=list)
    reflective: list[Any] = field(default_factory=list)
    learning: list[Any] = field(default_factory=list)
    reconstruction_steps: list[str] = field(default_factory=list)
    # Substrate only — never shown as cognitive authority.
    substrate_touched: tuple[str, ...] = ()

    def to_public(self) -> dict[str, Any]:
        return {
            "organ": self.organ,
            "has_memory": bool(self.memory),
            "confidence": self.confidence,
            "explanation_class": self.explanation_class,
            "cue_matched": self.cue_matched,
            "substrate_touched": list(self.substrate_touched),
            "reconstruction_steps": list(self.reconstruction_steps),
        }


def sanitize_cognitive_text(text: str | None, *, agent_id: str = "") -> str | None:
    """Refuse raw storage dumps and strip assistant identity bleed for user answers."""
    if text is None:
        return None
    if not isinstance(text, str):
        # Never allow dict/list adaptation records as "memory".
        return _summarize_non_text(text)
    s = text.strip()
    if not s:
        return None
    if _DICTISH.match(s) or ("'id':" in s and "'kind':" in s) or ('"id":' in s and '"kind":' in s):
        return None
    if agent_id:
        # Drop sentences that claim to be the assistant when answering as user identity.
        parts = re.split(r"(?<=[.!?])\s+", s)
        kept = []
        for part in parts:
            if re.search(rf"\bI am\s+{re.escape(agent_id)}\b", part, re.I):
                continue
            is_assistant_line = bool(_ASSISTANT_BLEED.search(part))
            is_user_directed = "you are" in part.lower() or "your name" in part.lower()
            if is_assistant_line and not is_user_directed:
                # Keep user-directed lines; drop assistant self-description bleed.
                if not re.search(r"\b(you|your)\b", part, re.I):
                    continue
            kept.append(part)
        s = " ".join(kept).strip()
    return s or None


def _summarize_non_text(value: Any) -> str | None:
    if isinstance(value, dict):
        kind = value.get("kind") or value.get("type")
        if kind:
            return f"Adapted via {kind}."
        return None
    if isinstance(value, (list, tuple)):
        bits = [_summarize_non_text(v) for v in value[:5]]
        bits = [b for b in bits if b]
        return "; ".join(bits) if bits else None
    return str(value).strip() or None


def format_learning_memory(learned: dict[str, Any]) -> tuple[str | None, float, list[Any]]:
    """Cognitive speech for learning — never raw adaptation records."""
    lessons = learned.get("lessons") or []
    adaptations = learned.get("adaptations") or []
    answer = learned.get("answer")
    evidence: list[Any] = []

    if isinstance(answer, str) and answer.strip() and not _DICTISH.match(answer.strip()):
        text = answer.strip()
        conf = 0.75 if adaptations or lessons else 0.5
        evidence = list(adaptations or lessons)
        return text, conf, evidence

    lesson_lines: list[str] = []
    for item in lessons[:5]:
        if isinstance(item, str) and item.strip() and not _DICTISH.match(item):
            lesson_lines.append(item.strip())
        elif isinstance(item, dict):
            summary = item.get("summary") or item.get("lesson") or item.get("kind")
            if summary and isinstance(summary, str):
                lesson_lines.append(summary.strip())
            evidence.append({"kind": item.get("kind"), "id": item.get("id")})

    adapt_kinds: list[str] = []
    for item in adaptations[:8]:
        if isinstance(item, dict):
            evidence.append({"kind": item.get("kind"), "id": item.get("id")})
            k = item.get("kind")
            if k and str(k) not in adapt_kinds:
                adapt_kinds.append(str(k))
        elif isinstance(item, str) and item.strip():
            lesson_lines.append(item.strip())

    if lesson_lines:
        return "; ".join(lesson_lines), 0.75, evidence
    if adapt_kinds:
        return (
            "My understanding has adapted through: " + ", ".join(adapt_kinds) + ".",
            0.7,
            evidence,
        )
    if adaptations or lessons:
        return "I have recorded learning adaptations, but no clear lesson text yet.", 0.45, evidence
    return None, 0.0, []


class CognitiveOrganHandlers:
    """Registry of organ handlers — each returns OrganContribution only."""

    def __init__(self, engine: CognitiveEngine) -> None:
        self.engine = engine

    def invoke(
        self,
        organ: str,
        request: str,
        *,
        intent: CognitiveIntent,
        as_primary: bool = True,
    ) -> OrganContribution:
        if organ in FORBIDDEN_TERMINALS:
            raise RuntimeError(f"Forbidden cognitive terminal: {organ}")
        if organ == ORGAN_IDENTITY:
            return self._identity(request, intent=intent)
        if organ == ORGAN_LEARNING:
            return self._learning(request)
        if organ == ORGAN_CONFIDENCE:
            return self._confidence(request)
        if organ == ORGAN_REFLECTION:
            return self._reflection(request)
        if organ == ORGAN_RECONCILIATION:
            return self._reconciliation(request)
        if organ == ORGAN_ASSOCIATIONS:
            return self._associations(request)
        if organ == ORGAN_GOALS:
            return self._goals(request)
        if organ == ORGAN_PREDICTION:
            return self._prediction(request)
        if organ in (ORGAN_WORKING, ORGAN_CONTEXT):
            return self._working_context(request, organ=organ)
        if organ == ORGAN_CONCEPTS:
            return self._remember(request, organ=ORGAN_CONCEPTS, label="concepts")
        if organ == ORGAN_EXPERIENCES:
            return self._remember(request, organ=ORGAN_EXPERIENCES, label="experiences")
        # Default remembering
        return self._remember(request, organ=ORGAN_REMEMBERING, label="remembering")

    def _identity(self, request: str, *, intent: CognitiveIntent) -> OrganContribution:
        if intent == CognitiveIntent.USER_IDENTITY:
            return self._user_identity(request)
        return self._assistant_identity(request)

    def _assistant_identity(self, request: str) -> OrganContribution:
        """Assistant Identity path — operational/agent schema only; never user."""
        from acm.identity.rendering import (
            IdentityRenderTarget,
            is_relationship_identity_request,
            isolate_identity_text,
        )

        steps = ["identity.assistant_schema", "identity.operational", "identity.render_isolate"]
        if is_relationship_identity_request(request):
            steps.append("identity.relationship_allowed")
        who = self.engine.identity.render_assistant_identity()
        answer = who.get("answer") if isinstance(who.get("answer"), str) else None
        text = sanitize_cognitive_text(answer)
        if text and not is_relationship_identity_request(request):
            user = self.engine.identity.schema_concept("user")
            forbidden = {
                a.value
                for a in user.attributes
                if a.active and a.key in ("name", "preferred_name", "location")
            }
            text = isolate_identity_text(
                text,
                target=IdentityRenderTarget.ASSISTANT,
                forbidden_values=forbidden,
            )
        conf = float(who.get("confidence") or 0.0)
        return OrganContribution(
            organ=ORGAN_IDENTITY,
            memory=text,
            confidence=conf if text else 0.0,
            explanation_class=str(who.get("explanation_class") or "experience"),
            ambiguous=False,
            cue_matched=bool(text),
            concepts=[{"id": self.engine.identity.schema_concept("agent").id}],
            reconstruction_steps=steps,
            substrate_touched=("cognitive_store",),
        )

    def _user_identity(self, request: str) -> OrganContribution:
        from acm.identity.rendering import (
            IdentityRenderTarget,
            is_relationship_identity_request,
            isolate_identity_text,
        )

        engine = self.engine
        steps = ["identity.user_schema", "identity.render_isolate"]
        who = engine.identity.render_user_identity()
        text = who.get("answer") if isinstance(who.get("answer"), str) else None
        text = sanitize_cognitive_text(text, agent_id=str(engine.agent_id or ""))
        if text and not is_relationship_identity_request(request):
            agent = engine.identity.schema_concept("agent")
            forbidden = {a.value for a in agent.attributes if a.active and a.key == "name"}
            if engine.agent_id:
                forbidden.add(str(engine.agent_id))
            text = isolate_identity_text(
                text,
                target=IdentityRenderTarget.USER,
                forbidden_values=forbidden,
            )
        if text:
            steps.append("identity.structured_attributes")
            conf = float(who.get("confidence") or 0.0)
        else:
            steps.append("identity.user_insufficient")
            conf = 0.0

        user = engine.identity.schema_concept("user")
        return OrganContribution(
            organ=ORGAN_IDENTITY,
            memory=text,
            confidence=conf if text else 0.0,
            explanation_class="experience" if text else "unknown",
            ambiguous=False,
            cue_matched=bool(text),
            concepts=[{"id": user.id}],
            reconstruction_steps=steps,
            substrate_touched=("cognitive_store",),
        )

    def _learning(self, request: str) -> OrganContribution:
        learned = self.engine.learn(cue=request)
        text, conf, evidence = format_learning_memory(learned if isinstance(learned, dict) else {})
        return OrganContribution(
            organ=ORGAN_LEARNING,
            memory=text,
            confidence=conf,
            explanation_class="experience" if text else "unknown",
            cue_matched=bool(text),
            learning=evidence,
            reconstruction_steps=["learning.learn", "learning.format_cognitive"],
            substrate_touched=("cognitive_store",),
        )

    def _confidence(self, request: str) -> OrganContribution:
        certain = self.engine.how_certain_am_i(request)
        text = sanitize_cognitive_text(
            certain.get("answer") if isinstance(certain.get("answer"), str) else None
        )
        return OrganContribution(
            organ=ORGAN_CONFIDENCE,
            memory=text,
            confidence=float(certain.get("overall_confidence") or 0.0),
            explanation_class="experience",
            cue_matched=True,
            reconstruction_steps=["confidence.how_certain_am_i"],
            substrate_touched=("cognitive_store",),
        )

    def _reflection(self, request: str) -> OrganContribution:
        from acm.reflection.explain import explain_reflection

        thought = self.engine.what_do_i_think(request)
        explanation = explain_reflection(thought if isinstance(thought, dict) else {})
        raw_answer = thought.get("summary") or thought.get("answer") or explanation
        text = sanitize_cognitive_text(
            explanation if explanation else (raw_answer if isinstance(raw_answer, str) else None)
        )
        return OrganContribution(
            organ=ORGAN_REFLECTION,
            memory=text,
            confidence=float(thought.get("confidence") or 0.5),
            explanation_class=(
                "unknown" if thought.get("insufficient_evidence") else "experience"
            ),
            ambiguous=bool(thought.get("hypotheses")),
            cue_matched=not bool(thought.get("insufficient_evidence")),
            reflective=list(thought.get("outcomes") or []),
            reconstruction_steps=["reflection.what_do_i_think", "reflection.explain"],
            substrate_touched=("cognitive_store",),
        )

    def _reconciliation(self, request: str) -> OrganContribution:
        recon = self.engine.how_should_memory_reconcile(request)
        text = sanitize_cognitive_text(
            recon.get("answer") if isinstance(recon.get("answer"), str) else None
        )
        return OrganContribution(
            organ=ORGAN_RECONCILIATION,
            memory=text,
            confidence=float((recon.get("reconciliation") or {}).get("confidence") or 0.4),
            explanation_class="contested",
            ambiguous=True,
            cue_matched=True,
            reconstruction_steps=["reconciliation.how_should_memory_reconcile"],
            substrate_touched=("cognitive_store",),
        )

    def _associations(self, request: str) -> OrganContribution:
        from acm.authority.routing import _extract_relation_pair

        left, right = _extract_relation_pair(request)
        steps = ["associations.how_related"]
        if left and right:
            related = self.engine.how_related(left, right)
            answer = related.get("answer") or related.get("summary")
            text = sanitize_cognitive_text(answer if isinstance(answer, str) else None)
            return OrganContribution(
                organ=ORGAN_ASSOCIATIONS,
                memory=text,
                confidence=float(related.get("confidence") or 0.5),
                explanation_class="experience" if text else "unknown",
                cue_matched=bool(text),
                associations=list(related.get("associations") or [])[:8]
                if isinstance(related.get("associations"), list)
                else [],
                reconstruction_steps=steps,
                substrate_touched=("cognitive_store",),
            )
        return self._remember(request, organ=ORGAN_ASSOCIATIONS, label="associations_fallback")

    def _goals(self, request: str) -> OrganContribution:
        goals = list(self.engine.store.active_goals())
        steps = ["goals.active_goals"]
        if goals:
            titles = [g.title for g in goals[:8]]
            text = "Active goals: " + "; ".join(titles) + "."
            return OrganContribution(
                organ=ORGAN_GOALS,
                memory=text,
                confidence=0.85,
                explanation_class="experience",
                cue_matched=True,
                reconstruction_steps=steps,
                substrate_touched=("cognitive_store",),
            )
        # Empty goals: contribution is empty; dispatch invokes supporting organs.
        return OrganContribution(
            organ=ORGAN_GOALS,
            memory=None,
            confidence=0.0,
            explanation_class="unknown",
            cue_matched=False,
            reconstruction_steps=steps + ["goals.empty"],
            substrate_touched=("cognitive_store",),
        )

    def _prediction(self, request: str) -> OrganContribution:
        result = self.engine.what_is_likely(request)
        answer = (result.get("answer") or "").strip()
        outcomes = list(result.get("outcomes") or [])
        experiences: list[dict[str, Any]] = []
        seen: set[str] = set()
        for outcome in outcomes[:6]:
            for sid in list(outcome.get("support") or [])[:4]:
                if sid in seen:
                    continue
                exp = self.engine.store.experiences.get(sid)
                if exp is not None:
                    seen.add(sid)
                    experiences.append({"id": exp.id, "summary": exp.summary})
                    continue
                assoc = self.engine.store.associations.get(sid)
                if assoc is None:
                    continue
                for eid in list(getattr(assoc, "evidence_ids", []) or [])[:3]:
                    if eid in seen:
                        continue
                    exp = self.engine.store.experiences.get(eid)
                    if exp is None:
                        continue
                    seen.add(eid)
                    experiences.append({"id": exp.id, "summary": exp.summary})
        conf = float(result.get("confidence") or 0.0)
        ambiguous = bool(result.get("ambiguous"))
        if not outcomes or not answer or answer.lower().startswith(
            "memory does not yet support"
        ):
            return OrganContribution(
                organ=ORGAN_PREDICTION,
                memory=None,
                confidence=0.0,
                explanation_class="unknown",
                cue_matched=False,
                ambiguous=False,
                reconstruction_steps=["prediction.what_is_likely", "prediction.insufficient"],
                substrate_touched=("cognitive_store",),
            )
        expl = "contested" if ambiguous else "experience"
        return OrganContribution(
            organ=ORGAN_PREDICTION,
            memory=answer,
            confidence=conf,
            explanation_class=expl,
            ambiguous=ambiguous,
            cue_matched=True,
            concepts=[{"id": cid} for cid in (result.get("source_concept_ids") or [])[:8]],
            experiences=experiences[:8],
            reconstruction_steps=["prediction.what_is_likely"],
            substrate_touched=("cognitive_store",),
        )

    def _working_context(self, request: str, *, organ: str) -> OrganContribution:
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
        text = " ".join(parts) if parts else None
        return OrganContribution(
            organ=organ,
            memory=text,
            confidence=0.7 if text else 0.0,
            explanation_class="experience" if text else "unknown",
            cue_matched=bool(text),
            reconstruction_steps=[f"{organ}.context_frame"],
            substrate_touched=("context_frame",),
        )

    def _remember(
        self,
        request: str,
        *,
        organ: str = ORGAN_REMEMBERING,
        label: str = "remembering",
    ) -> OrganContribution:
        engine = self.engine
        remembered = engine.remember(request)
        recon = remembered.reconstruction or {}
        memory_text = sanitize_cognitive_text(
            (remembered.answer or "").strip(),
            agent_id="",  # remembering may legitimately discuss assistant for other intents
        )
        cue = request.lower()
        cue_tokens = [t for t in cue.split() if len(t) > 2]
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
        competing = list(recon.get("competing") or [])
        # B04: when reconstruction is ambiguous, speak names semantic competitors
        # instead of silently presenting only the leading candidate.
        if remembered.ambiguous and competing:
            previews: list[str] = []
            for item in competing[:4]:
                if isinstance(item, dict):
                    bit = str(
                        item.get("answer_preview")
                        or item.get("label")
                        or ""
                    ).strip()
                else:
                    bit = str(item).strip()
                if bit and bit not in previews:
                    previews.append(bit)
            if memory_text and memory_text not in previews:
                previews.insert(0, memory_text)
            if len(previews) >= 2:
                joined = " and ".join(previews[:3])
                memory_text = (
                    f"Remembered evidence conflicts: {joined}. "
                    f"Confidence is reduced ({int(round(float(remembered.confidence) * 100))}%)."
                )
            elif previews:
                memory_text = (
                    f"Remembered evidence conflicts around {previews[0]}. "
                    f"Confidence is reduced ({int(round(float(remembered.confidence) * 100))}%)."
                )
        return OrganContribution(
            organ=organ,
            memory=memory_text,
            confidence=float(remembered.confidence),
            explanation_class=remembered.explanation_class.value,
            ambiguous=bool(remembered.ambiguous),
            cue_matched=cue_matched,
            concepts=concepts,
            experiences=experiences,
            associations=associations,
            reconstruction_steps=[f"{label}.remember"],
            substrate_touched=("cognitive_store",),
        )

    def project_support(self) -> OrganContribution:
        engine = self.engine
        engine.identity.ensure_schemas()
        project = engine.identity.schema_concept("project")
        attrs = [a for a in project.attributes if a.active]
        if not attrs and not project.labels:
            return OrganContribution(
                organ=ORGAN_IDENTITY,
                memory=None,
                confidence=0.0,
                reconstruction_steps=["identity.project_schema_empty"],
                substrate_touched=("cognitive_store",),
            )
        bits = [f"{a.key}: {a.value}" for a in attrs[:6]]
        label = project.labels[0] if project.labels else "project"
        text = f"Project ({label}): " + "; ".join(bits) if bits else f"Tracked project: {label}."
        return OrganContribution(
            organ=ORGAN_IDENTITY,
            memory=text,
            confidence=float(project.confidence or 0.5),
            explanation_class="experience",
            cue_matched=True,
            concepts=[{"id": project.id}],
            reconstruction_steps=["identity.project_schema"],
            substrate_touched=("cognitive_store",),
        )
