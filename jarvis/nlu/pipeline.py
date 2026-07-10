"""NLU pipeline — context → grammar → morphology → syntax → classifier → router intent."""

from __future__ import annotations

import os
from typing import Any

from jarvis.nlu.confidence import build_clarification_intent, needs_clarification
from jarvis.nlu.grammar import analyze_grammar
from jarvis.nlu.learning import lookup_learned_intent
from jarvis.nlu.mapping import nlu_to_router_intent
from jarvis.nlu.morphology import analyze_morphology
from jarvis.nlu.semantic import classify_semantic
from jarvis.nlu.syntax import analyze_syntax
from jarvis.nlu.types import NLUResult, SemanticClassification
from jarvis.session import SessionContext


def nlu_enabled() -> bool:
    return os.getenv("JARVIS_NLU_ROUTING", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _keyword_hint(message: str) -> str:
    from jarvis.runtime_routing import is_runtime_routing_question

    hints: list[str] = []
    if is_runtime_routing_question(message):
        hints.append("possible_runtime_state")
    lower = message.lower()
    if "documentation" in lower or "docs" in lower or "readme" in lower or "how do i" in lower:
        hints.append("possible_reference")
    if "search my memory" in lower:
        hints.append("possible_memory")
    if "search the web" in lower:
        hints.append("possible_web_search")
    if "explain" in lower or "what is a" in lower or "tell me about" in lower:
        hints.append("possible_knowledge")
    return ", ".join(hints)


def analyze_prompt(message: str, session: SessionContext) -> NLUResult:
    context = session.context_summary() if session else ""
    grammar = analyze_grammar(message)
    morphology = analyze_morphology(message)
    syntax = analyze_syntax(message, grammar)
    keyword_hint = _keyword_hint(message)

    learned = lookup_learned_intent(message)
    if learned:
        if learned == "documentation":
            learned = "reference"
        semantic = SemanticClassification(
            intent=learned,
            action="",
            subject=syntax.object,
            confidence=0.99,
            model="learned",
            device="local",
            latency_ms=0.0,
        )
        return NLUResult(
            prompt=message,
            grammar=grammar,
            morphology=morphology,
            syntax=syntax,
            semantic=semantic,
            conversation_context=context,
            learned_match=True,
            keyword_hint=keyword_hint,
        )

    semantic = classify_semantic(
        message,
        grammar=grammar,
        morphology=morphology,
        syntax=syntax,
        context=context,
        keyword_hint=keyword_hint,
    ) or SemanticClassification(confidence=0.0)

    result = NLUResult(
        prompt=message,
        grammar=grammar,
        morphology=morphology,
        syntax=syntax,
        semantic=semantic,
        conversation_context=context,
        keyword_hint=keyword_hint,
    )
    if semantic.confidence <= 0:
        from jarvis.nlu.mapping import infer_intent_from_structure

        structural = infer_intent_from_structure(result)
        if structural:
            result.semantic.intent = structural
            result.semantic.confidence = 0.78
            result.semantic.model = "structure"
    return result


def route_via_nlu(
    message: str,
    session: SessionContext,
    attachment: dict | None = None,
) -> dict[str, Any] | None:
    if not nlu_enabled():
        return None
    text = (message or "").strip()
    if not text or attachment:
        return None

    result = analyze_prompt(text, session)

    if needs_clarification(result):
        from jarvis.runtime_routing import is_runtime_routing_question

        if is_runtime_routing_question(text):
            return None
        return build_clarification_intent(result)

    intent = nlu_to_router_intent(result)
    if not intent:
        return None

    try:
        from aiplatform.mission_control.intent_registry import record_intent_use

        record_intent_use(
            intent=result.semantic.intent,
            prompt=text,
            handler=intent.get("route_handler", ""),
            confidence=result.semantic.confidence,
        )
    except Exception:
        pass

    if intent.get("flag_for_review"):
        try:
            from aiplatform.mission_control.timeline import record_timeline_event

            record_timeline_event(
                "routing_review_flagged",
                application="aria",
                component="nlu",
                category="routing",
                detail=f"{text[:120]} conf={result.semantic.confidence}",
            )
        except Exception:
            pass

    return intent
