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
    r"\bsearch\s+(?:my\s+)?memory\b|\brecall\b|\bwhat\s+do\s+you\s+remember\b|"
    r"\bwhat\s+do\s+you\s+know\s+about\s+me\b|"
    r"\b(?:please\s+)?(?:remember|don'?t\s+forget|note\s+that|keep\s+in\s+mind)\b|"
    r"\b(?:please\s+)?(?:forget|delete\s+memory|remove\s+memory)\b|"
    r"\b(?:please\s+)?(?:update|change|correct|fix)\s+my\b|"
    # Memory explanation / lineage (must not fall through to Mission Control)
    r"\bwhy\b.+\b(?:favorite|favourite)\b|"
    r"\bwhy\b.+\b(?:isn'?t|is\s+not|no\s+longer)\b.+\bactive\b|"
    r"\bwhy\b.+\bactive\b|"
    r"\bwhat\s+replaced\b|"
    r"\b(?:retired|superseded|replaced)\b",
    re.I,
)

# Imperative write — "remember that …" but not "what do you remember" / "do you remember …?"
_MEMORY_WRITE = re.compile(
    r"\b(?:please\s+)?(?:remember|don'?t\s+forget|note\s+that|keep\s+in\s+mind)\b",
    re.I,
)
_MEMORY_WRITE_QUESTION = re.compile(
    r"\b(?:what\s+do\s+you\s+remember|do\s+you\s+remember|did\s+you\s+remember)\b",
    re.I,
)
_MEMORY_FORGET = re.compile(
    r"\b(?:please\s+)?(?:forget|delete\s+memory|remove\s+memory)\b",
    re.I,
)
_MEMORY_UPDATE = re.compile(
    r"\b(?:please\s+)?(?:correct|update|fix|change)\s+"
    r"(?:that|the\s+fact|memory|my\s+memory|my)\b|"
    r"^(?:please\s+)?(?:update|change|correct|fix)\s+my\b|"
    r"^(?:please\s+)?actually,?\s+",
    re.I,
)
_MEMORY_SEARCH = re.compile(
    r"\b(?:search\s+my\s+memory|search\s+memory|find\s+in\s+memory|memory\s+search)\b",
    re.I,
)
_MEMORY_SUMMARY = re.compile(
    r"\b(?:"
    r"what\s+do\s+you\s+know\s+about\s+me|tell\s+me\s+something\s+about\s+me|"
    r"tell\s+me\s+about\s+myself|about\s+me\b|who\s+am\s+i\b|"
    r"what\s+do\s+you\s+remember(?:\s+about\s+me)?|"
    r"my\s+memories|something\s+i\s+like|what\s+do\s+i\s+like|"
    r"what\s+preferences?\s+(?:do\s+you\s+)?know|"
    r"preferences?\s+(?:do\s+you\s+know|about\s+me)"
    r")\b",
    re.I,
)
_MEMORY_RECALL_FACT = re.compile(
    r"\bwhat\s+is\s+my\b|\bwhat'?s\s+my\b|\bdo\s+you\s+remember\s+my\b|"
    r"\bwhat\s+do\s+you\s+know\s+about\s+(?!me\b)",
    re.I,
)
_MEMORY_RECALL_RUNTIME = re.compile(
    r"\b(?:gpu|vram|cpu|ram|model|hardware|graphics|card|disk|storage|"
    r"service|platform|mission\s+control|ollama|docker|provider|job)\b",
    re.I,
)
_MEMORY_LIST = re.compile(
    r"\b(?:recall|list\s+(?:my\s+)?memor(?:y|ies)|show\s+(?:my\s+)?memor(?:y|ies))\b",
    re.I,
)


def resolve_memory_route(prompt: str) -> dict[str, Any] | None:
    """Map memory verbs to distinct router actions (write ≠ search ≠ dump).

    Returns a partial intent dict with action/params, or None if not a memory utterance.
    """
    message = (prompt or "").strip()
    if not message:
        return None
    lower = message.lower()

    # Order matters: write before interrogative remember; search before generic recall.
    if _MEMORY_SEARCH.search(lower):
        query = (
            re.sub(
                r"^(please\s+)?(search my memory|search memory|find in memory|memory search)\s*(for\s+)?",
                "",
                message,
                flags=re.I,
            ).strip()
            or message
        )
        return {"action": "memory_search", "params": {"query": query}, "thinking": "memory search"}

    if _MEMORY_FORGET.search(lower):
        query = (
            re.sub(
                r"^(please\s+)?(forget|delete memory|remove memory)\s*(about\s+)?",
                "",
                message,
                flags=re.I,
            ).strip()
            or message
        )
        return {"action": "memory_forget", "params": {"query": query}, "thinking": "forget memory"}

    if _MEMORY_UPDATE.search(lower):
        from jarvis.trust_memory import parse_memory_correct

        parsed = parse_memory_correct(message)
        if parsed:
            hint, new_fact = parsed
            return {
                "action": "memory_correct",
                "params": {"new_fact": new_fact, "search_hint": hint},
                "thinking": "correct memory",
            }
        # Soft update: "Update my favorite coffee" → correct with hint, await new value
        hint = re.sub(
            r"^(please\s+)?(update|change|correct|fix)\s+(my\s+)?",
            "",
            message,
            flags=re.I,
        ).strip()
        return {
            "action": "memory_correct",
            "params": {"new_fact": "", "search_hint": hint or message},
            "thinking": "update memory",
        }

    if _MEMORY_WRITE.search(lower) and not _MEMORY_WRITE_QUESTION.search(lower):
        text = re.sub(
            r"^(please\s+)?(remember|don't forget|don'?t forget|note that|keep in mind)\s*(that\s+)?",
            "",
            message,
            flags=re.I,
        ).strip()
        text = re.sub(r"^(these|the following)\s+facts?\s*:?\s*", "", text, flags=re.I).strip()
        if text:
            return {"action": "remember", "params": {"text": text}, "thinking": "remember"}

    if _MEMORY_SUMMARY.search(lower):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "memory summary",
        }

    # Memory explanation / lineage — full prompt to Memory Authority
    if re.search(
        r"\bwhy\b.+\b(?:favorite|favourite)\b|"
        r"\bwhy\b.+\b(?:isn'?t|is\s+not|no\s+longer)\b.+\bactive\b|"
        r"\bwhy\b.+\bactive\b|"
        r"\bwhat\s+replaced\b",
        lower,
    ):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "memory explanation",
        }

    if _MEMORY_RECALL_FACT.search(lower) and not _MEMORY_RECALL_RUNTIME.search(lower):
        # Targeted fact retrieval — never dump the whole store.
        return {
            "action": "memory_search",
            "params": {"query": message},
            "thinking": "memory recall fact",
        }

    if _MEMORY_LIST.search(lower):
        return {"action": "recall", "params": {}, "thinking": "memory list"}

    if _USER_MEMORY.search(message):
        # Fallback for other memory-ish phrasing matched by structure.
        return {"action": "memory_search", "params": {"query": message}, "thinking": "memory"}

    return None


