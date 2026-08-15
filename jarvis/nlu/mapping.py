"""Map NLU semantic output to router actions with intent guards."""

from __future__ import annotations

import re
from typing import Any

from jarvis.nlu.confidence import confidence_band
from jarvis.nlu.episodic_patterns import (
    is_episodic_memory_query,
    is_episodic_teaching,
    is_live_hardware_question,
    is_past_event_memory_question,
)
from jarvis.nlu.semantic_autobio_patterns import (
    is_semantic_autobio_query,
    is_semantic_autobio_teaching,
)
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
    r"\b(status|postgres|redis|mongodb|platform|mission control|ollama)\b|"
    r"\bhealth\b(?!\s+records?\b)",
    re.I,
)
_MY_STATE = re.compile(
    r"\bwhat\s+is\s+my\b|\bmy\s+current\b|\bam\s+i\s+using\b|\bwhich\b.+\b(active|loaded|running)\b",
    re.I,
)
# Local documentation cues only — bare "how do I …" is NOT local reference_search.
_REF = re.compile(
    r"\b(documentation|docs?|readme|manual|changelog|adr|configure\s+(?:the\s+)?(?:project|repo|aria|jarvis))\b",
    re.I,
)
_EXPLICIT_WEB = re.compile(
    r"\b(?:search\s+(?:the\s+)?web|web\s+search|look\s+up(?:\s+online)?|search\s+up|google)\b",
    re.I,
)
_LOCAL_CORPUS = re.compile(
    r"\b(?:docs?|documentation|readme|manual|adr|changelog|"
    r"this\s+(?:project|repo|codebase)|jarvis|aria|ai[- ]?platform)\b",
    re.I,
)
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
    r"\b(?:retired|superseded|replaced)\b|"
    # Evidence / lineage introspection (must not fall through to memory_search)
    r"\bevidence\b|"
    r"\bhistory\s+behind\s+this\s+memory\b|"
    r"\bwhy\s+this\s+memory\s+changed\b|"
    r"\b(?:yesterday|today|this\s+morning|last\s+week|last\s+tuesday|last\s+friday)\s+i\s+"
    r"(?:bought|cleaned|went|installed|visited|caught|fished)\b|"
    r"\bi\s+(?:bought|cleaned|went|installed|visited|caught|fished)\s+.+\s+"
    r"(?:yesterday|today|this\s+morning|last\s+week|last\s+friday)\b",
    re.I,
)

_CONVERSATION_LANGUAGE_QUERY = re.compile(
    r"\bwhat\s+language\s+(?:have\s+we|are\s+we|did\s+we)\s+(?:been\s+)?"
    r"(?:speaking|using|talking)\b|"
    r"\bwhat\s+language\s+is\s+(?:this|our)\s+conversation\b|"
    r"\bin\s+what\s+language\s+(?:are|have)\s+we\s+(?:been\s+)?"
    r"(?:speaking|talking)\b",
    re.I,
)

