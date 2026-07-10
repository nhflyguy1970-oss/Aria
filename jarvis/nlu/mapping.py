"""Map NLU semantic output to router actions with intent guards."""

from __future__ import annotations

import re
from typing import Any

from jarvis.nlu.types import NLUResult

_LIVE_STATE = re.compile(
    r"\b(my|our|current|running|loaded|connected|free|available)\b|"
    r"\b(status|health|services?|providers?|models?|jobs?|applications?)\b|"
    r"\b(am i using|are we using)\b",
    re.I,
)
_ENCYCLOPEDIC = re.compile(
    r"\bwhat\s+is\s+(?:a|an)\b|\bexplain\b|\bteach\s+me\b|\bhistory\s+of\b|\bcompare\b",
    re.I,
)
_DOCS = re.compile(
    r"\b(documentation|docs?|readme|manual|how\s+(?:do|to)\s+(?:i|we)\s+\w+)\b",
    re.I,
)
_EXPLICIT_WEB = re.compile(r"\bsearch\s+(?:the\s+)?web\b|\blook\s+up\s+online\b", re.I)
_USER_MEMORY = re.compile(
    r"\bsearch\s+(?:my\s+)?memory\b|\brecall\b|\bwhat\s+do\s+you\s+remember\b", re.I
)


def _runtime_action(subject: str, verb: str) -> str:
    blob = f"{subject} {verb}".lower()
    if re.search(r"\b(gpu|vram|cpu|ram|hardware)\b", blob):
        return "runtime_gpu"
    if re.search(r"\b(model|ollama|litellm)\b", blob):
        return "runtime_models"
    if re.search(r"\b(service|redis|postgres|database|mongodb|qdrant)\b", blob):
        return "runtime_services"
    if re.search(r"\b(job|activity)\b", blob):
        return "runtime_jobs"
    if re.search(r"\b(provider|memory provider|knowledge provider)\b", blob):
        return "runtime_providers"
    if re.search(r"\b(application|app)\b", blob):
        return "runtime_applications"
    if re.search(r"\b(platform|mission control|runtime)\b", blob):
        return "runtime_platform"
    return "runtime_status"


def infer_intent_from_structure(result: NLUResult) -> str | None:
    """Structural intent when classifier unavailable — grammar/syntax only."""
    prompt = result.prompt
    syntax = result.syntax
    grammar = result.grammar

    if _USER_MEMORY.search(prompt):
        return "memory"
    if _EXPLICIT_WEB.search(prompt):
        return "web_search"
    if syntax.subject == "documentation" or (
        _DOCS.search(prompt) and not _LIVE_STATE.search(prompt)
    ):
        return "documentation"
    if _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if syntax.verb == "using" and syntax.object and _LIVE_STATE.search(prompt):
        return "runtime"
    if grammar.mood == "instruction" and syntax.verb in ("configure", "setup"):
        return "documentation"
    if _LIVE_STATE.search(prompt) and grammar.sentence_type == "interrogative":
        return "runtime"
    return None


def apply_intent_guards(result: NLUResult) -> str:
    """Return corrected intent after structural guards."""
    prompt = result.prompt
    intent = result.semantic.intent
    syntax = result.syntax

    if _USER_MEMORY.search(prompt):
        return "memory"
    if _EXPLICIT_WEB.search(prompt):
        return "web_search"
    if (
        _DOCS.search(prompt)
        or syntax.subject == "documentation"
        or syntax.verb in ("configure", "setup")
    ):
        if not _LIVE_STATE.search(prompt):
            return "documentation"
    if _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if intent == "runtime" and _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if intent == "documentation" and _LIVE_STATE.search(prompt):
        return "runtime"
    if intent in ("web_search", "knowledge") and _LIVE_STATE.search(prompt):
        if syntax.verb in ("using", "running", "loaded") or "my" in prompt.lower():
            return "runtime"
    return intent


def nlu_to_router_intent(result: NLUResult) -> dict[str, Any] | None:
    intent = apply_intent_guards(result)
    subject = result.semantic.subject or result.syntax.object
    verb = result.syntax.verb or result.semantic.action
    confidence = result.semantic.confidence

    if confidence < 0.45 and not result.learned_match:
        return None

    params: dict[str, Any] = {}
    action = "chat"

    if intent == "runtime":
        action = _runtime_action(subject, verb)
    elif intent == "knowledge":
        if re.search(r"\blearn\s+about\b", result.prompt, re.I):
            from jarvis.knowledge import parse_learn_topic

            action = "learn_about"
            params = {"topic": parse_learn_topic(result.prompt)}
        else:
            action = "chat"
            params = {"knowledge_mode": True, "query": result.prompt}
    elif intent == "documentation":
        action = "documentation_search"
        params = {"query": subject or result.prompt, "subject": subject}
    elif intent == "memory":
        if result.syntax.subject == "memory" or "search" in result.prompt.lower():
            action = "memory_search"
            params = {"query": subject or result.prompt}
        else:
            action = "recall"
    elif intent == "web_search":
        action = "web_search"
        params = {"query": subject or result.prompt}
    elif intent == "coding":
        action = "coding_chat"
        params = {"query": result.prompt}
    elif intent == "chat":
        action = "chat"
    else:
        return None

    return {
        "action": action,
        "params": params,
        "thinking": "nlu",
        "route_reason": "nlu_semantic",
        "route_confidence": confidence,
        "route_handler": _handler_for_intent(intent),
        "nlu": result.to_debug(),
        "router": "nlu",
        "router_stage": "nlu_pipeline",
        "rule_matched": intent,
    }


def _handler_for_intent(intent: str) -> str:
    return {
        "runtime": "RuntimeClient",
        "knowledge": "KnowledgeEngine",
        "documentation": "DocumentationEngine",
        "memory": "MemoryStore",
        "web_search": "WebSearch",
        "coding": "EngineeringEngine",
        "chat": "ConversationEngine",
    }.get(intent, "ConversationEngine")