def _runtime_action(subject: str, verb: str, prompt: str = "") -> str:
    lower = (prompt or "").strip().lower()
    if lower in ("status", "health", "platform health", "mission control status"):
        return "status_summary"
    if re.search(r"\b(full status|runtime report|system report|diagnostics?)\b", lower):
        return "runtime_report"
    blob = f"{subject} {verb} {prompt}".lower()
    if re.search(r"\b(how much )?ram\b|\bsystem memory\b|\bavailable memory\b", blob):
        return "runtime_ram"
    if re.search(r"\b(gpu|vram|cpu|hardware|graphics)\b", blob):
        return "runtime_gpu"
    if re.search(r"\b(disk|storage)\b", blob):
        return "runtime_storage"
    if re.search(r"\bnetwork\b", blob):
        return "runtime_network"
    if re.search(r"\b(model|ollama|litellm)\b", blob):
        return "runtime_models"
    if re.search(r"\b(database|postgres|mongodb|mongo|redis|qdrant)\b", blob):
        return "runtime_databases"
    if re.search(r"\b(service|docker)\b", blob):
        return "runtime_services"
    if re.search(r"\b(job|activity)\b", blob):
        return "runtime_jobs"
    if re.search(r"\b(provider|memory provider|knowledge provider)\b", blob):
        return "runtime_providers"
    if re.search(r"\b(application|app)\b", blob):
        return "runtime_applications"
    if re.search(r"\b(needs attention|attention)\b", blob):
        return "runtime_attention"
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
    # Autobiographical "my" (favorite color, my name, …) must never be forced to
    # Mission Control merely because _LIVE_STATE matches the word "my".
    if intent in ("web_search", "knowledge") and _LIVE_STATE.search(prompt):
        if re.search(
            r"\b(favorite|favourite|prefer|name|remember|memory|retired|replaced|active)\b",
            prompt,
            re.I,
        ):
            return "memory"
        if syntax.verb in ("using", "running", "loaded", "active") or re.search(
            r"\b(gpu|vram|cpu|model|hardware|service|platform|mission\s+control)\b",
            prompt,
            re.I,
        ):
            return "runtime"
    return intent


_EXACT_RUNTIME_COMMANDS: dict[str, str] = {
    "status": "status_summary",
    "health": "runtime_health",
    "services": "runtime_services",
    "databases": "runtime_databases",
    "models": "runtime_models",
    "memory": "runtime_providers",
    "ram": "runtime_ram",
    "providers": "runtime_providers",
    "gpu": "runtime_gpu",
    "jobs": "runtime_jobs",
    "attention": "runtime_attention",
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

    # Distinct memory verbs (write/forget/update/search/summary) never collapse to dump.
    mem = resolve_memory_route(result.prompt)
    if mem:
        intent = "memory"
        action = str(mem["action"])
        params = dict(mem.get("params") or {})

    exact = _EXACT_RUNTIME_COMMANDS.get(result.prompt.strip().lower())
    if exact:
        action = exact
    elif mem:
        pass  # already set from resolve_memory_route
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
        if not mem:
            # Live failure (post-M0J): declarative teachings such as
            # "My favorite color is green." classified as intent=memory with
            # subject="favorite color", then collapsed to memory_search with
            # ONLY the subject — Teaching Recognition never saw the statement,
            # EncodeAuthority never ran, and recall stayed on the prior value.
            # Unresolved memory intents must reach Memory Authority with the
            # FULL prompt. Declaratives go through cognitive_respond (Teaching
            # Recognition → EncodeAuthority). Interrogatives/search keep
            # memory_search but still pass the full prompt, never a fragment.
            if result.grammar.sentence_type == "declarative":
                action = "memory_about_user"
                params = {"question": result.prompt}
            else:
                action = "memory_search"
                params = {"query": result.prompt}
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
        if action == "chat":
            action = "chat"
    else:
        if action == "chat":
            return None

    out = {
        "action": action,
        "params": params,
        "thinking": (mem or {}).get("thinking") or "nlu",
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