# Imperative write — anchored at utterance start (or polite "remember that…").
# Mid-sentence "remember" in questions is recall, not storage (BUG-025).
_MEMORY_WRITE = re.compile(
    r"^(?:(?:hey\s+)?(?:aria|jarvis)[,:\s]+)?(?:please\s+)?"
    r"(?:remember|don'?t\s+forget|note\s+that|keep\s+in\s+mind)\b|"
    r"^(?:(?:could|can|would)\s+you\s+(?:please\s+)?)?"
    r"(?:remember|don'?t\s+forget)\s+that\b|"
    r"^(?:please\s+)?(?:store|save)\s+this\b",
    re.I,
)
# Explicit recall phrasing that contains "remember" (never a storage imperative).
_MEMORY_WRITE_QUESTION = re.compile(
    r"\b(?:"
    r"what\s+do\s+you\s+remember|"
    r"what\s+else\s+(?:do\s+you\s+)?remember|"
    r"anything\s+else\s+(?:relevant\s+)?(?:you\s+know|you\s+remember)|"
    r"do\s+you\s+remember|"
    r"did\s+you\s+remember|"
    r"(?:can|could)\s+you\s+remember\s+(?!that\b)|"
    r"tell\s+me\s+what\s+you\s+remember|"
    r"(?:ask(?:ed)?|told)\s+you\s+to\s+remember|"
    r"i\s+(?:ask(?:ed)?|told)\s+you\s+to\s+remember|"
    r"remind\s+me\s+(?:of|what|about)\b|"
    r"which\s+(?:machine|computer|desktop)\s+(?:did\s+i|i)\s+(?:say|want|prefer)|"
    r"what\s+(?:exact\s+)?(?:\w[\w-]*\s+){0,8}?(?:marker|token|value|fact)\b[\s\S]{0,80}?\bremember|"
    r"what\s+.+\b(?:did\s+i|i)\s+ask\s+you\s+to\s+remember|"
    r"recall\s+only\b"
    r")\b",
    re.I,
)
# Marker / acceptance-token recall — not storage (store uses imperative remember).
_MEMORY_MARKER_RECALL = re.compile(
    r"(?:"
    r"\bwhat\b[\s\S]{0,80}?\bARIA-FINAL-MEMORY\b|"
    r"\bARIA-FINAL-MEMORY\s+marker\b|"
    r"\b(?:unique\s+)?(?:acceptance\s+)?memory\s+marker\b|"
    r"\bmarker\s+i\s+just\s+stored\b|"
    r"\bwhat\s+was\s+the\s+ARIA-FINAL-MEMORY\b"
    r")",
    re.I,
)
# Memory deletion — fact-scoped ("forget that I…", "take X out of memory").
_MEMORY_FORGET = re.compile(
    r"^(?:(?:okay|ok|alright)[, ]+)?(?:please\s+)?"
    r"(?:"
    r"forget\s+that\s+i\b|"
    r"forget\s+what\s+i\b|"
    r"forget\s+(?:my\s+)?(?:preference|fact|memory)\b|"
    r"forget\s+.+\bout\s+of\s+memory\b|"
    r"take\s+.+\bout\s+of\s+memory\b|"
    r"remove\s+(?:that|this|it)\s+from\s+memory\b|"
    r"delete\s+memory\b|"
    r"remove\s+memory\b|"
    r"you\s+can\s+forget\b|"
    r"don'?t\s+remember\s+that\b|"
    r"forget\b"
    r")",
    re.I,
)
# Conversational topic drop ("forget the truck, let's…") — NOT memory_search.
_CONVERSATIONAL_SUBJECT_CHANGE = re.compile(
    r"^(?:(?:okay|ok|alright)[, ]+)?(?:please\s+)?"
    r"forget\s+(?:the\s+|about\s+)?(?!that\s+i\b|what\s+i\b)"
    r"(?P<topic>[a-z][\w\s-]{0,40}?)\s*[,.]?\s*"
    r"(?:let'?s|i\s+want|we\s+(?:should|can)|now\s+let'?s|switch\s+to)\b",
    re.I,
)
_MEMORY_UPDATE = re.compile(
    r"\b(?:please\s+)?(?:correct|update|fix|change)\s+"
    r"(?:that|the\s+fact|memory|my\s+memory|my)\b|"
    r"^(?:please\s+)?(?:update|change|correct|fix)\s+my\b",
    re.I,
)
# Discourse "actually…" is NOT a memory correction by itself.
_MEMORY_UPDATE_DISCOURSE = re.compile(
    r"^(?:please\s+)?actually\s*(?:never\s+mind|wait|hold\s+on|scratch\s+that)\b|"
    r"^(?:please\s+)?actually\s*[,—–-]\s*(?:what|how|why|where|when|who|is|are|can|could|should|do|does)\b",
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
# Assistant identity — Memory Authority (never NLU→chat / LLM).
_ASSISTANT_IDENTITY = re.compile(
    r"^\s*(?:"
    r"who\s+are\s+you\b|"
    r"what(?:'s|\s+is)\s+your\s+name\b|"
    r"what\s+are\s+you\s+called\b|"
    r"tell\s+me\s+your\s+name\b|"
    r"what\s+is\s+your\s+identity\b"
    r")\s*[?.!]?\s*$",
    re.I,
)
_MEMORY_RECALL_FACT = re.compile(
    r"\bwhat\s+is\s+my\b|\bwhat'?s\s+my\b|\bdo\s+you\s+remember\s+my\b|"
    r"\bwhat\s+do\s+you\s+know\s+about\s+(?!me\b)|"
    r"\bwhat\s+kind\s+of\s+.+\s+do\s+i\s+prefer\b|"
    r"\bremind\s+me\s+(?:what|of|about)\b|"
    r"\bwhat\s+(?:computer|machine|workstation|project)\s+(?:was\s+i|did\s+i|am\s+i)\b|"
    r"\bwhat\s+(?:gpu|graphics\s+card)\s+(?:was\s+i|did\s+i)\b|"
    r"\bwhat\s+was\s+the\s+name\s+of\s+my\b|"
    r"\bwhat\s+(?!gpu\b|cpu\b|ram\b|vram\b|disk\b)\w[\w\s-]{0,40}?\s+do\s+i\s+have\b",
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
# Evidence / lineage — Memory Authority speak path (never memory_search).
_MEMORY_EVIDENCE = re.compile(
    r"\b("
    r"(?:show|tell|give|list)\s+(?:me\s+)?(?:the\s+)?(?:my\s+)?(?:memory\s+)?evidence|"
    r"what(?:'s|\s+is)\s+(?:the\s+)?evidence|"
    r"what\s+evidence\b|"
    r"supporting\s+evidence|"
    r"evidence\s+for|"
    r"show\s+(?:the\s+)?history\s+behind\s+this\s+memory|"
    r"show\s+why\s+this\s+memory\s+changed"
    r")\b",
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

    # Conversation-language introspection is owned by the language subsystem —
    # never Memory Authority / preference reconstruction.
    if _CONVERSATION_LANGUAGE_QUERY.search(message):
        return None

    # Subject change ("Okay, forget the truck. Let's work on…") — chat, not memory (RW-009).
    if _CONVERSATIONAL_SUBJECT_CHANGE.search(message):
        return None

    # Fact forget must beat teaching detection ("Forget that I prefer…") — RW-011.
    if _MEMORY_FORGET.search(lower) and (
        re.search(
            r"\bforget\s+that\s+i\b|\bforget\s+what\s+i\b|\bout\s+of\s+memory\b|"
            r"\bfrom\s+memory\b|\bdelete\s+memory\b|\bremove\s+memory\b|"
            r"\bdon'?t\s+remember\s+that\b|\byou\s+can\s+forget\b|"
            r"\bforget\s+(?:my\s+)?(?:preference|fact)\b",
            lower,
        )
        or (
            re.match(r"^(?:(?:okay|ok|alright)[, ]+)?(?:please\s+)?forget\b", lower)
            and re.search(r"\b(?:that\s+i|what\s+i|preference|prefer)\b", lower)
            and not _CONVERSATIONAL_SUBJECT_CHANGE.search(message)
        )
    ):
        query = re.sub(
            r"^(?:(?:okay|ok|alright)[, ]+)?(?:please\s+)?"
            r"(?:forget|delete memory|remove memory|you can forget|don't remember|don'?t remember)\s*"
            r"(?:that\s+|what\s+|about\s+)?",
            "",
            message,
            flags=re.I,
        ).strip()
        query = re.sub(
            r"^(?:take\s+)|(?:\s+out\s+of\s+memory\.?$)|(?:\s+from\s+memory\.?$)",
            "",
            query,
            flags=re.I,
        ).strip()
        return {
            "action": "memory_forget",
            "params": {"query": query or message},
            "thinking": "forget memory",
        }

    # Assistant identity — ACM Memory Authority (D043/D044), never LLM chat.
    if _ASSISTANT_IDENTITY.search(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "assistant identity",
        }

    # Episodic autobiographical events and temporal recall — Memory Authority only.
    if is_episodic_teaching(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "episodic teaching",
        }
    if is_episodic_memory_query(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "episodic recall",
        }

    # Semantic autobiographical facts / integrated personal knowledge — Memory Authority.
    # Explicit "remember that…" imperatives keep the remember verb (tested write path).
    # Never treat forget/negation as teaching (RW-011).
    if (
        is_semantic_autobio_teaching(message)
        and not _MEMORY_WRITE.search(lower)
        and not re.search(r"\b(?:forget|don'?t\s+remember|remove\s+from\s+memory)\b", lower)
    ):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "semantic autobiographical teaching",
        }
    if is_semantic_autobio_query(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "semantic autobiographical recall",
        }

    # Past-event recall (including "did I tell you…") — Memory Authority, not search/runtime.
    if is_past_event_memory_question(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "past event recall",
        }

    # Live hardware/system questions — defer to Mission Control (no memory route).
    if is_live_hardware_question(message):
        return None

    # Recall that merely contains "remember" / marker cues — never store the question (BUG-025).
    # Imperative "Please remember … ARIA-FINAL-MEMORY-…" must still store (checked first).
    if _MEMORY_WRITE.search(lower) and not (
        _MEMORY_WRITE_QUESTION.search(lower) or _MEMORY_MARKER_RECALL.search(message)
    ):
        text = re.sub(
            r"^(?:(?:hey\s+)?(?:aria|jarvis)[,:\s]+)?(?:please\s+)?"
            r"(?:remember|don't forget|don'?t forget|note that|keep in mind)\s*"
            r"(?:for\s+later\s*)?(?:that\s+|this\s+|the\s+following\s*)?:?\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        text = re.sub(
            r"^(?:(?:could|can|would)\s+you\s+(?:please\s+)?)?"
            r"(?:remember|don'?t forget)\s+that\s+",
            "",
            text,
            flags=re.I,
        ).strip()
        text = re.sub(
            r"^(?:please\s+)?(?:store|save)\s+this\s*(?:fact\s*)?:?\s*",
            "",
            text,
            flags=re.I,
        ).strip()
        text = re.sub(r"^(these|the following)\s+facts?\s*:?\s*", "", text, flags=re.I).strip()
        text = re.sub(r"^(exactly|literally)\s*:\s*", "", text, flags=re.I).strip()
        # Normalize with parse_remember so confirmational/QA tails never ride in params (BUG-008).
        try:
            from jarvis.modules.memory_common import parse_remember

            text, _etype, _ns = parse_remember(f"remember {text}")
        except Exception:
            pass
        if text:
            return {"action": "remember", "params": {"text": text}, "thinking": "remember"}

    if _MEMORY_WRITE_QUESTION.search(lower) or _MEMORY_MARKER_RECALL.search(message):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "memory recall remember",
        }

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

    if _MEMORY_UPDATE_DISCOURSE.search(message):
        return None
    if _MEMORY_UPDATE.search(lower):
        from jarvis.trust_memory import parse_memory_correct

        # Questions are never memory corrections.
        if "?" in message or re.match(
            r"^(?:please\s+)?actually\s*[,—–-]?\s*(?:what|how|why|where|when|who)\b",
            message,
            re.I,
        ):
            return None
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
        r"\bwhat\s+replaced\b|"
        r"\bhow\s+(?:did|do)\s+you\s+know\b",
        lower,
    ):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "memory explanation",
        }

    # Evidence reconstruction — full original prompt to Memory Authority (never search)
    if _MEMORY_EVIDENCE.search(lower):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "memory evidence",
        }

    if _MEMORY_RECALL_FACT.search(lower) and not _MEMORY_RECALL_RUNTIME.search(lower):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
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

    if is_episodic_teaching(prompt) or is_episodic_memory_query(prompt):
        return "memory"
    if is_past_event_memory_question(prompt):
        return "memory"
    if is_live_hardware_question(prompt):
        return "runtime"
    if re.search(
        r"\b(?:help me plan|help us plan|plan (?:a|an|the|my|our)\b|make (?:a|an) plan\b|"
        r"create (?:a|an) plan\b|plan my (?:day|week))\b",
        lower,
    ):
        return "planning"
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
    # Writing ("status update" / project note) must not become Mission Control (RW-010).
    try:
        from jarvis.runtime_routing import is_writing_request

        if is_writing_request(prompt):
            return "chat"
    except Exception:
        pass
    if _STATUS.search(lower) and not _ENCYCLOPEDIC.search(prompt):
        try:
            from jarvis.runtime_routing import is_writing_request as _is_write

            if _is_write(prompt):
                return "chat"
        except Exception:
            pass
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
    # Instruction mood alone must not become local docs — require a corpus cue.
    if (
        grammar.mood == "instruction"
        and syntax.verb in ("configure", "setup")
        and _LOCAL_CORPUS.search(prompt)
    ):
        return "reference"
    if _LIVE_STATE.search(prompt) and grammar.sentence_type == "interrogative":
        if re.search(r"\b(which|what)\b.+\b(using|running|loaded|active)\b", prompt, re.I):
            return "runtime"
    return None


