"""Map NLU semantic output to router actions with intent guards."""

from __future__ import annotations

import re
from typing import Any

from jarvis.nlu.confidence import confidence_band
from jarvis.nlu.types import NLUResult

_LIVE_STATE = re.compile(
    r"\b(my|our|current|running|loaded|connected|free|available)\b|"
    r"\b(status|health|services?|providers?|models?|jobs?|applications?)\b|"
    r"\b(am i using|are we using|is .+ running)\b",
    re.I,
)
_ENCYCLOPEDIC = re.compile(
    r"\bwhat\s+is\s+(?:a|an)\b|\bwhat\s+are\s+(?:the\s+)?(?:benefits|advantages)\b|"
    r"\bexplain\b|\bteach\s+me\b|\btell\s+me\s+about\b|"
    r"\bhistory\s+of\b|\bcompare\b",
    re.I,
)
_STATUS = re.compile(
    r"\b(status|health|postgres|redis|mongodb|platform|mission control|ollama)\b",
    re.I,
)
_MY_STATE = re.compile(
    r"\bwhat\s+is\s+my\b|\bmy\s+current\b|\bam\s+i\s+using\b|\bwhich\b.+\b(active|loaded|running)\b",
    re.I,
)
_REF = re.compile(
    r"\b(documentation|docs?|readme|manual|how\s+(?:do|to)\s+(?:i|we)\s+\w+|configure)\b",
    re.I,
)
_EXPLICIT_WEB = re.compile(r"\bsearch\s+(?:the\s+)?web\b|\blook\s+up\s+online\b", re.I)
_USER_MEMORY = re.compile(
    r"\bsearch\s+(?:my\s+)?memory\b|\brecall\b|\bwhat\s+do\s+you\s+remember\b", re.I
)


def _runtime_action(subject: str, verb: str, prompt: str = "") -> str:
    lower = (prompt or "").strip().lower()
    if lower in ("status", "health", "platform health", "mission control status"):
        return "status_summary"
    blob = f"{subject} {verb}".lower()
    if re.search(r"\b(gpu|vram|cpu|ram|hardware|graphics|inference)\b", blob):
        return "runtime_gpu"
    if re.search(r"\b(model|ollama|litellm)\b", blob):
        return "runtime_models"
    if re.search(r"\b(service|redis|postgres|database|mongodb|qdrant|docker)\b", blob):
        if re.search(r"\bis\b.*\brunning\b", blob) or "running" in blob:
            return "runtime_services"
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
    prompt = result.prompt
    syntax = result.syntax
    grammar = result.grammar
    lower = prompt.lower().strip()

    if _USER_MEMORY.search(prompt):
        return "memory"
    if _EXPLICIT_WEB.search(prompt):
        return "web_search"
    if re.search(r"\blearn\s+about\b", lower):
        return "knowledge"
    if re.search(r"\bfix\s+errors?\s+in\b.+\.py", lower):
        return "coding"
    if re.search(r"\bwhat\b.+\bare\s+you\s+using\b", lower):
        return "runtime"
    if _STATUS.search(lower) and not _ENCYCLOPEDIC.search(prompt):
        return "runtime"
    if _MY_STATE.search(lower) and re.search(
        r"\b(gpu|graphics|model|hardware|cpu|vram|card)\b", lower, re.I
    ):
        return "runtime"
    if syntax.subject in ("documentation", "reference") or (
        _REF.search(prompt) and not _LIVE_STATE.search(prompt)
    ):
        if not re.search(r"\bis\b.+\brunning\b", prompt, re.I):
            return "reference"
    if _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if re.search(r"\bis\b.+\brunning\b", prompt, re.I):
        return "runtime"
    if syntax.verb in ("using", "active", "loaded", "running") and syntax.object:
        if re.search(r"\b(gpu|graphics|card|hardware|model|docker|ollama)\b", syntax.object, re.I):
            return "runtime"
    if syntax.verb == "using" and syntax.object:
        return "runtime"
    if grammar.mood == "instruction" and syntax.verb in ("configure", "setup"):
        return "reference"
    if _LIVE_STATE.search(prompt) and grammar.sentence_type == "interrogative":
        if re.search(r"\b(which|what)\b.+\b(using|running|loaded|active)\b", prompt, re.I):
            return "runtime"
    return None


