"""Confidence-aware routing thresholds and clarification."""

from __future__ import annotations

import os
from typing import Any

from jarvis.nlu.types import NLUResult

AUTO_ROUTE = float(os.getenv("JARVIS_NLU_CONFIDENCE_AUTO", "0.95"))
REVIEW_ROUTE = float(os.getenv("JARVIS_NLU_CONFIDENCE_REVIEW", "0.70"))
CLARIFY_BELOW = REVIEW_ROUTE

_CLARIFY_OPTIONS = (
    ("Reference", "reference"),
    ("Runtime", "runtime"),
    ("Knowledge", "knowledge"),
    ("Memory", "memory"),
    ("Search", "web_search"),
    ("Coding", "coding"),
    ("Conversation", "chat"),
)


def confidence_band(confidence: float) -> str:
    if confidence >= AUTO_ROUTE:
        return "auto"
    if confidence >= REVIEW_ROUTE:
        return "review"
    return "clarify"


def needs_clarification(result: NLUResult) -> bool:
    if result.learned_match:
        return False
    from jarvis.nlu.mapping import infer_intent_from_structure, resolve_memory_route

    # Resolved memory verbs are deterministic — do not ask for clarification.
    if resolve_memory_route(result.prompt):
        return False
    if infer_intent_from_structure(result) and (
        result.semantic.confidence >= REVIEW_ROUTE or result.semantic.model == "structure"
    ):
        return False
    if result.semantic.model == "structure":
        return result.semantic.confidence < CLARIFY_BELOW
    return result.semantic.confidence < CLARIFY_BELOW


def build_clarification_intent(result: NLUResult) -> dict[str, Any]:
    subject = result.syntax.object or result.prompt.strip()
    choices = [label for label, _ in _CLARIFY_OPTIONS]
    return {
        "action": "nlu_clarify",
        "params": {
            "original_prompt": result.prompt,
            "subject": subject,
            "nlu": result.to_debug(),
        },
        "needs_clarification": True,
        "clarification_question": (
            f'I\'m not fully confident how to handle "{subject or result.prompt}". '
            "What did you mean?"
        ),
        "choices": choices,
        "clarification_options": dict(_CLARIFY_OPTIONS),
        "thinking": "nlu_clarify",
        "route_reason": "low_confidence",
        "route_confidence": result.semantic.confidence,
        "route_handler": "NLU",
        "router": "nlu",
        "router_stage": "clarification_required",
        "nlu": result.to_debug(),
    }


def resolve_clarification_choice(choice: str, pending: dict[str, Any]) -> dict[str, Any] | None:
    from jarvis.nlu.types import (
        GrammarAnalysis,
        MorphologyAnalysis,
        NLUResult,
        SemanticClassification,
        SyntaxAnalysis,
    )

    options = pending.get("clarification_options") or dict(_CLARIFY_OPTIONS)
    key = (choice or "").strip().lower()
    intent = None
    for label, value in options.items():
        if key == label.lower() or key == value:
            intent = value
            break
    if not intent and key.isdigit():
        idx = int(key) - 1
        labels = list(options.keys())
        if 0 <= idx < len(labels):
            intent = options[labels[idx]]
    if not intent:
        return None
    from jarvis.nlu.mapping import _runtime_action, handler_for_intent

    prompt = pending.get("original_prompt") or ""
    syntax = SyntaxAnalysis(object=pending.get("subject") or "")
    result = NLUResult(
        prompt=prompt,
        grammar=GrammarAnalysis(),
        morphology=MorphologyAnalysis(),
        syntax=syntax,
        semantic=SemanticClassification(intent=intent, confidence=1.0, model="clarification"),
        learned_match=True,
    )
    params: dict[str, Any] = {}
    action = "chat"
    if intent == "runtime":
        action = _runtime_action(syntax.object, "", prompt)
    elif intent == "reference":
        action = "reference_search"
        params = {"query": prompt, "subject": syntax.object}
    elif intent == "knowledge":
        action = "chat"
        params = {"knowledge_mode": True, "query": prompt}
    elif intent == "memory":
        from jarvis.nlu.grammar import analyze_grammar
        from jarvis.nlu.mapping import resolve_memory_route

        mem = resolve_memory_route(prompt)
        if mem:
            action = str(mem["action"])
            params = dict(mem.get("params") or {})
        elif analyze_grammar(prompt).sentence_type == "declarative":
            # Same contract as nlu_to_router_intent: full prompt → Memory Authority
            action = "memory_about_user"
            params = {"question": prompt}
        else:
            action = "memory_search"
            params = {"query": prompt}
    elif intent == "web_search":
        action = "web_search"
        params = {"query": prompt}
    elif intent == "coding":
        action = "coding_chat"
        params = {"query": prompt}
    return {
        "action": action,
        "params": params,
        "thinking": "clarification_accepted",
        "route_reason": "clarification_accepted",
        "route_confidence": 1.0,
        "route_handler": handler_for_intent(intent),
        "clarification_accepted": True,
        "final_intent": intent,
        "nlu": result.to_debug(),
    }