_CALENDAR_FACT_QUERY = re.compile(
    r"\bwhat\s+day\s+is\s+(?:it|today)\b|"
    r"\bwhat(?:'?s|\s+is)\s+today'?s\s+date\b|"
    r"\bwhat\s+is\s+the\s+(?:date|day)\b|"
    r"\bwhat(?:'?s|\s+is)\s+the\s+date\s+today\b|"
    r"\bday\s+of\s+the\s+week\b",
    re.I,
)


def is_calendar_fact_question(prompt: str) -> bool:
    """Clock/calendar facts are chat — never memory_search or clarification."""
    return bool(_CALENDAR_FACT_QUERY.search(prompt or ""))


# Local forecast via Open-Meteo handler — must not fall through to chat/Ollama.
_WEATHER_FORECAST_QUERY = re.compile(
    r"\b(weather|forecast|temperature|temps?|humidity|rain(?:y|ing)?|snow(?:y|ing)?|"
    r"windy|cloudy|sunny|umbrella|how\s+(?:hot|cold|warm))\b",
    re.I,
)
_WEATHER_FORECAST_CUE = re.compile(
    r"\b(what|how|will|going to|like|expect|tomorrow|today|tonight|this week|next week|"
    r"outside|look like)\b",
    re.I,
)


def is_weather_forecast_question(prompt: str) -> bool:
    """Deterministic weather questions → weather_forecast action (no chat LLM)."""
    text = prompt or ""
    if is_calendar_fact_question(text):
        return False
    return bool(_WEATHER_FORECAST_QUERY.search(text) and _WEATHER_FORECAST_CUE.search(text))