def apply_intent_guards(result: NLUResult) -> str:
    prompt = result.prompt
    intent = result.semantic.intent
    if intent == "documentation":
        intent = "reference"
    structural = infer_intent_from_structure(result)
    if structural and (intent in ("chat", "") or result.semantic.confidence < 0.85):
        intent = structural
    syntax = result.syntax

    if _USER_MEMORY.search(prompt):
        return "memory"
    if _EXPLICIT_WEB.search(prompt):
        return "web_search"
    if (
        _REF.search(prompt)
        or syntax.subject in ("documentation", "reference")
        or syntax.verb in ("configure", "setup", "show")
    ):
        if not _LIVE_STATE.search(prompt) or syntax.subject in ("documentation", "reference"):
            if not re.search(r"\bis\b.+\brunning\b", prompt, re.I):
                return "reference"
    if _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if intent == "runtime" and _ENCYCLOPEDIC.search(prompt) and not _LIVE_STATE.search(prompt):
        return "knowledge"
    if intent == "reference" and re.search(r"\bis\b.+\brunning\b", prompt, re.I):
        return "runtime"
    if intent in ("web_search", "knowledge") and _LIVE_STATE.search(prompt):
        if syntax.verb in ("using", "running", "loaded", "active") or "my" in prompt.lower():
            return "runtime"
    return intent


_EXACT_RUNTIME_COMMANDS: dict[str, str] = {
    "status": "status_summary",
    "health": "runtime_health",
    "services": "runtime_services",
    "models": "runtime_models",
    "memory": "runtime_providers",
    "providers": "runtime_providers",
    "gpu": "runtime_gpu",
    "jobs": "runtime_jobs",
}


def nlu_to_router_intent(result: NLUResult) -> dict[str, Any] | None:
    intent = apply_intent_guards(result)
    subject = result.semantic.subject or result.syntax.object
    verb = result.syntax.verb or result.semantic.action
    confidence = result.semantic.confidence
    band = confidence_band(confidence)

    if confidence < 0.45 and not result.learned_match:
        return None

    params: dict[str, Any] = {}
    action = "chat"

    exact = _EXACT_RUNTIME_COMMANDS.get(result.prompt.strip().lower())
    if exact:
        action = exact
    elif intent == "runtime":
        action = _runtime_action(subject, verb, result.prompt)
    elif intent == "knowledge":
        if re.search(r"\blearn\s+about\b", result.prompt, re.I):
            from jarvis.knowledge import parse_learn_topic

            action = "learn_about"
            params = {"topic": parse_learn_topic(result.prompt)}
        else:
            action = "chat"
            params = {"knowledge_mode": True, "query": result.prompt}
    elif intent == "reference":
        action = "reference_search"
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
        if re.search(r"\bfix\s+errors?\s+in\b", result.prompt, re.I):
            from jarvis.router import py_path_from_message

            action = "coding_fix"
            params = {"path": py_path_from_message(result.prompt)}
        else:
            action = "coding_chat"
            params = {"query": result.prompt}
    elif intent == "chat":
        action = "chat"
    else:
        return None

    out = {
        "action": action,
        "params": params,
        "thinking": "nlu",
        "route_reason": "nlu_semantic",
        "route_confidence": confidence,
        "route_handler": handler_for_intent(intent),
        "nlu": result.to_debug(),
        "semantic_report": result.to_debug(),
        "router": "nlu",
        "router_stage": "nlu_pipeline",
        "rule_matched": intent,
        "confidence_band": band,
        "flag_for_review": band == "review",
    }
    return out


def handler_for_intent(intent: str) -> str:
    if intent == "documentation":
        intent = "reference"
    return {
        "runtime": "RuntimeClient",
        "knowledge": "KnowledgeEngine",
        "reference": "ReferenceEngine",
        "memory": "MemoryStore",
        "web_search": "WebSearch",
        "coding": "EngineeringEngine",
        "chat": "ConversationEngine",
    }.get(intent, "ConversationEngine")


# Backward compat
_handler_for_intent = handler_for_intent