def apply_intent_guards(result: NLUResult) -> str:
    prompt = result.prompt
    intent = result.semantic.intent
    # Calendar / clock facts must never collapse into memory_search.
    if is_calendar_fact_question(prompt):
        return "chat"
    try:
        from jarvis.runtime_routing import is_writing_request

        if is_writing_request(prompt):
            return "chat"
    except Exception:
        pass
    if is_weather_forecast_question(prompt):
        return "weather"
    if is_episodic_teaching(prompt):
        return "memory"
    if is_episodic_memory_query(prompt) or is_past_event_memory_question(prompt):
        return "memory"
    if is_live_hardware_question(prompt):
        return "runtime"
    if re.search(
        r"\b(?:help me plan|help us plan|plan (?:a|an|the|my|our)\b|make (?:a|an) plan\b|"
        r"create (?:a|an) plan\b|plan my (?:day|week))\b",
        prompt,
        re.I,
    ):
        return "planning"
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
    # reference_search only for local corpus / explicit documentation asks.
    if syntax.subject in ("documentation", "reference") or (
        _REF.search(prompt) and _LOCAL_CORPUS.search(prompt)
    ):
        if not _LIVE_STATE.search(prompt) or syntax.subject in ("documentation", "reference"):
            if not re.search(r"\bis\b.+\brunning\b", prompt, re.I):
                return "reference"
    if (
        syntax.verb in ("configure", "setup")
        and _LOCAL_CORPUS.search(prompt)
        and not _LIVE_STATE.search(prompt)
    ):
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
        if is_episodic_teaching(prompt):
            return "memory"
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
    if is_calendar_fact_question(result.prompt or ""):
        confidence = max(confidence, 0.95)
    if is_weather_forecast_question(result.prompt or ""):
        confidence = max(confidence, 0.95)
    band = confidence_band(confidence)

    if confidence < 0.45 and not result.learned_match:
        return None

    params: dict[str, Any] = {}
    action = "chat"

    # Active conversation language — language subsystem, never memory/preferences.
    if _CONVERSATION_LANGUAGE_QUERY.search(result.prompt or ""):
        return {
            "action": "conversation_language",
            "params": {"question": result.prompt},
            "thinking": "active conversation language",
            "route_reason": "conversation_language",
            "route_confidence": max(confidence, 0.95),
            "route_handler": "ConversationEngine",
            "nlu": result.to_debug(),
            "semantic_report": result.to_debug(),
            "router": "nlu",
            "router_stage": "nlu_pipeline",
            "rule_matched": "conversation_language",
            "confidence_band": "high",
            "flag_for_review": False,
        }

    if is_calendar_fact_question(result.prompt or ""):
        return {
            "action": "chat",
            "params": {},
            "thinking": "calendar fact",
            "route_reason": "calendar_fact",
            "route_confidence": confidence,
            "route_handler": "ConversationEngine",
            "nlu": result.to_debug(),
            "semantic_report": result.to_debug(),
            "router": "nlu",
            "router_stage": "nlu_pipeline",
            "rule_matched": "calendar_fact",
            "confidence_band": "high",
            "flag_for_review": False,
        }

    if is_weather_forecast_question(result.prompt or "") or intent == "weather":
        from jarvis.journal_weather import parse_weather_day

        day = parse_weather_day(result.prompt or "")
        return {
            "action": "weather_forecast",
            "params": {"day": day} if day else {},
            "thinking": "weather forecast",
            "route_reason": "weather_forecast",
            "route_confidence": confidence,
            "route_handler": "weather_forecast",
            "nlu": result.to_debug(),
            "semantic_report": result.to_debug(),
            "router": "nlu",
            "router_stage": "nlu_pipeline",
            "rule_matched": "weather_forecast",
            "confidence_band": "high",
            "flag_for_review": False,
        }

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
        from jarvis.router import py_path_from_message

        prompt = result.prompt or ""
        lower = prompt.lower()
        path = py_path_from_message(prompt) or (subject if subject and "." in subject else "")
        if re.search(
            r"\b(?:fix|repair|debug)(?:\s+(?:any\s+)?(?:issues?|bugs?|errors?|problems?))?\s+(?:in\s+|the\s+file\s+)?",
            lower,
        ) or re.search(r"\bfix\s+[`'\"]?[^\s`'\"]+\.py\b", lower):
            action = "coding_fix"
            params = {"path": path}
        elif re.search(r"\b(?:improve|refactor|clean up)\b", lower) and (
            path or re.search(r"\b(?:file|code|module|script)\b", lower)
        ):
            action = "coding_improve"
            params = {"path": path}
        elif re.search(
            r"\b(?:create|write|make|generate)\b.+\b(?:script|file|module|\.py)\b",
            lower,
        ) or re.search(r"\bcoding\s+create\b", lower):
            action = "coding_create"
            params = {"description": prompt, "path": path}
        elif re.search(
            r"\b(how does|where is|explain (the )?code|what does .+ do|how is .+ implemented)\b",
            lower,
        ):
            action = "coding_chat"
            params = {"query": prompt}
        else:
            # Prefer propose/fix when NLU says coding + a concrete path, not Q&A chat.
            if path and re.search(
                r"\b(fix|improve|refactor|edit|change|update|append|add)\b", lower
            ):
                action = "coding_improve" if "fix" not in lower else "coding_fix"
                if re.search(r"\b(?:fix|repair|debug)\b", lower):
                    action = "coding_fix"
                params = {"path": path}
            else:
                action = "coding_chat"
                params = {"query": prompt}
    elif intent == "planning":
        lower = result.prompt.lower()
        if re.search(r"\b(?:add|create)\s+(?:a\s+)?task\b", lower):
            action = "planner_add_task"
            params = {"text": result.prompt}
        elif re.search(
            r"\b(?:plan my (?:day|week)|today(?:'s)? schedule|what should i do(?: today)?)\b",
            lower,
        ):
            action = "planner_today"
            params = {}
        else:
            action = "planner_plan"
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
        "planning": "PlanningEngine",
        "chat": "ConversationEngine",
    }.get(intent, "ConversationEngine")


# Backward compat
_handler_for_intent = handler_for_intent
