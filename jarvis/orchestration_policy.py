"""General orchestration policy — task class, research need, verification, honesty.

This module is intentionally model- and product-agnostic. It does not encode
Ford-specific or prompt-specific special cases. Routers and conversation
handlers consult it so Aria distinguishes:

* stable knowledge vs current/external verification
* local project docs vs world knowledge
* personal memory evidence vs model invention
* consequential specifications vs unverified model text
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# --- Local project / documentation corpus cues (reference_search only) ---
# Strong cues = Aria's own corpus. Weak doc nouns alone are NOT local (world manuals).
_LOCAL_CORPUS_STRONG = re.compile(
    r"\b(?:"
    r"readme|adr|changelog|architecture|"
    r"this\s+(?:project|repo|codebase|repository)|"
    r"in\s+(?:the\s+)?(?:project|repo|codebase)|"
    # Bare "ARIA-…" tokens (memory markers) are not the product docs corpus.
    r"jarvis|aria\s+core|aria(?!-)|ai[- ]?platform|"
    r"our\s+(?:docs?|documentation|readme)|"
    r"local\s+(?:docs?|documentation)"
    r")\b",
    re.I,
)
_LOCAL_CORPUS_WEAK = re.compile(
    r"\b(?:docs?|documentation|manual|specification|spec)\b",
    re.I,
)
_LOCAL_CORPUS_CUE = _LOCAL_CORPUS_STRONG  # prefers_local_reference uses strong only

# --- Temporal / current-information language ---
_TEMPORAL_CURRENT = re.compile(
    r"\b(?:"
    r"latest|current|currently|newest|today|tonight|tomorrow|right\s+now|as\s+of|"
    r"this\s+(?:week|month|year)|recent(?:ly)?|up[- ]?to[- ]?date|"
    r"who\s+currently|what(?:'s|\s+is)\s+the\s+(?:latest|current)|"
    r"most\s+recent|newly\s+released|release\s+notes?\s+for|"
    r"does\s+.+\s+(?:version\s+)?[\w.]*\d[\d.]*\s+exist|"
    r"is\s+there\s+(?:a|an)\b.+\b(?:version|model|revision|driver)\b"
    r")\b",
    re.I,
)

# --- Explicit research / look-up verbs ---
_EXPLICIT_RESEARCH = re.compile(
    r"\b(?:"
    r"search\s+(?:the\s+)?(?:web|online)|web\s+search|look\s+up(?:\s+online)?|"
    r"search\s+up|google|find\s+out|research|compare\b.+\busing\s+current|"
    r"find\s+the\s+official|official\s+documentation|official\s+manual|"
    r"what\s+does\s+(?:the|its|their)\s+(?:official\s+)?(?:manual|documentation|docs?)\b|"
    r"what\s+does\s+.+\b(?:manual|documentation)\s+say\b|"
    r"what\s+does\s+(?:the|its|their)\s+official|"
    r"according\s+to\b.+\b(?:manual|owner'?s?\s+manual|spec|revision|rev)\b|"
    r"show\s+.+\bdocumentation\b|documentation\s+for\b|"
    r"confirm\s+that\s+torque|confirm\s+(?:this|that)\s+(?:torque|spec)|"
    r"authoritative\s+sources?|conflicting\s+(?:web\s+)?sources|"
    r"prefer\s+authoritative"
    r")\b",
    re.I,
)

# --- Consequential real-world / safety domains (general, not brand-specific) ---
_CONSEQUENTIAL_DOMAIN = re.compile(
    r"\b(?:"
    r"torque|ft-?lbf?|n(?:ewton)?[- ]?m(?:eter)?s?|"
    r"brakes?|rotors?|discs?|calipers?|pads?|bleed(?:ing)?\s+the\s+brakes?|"
    r"electrical|wiring|voltage|amperage|240\s*v|120\s*v|"
    r"fsck|rm\s+-rf|mkfs|dd\s+if=|format\s+the\s+(?:disk|drive)|"
    r"medication|dosage|mg\b|ml\b|"
    r"structural\s+load|load[- ]bearing|"
    r"legal\s+requirement|regulation|code\s+compliance|"
    r"replace\s+the\s+(?:battery|rotors?|pads?|brakes?|discs?)|"
    r"how\s+(?:do|to)\s+(?:i|we)\s+(?:change|replace|install|remove|service)\b|"
    r"(?:brake|rotors?|discs?|calipers?|battery|alternator|spark\s+plug|timing\s+belt)|"
    r"vehicle|truck|car|motorcycle|key\s+fob|"
    r"show\s+me\s+how\s+to\s+(?:change|replace|install|remove|service)\b"
    r")\b",
    re.I,
)

_CRITICAL_SPEC_IN_ANSWER = re.compile(
    r"\b\d{1,4}(?:\.\d+)?\s*(?:"
    r"ft[- ]?lbf?|ft·lb|lbf?[- ]?ft|n(?:ewton)?[- ]?m(?:eter)?s?|nm\b|"
    r"psi|bar|volts?|amps?|amperes?|watts?|"
    r"mg\b|ml\b|mcg\b"
    r")\b",
    re.I,
)

# Stable conceptual / writing / math — must NOT force research.
_STABLE_LOCAL = re.compile(
    r"\b(?:"
    r"what\s+is\s+a\b|what\s+does\s+.+\s+mean\b|explain\b|difference\s+between\b|"
    r"rewrite|make\s+this\s+(?:easier|professional|clearer)|"
    r"turn\s+these\s+notes|summarize\s+the\s+tradeoffs|"
    r"hello|hi\b|hey\b|how\s+are\s+you|"
    r"\d+\s*(?:[\+\-\*/x×÷]|times|plus|minus)\s*\d+"
    r")\b",
    re.I,
)

# Personal memory questions — require ACM evidence, never invented biography.
_PERSONAL_MEMORY_ASK = re.compile(
    r"\b(?:"
    r"what\s+(?:computer|machine|workstation|gpu|graphics\s+card|nvidia\s+card|project|model)\s+(?:was\s+i|did\s+i|do\s+i)\b|"
    r"what\s+(?:gpu|graphics\s+card|nvidia\s+card)\s+(?:did\s+i|do\s+i|was\s+i|did\s+we)\b|"
    r"which\s+(?:gpu|graphics\s+card|nvidia\s+card)\s+(?:did\s+i|do\s+i|did\s+we|was\s+i)\b|"
    r"what\s+(?:nvidia\s+card|graphics\s+card|gpu)\s+am\s+i\s+running\s+for\b|"
    r"what\s+(?:computer|machine|workstation|project)\s+am\s+i\b|"
    r"what\s+was\s+the\s+name\s+of\s+my\b|"
    r"what(?:'s|\s+is)\s+the\s+name\s+of\s+my\b|"
    r"who\s+is\s+my\b|"
    r"what(?:'s|\s+is)\s+my\s+\w[\w\s-]{0,30}?\s+name\b|"
    r"what\s+did\s+we\s+decide\b|"
    r"remind\s+me\s+(?:what|of|about)\b|"
    r"what\s+(?:fly[- ]?tying\s+)?project\s+(?:did\s+i|was\s+i|i\s+told)|"
    r"continue\s+(?:the\s+)?(?:project|work)\s+from\s+where|"
    # Owned personal items previously taught — not live hardware probes.
    r"what\s+(?!gpu\b|cpu\b|ram\b|vram\b|disk\b)(\w[\w\s-]{0,40}?)\s+do\s+i\s+have\b|"
    r"what\s+\w[\w\s-]{0,40}?\s+do\s+i\s+have\s+in\s+the\b|"
    # Acceptance / unique stored markers — Memory Authority, not chat invention.
    r"ARIA-FINAL-MEMORY|"
    r"(?:unique\s+)?(?:acceptance\s+)?memory\s+marker|"
    r"what\s+(?:exact\s+)?(?:marker|token)\b|"
    r"ask(?:ed)?\s+you\s+to\s+remember|"
    r"marker\s+i\s+just\s+stored|"
    r"recall\s+only\b"
    r")\b",
    re.I,
)

# --- Destructive system-wide wipe / erase (conversational refusal; not skill exec) ---
# Distinguish from scoped admin (/tmp/…, uninstall package, single disposable dir).
_DESTRUCTIVE_SYSTEM_REQUEST = re.compile(
    r"(?:"
    r"\b(?:wipe|erase|destroy|obliterate|nuke)\b[\s\S]{0,80}?\b"
    r"(?:root(?:\s+filesystem)?|entire\s+(?:system|disk|drive|filesystem)|"
    r"boot\s+(?:disk|drive)|linux\s+installation|/)|"
    r"\b(?:delete|remove|erase)\b[\s\S]{0,60}?\bentire\s+root\s+filesystem\b|"
    r"\b(?:delete|remove|erase)\b[\s\S]{0,40}?\beverything\b[\s\S]{0,40}?(?:from\s+)?`?/|"
    r"\b(?:delete|remove)\s+everything\s+from\s+`?/|"
    r"\brecursively\s+(?:force[- ]?)?delete\b[\s\S]{0,80}?\b"
    r"(?:everything|entire\s+system|/)|"
    r"\b(?:force[- ]?)?delete\s+everything\s+under\s+`?/|"
    r"\brecursively\s+delete\s+the\s+entire\s+system\b|"
    r"\bgive\s+me\s+(?:the\s+)?(?:exact\s+)?command\b[\s\S]{0,80}?\b(?:wipe|erase|destroy)\b|"
    r"\b(?:exact\s+)?command\s+to\s+(?:wipe|erase|destroy)\b|"
    r"\bwhat\s+command\s+deletes\b[\s\S]{0,60}?`?/|"
    r"\bhow\s+(?:do\s+i|can\s+i|to)\s+(?:completely\s+)?"
    r"(?:erase|wipe|destroy|recursively\s+delete)\b[\s\S]{0,60}?\b(?:root|system|/|boot|linux)\b|"
    r"\bfastest\s+way\s+to\s+remove\s+all\s+files\s+from\s+`?/|"
    r"\bremove\s+all\s+files\s+from\s+`?/|"
    r"\bshell\s+command\b[\s\S]{0,80}?\b(?:recursively|force[- ]?delete|wipe)\b[\s\S]{0,40}?/|"
    r"\brm\s+-rf\s+/|"
    r"\berase\s+(?:my\s+)?boot\s+drive\b|"
    r"\bdestroy\s+(?:the\s+)?(?:entire\s+)?(?:linux\s+)?installation\b|"
    r"\bwipe\s+`?/"
    r")",
    re.I,
)
_SCOPED_ADMIN_SAFE = re.compile(
    r"(?:"
    r"/tmp/[^\s`\"']+|"
    r"ARIA-REPAIR|"
    r"disposable\s+test\s+(?:dir(?:ectory)?|folder)|"
    r"uninstall\s+(?:a\s+)?package|"
    r"\b(?:delete|remove)\s+(?:the\s+)?(?:file|folder|directory)\s+/tmp/"
    r")",
    re.I,
)

_MEMORY_EVIDENCE_MARKERS = re.compile(
    r"\b(?:i\s+remember|according\s+to\s+(?:your|my)\s+memory|from\s+memory|"
    r"you\s+(?:told|said|mentioned)\s+me|stored\s+memory|acm)\b",
    re.I,
)


@dataclass(frozen=True)
class TaskPolicy:
    """Lightweight task classification for routing guards."""

    task_class: str
    research_required: bool
    memory_required: bool
    local_reference_ok: bool
    consequential: bool
    reason: str


def prefers_local_reference(message: str) -> bool:
    """True only when the user is asking about local/project documentation."""
    text = message or ""
    if _LOCAL_CORPUS_STRONG.search(text):
        return True
    # Weak doc nouns alone are world/research unless paired with a strong local cue.
    return False


def is_consequential_request(message: str) -> bool:
    text = message or ""
    if _STABLE_LOCAL.search(text) and not _CONSEQUENTIAL_DOMAIN.search(text):
        return False
    return bool(_CONSEQUENTIAL_DOMAIN.search(text))


def is_destructive_system_request(message: str) -> bool:
    """True for system-wide wipe/erase of `/`, boot disk, or entire installation.

    Scoped admin (e.g. delete `/tmp/ARIA-REPAIR-test`, uninstall a package) is False.
    """
    text = (message or "").strip()
    if not text:
        return False
    if _SCOPED_ADMIN_SAFE.search(text) and not re.search(
        r"\brm\s+-rf\s+/|wipe\s+`?/`?|entire\s+root|boot\s+drive|linux\s+installation",
        text,
        re.I,
    ):
        return False
    return bool(_DESTRUCTIVE_SYSTEM_REQUEST.search(text))


def destructive_system_refusal(message: str = "") -> str:
    """Clear refusal — never include actionable wipe/erase commands."""
    return (
        "I will not provide commands that wipe or destroy an entire system, "
        "the root filesystem (`/`), or a boot disk.\n\n"
        "Those operations are irreversible and can permanently destroy data and the OS. "
        "A warning does not make those instructions acceptable to give.\n\n"
        "If you have a legitimate goal, I can help with safer alternatives instead, such as:\n"
        "• backing up data before a planned reinstall\n"
        "• walking through a clean OS reinstall from recovery media\n"
        "• removing a specific disposable directory (for example under `/tmp/`)\n"
        "• uninstalling a package\n\n"
        "What are you actually trying to accomplish?"
    )


def answer_has_actionable_destructive_command(answer: str) -> bool:
    """Detect owner-facing actionable wipe/erase shell instructions."""
    text = answer or ""
    return bool(
        re.search(
            r"(?:"
            r"\bsudo\s+rm\s+-rf\s+/|"
            r"\brm\s+-rf\s+/\s*(?:;|$|\n|`)|"
            r"```(?:bash|sh|shell|zsh)?\s*\n\s*(?:sudo\s+)?rm\s+-rf\s+/|"
            r"\bmkfs\.\w+\s+/dev/\w+"
            r")",
            text,
            re.I,
        )
    )


def research_required(message: str) -> bool:
    """General decision: does this request need external verification?"""
    text = (message or "").strip()
    if not text:
        return False
    if re.search(
        r"^\s*(hi|hello|hey|how are you|how's it going|good (?:morning|afternoon|evening))\b",
        text,
        re.I,
    ):
        return False
    # Local calendar/clock facts are chat — "today" alone is not web research.
    try:
        from jarvis.nlu.mapping import is_calendar_fact_question

        if is_calendar_fact_question(text):
            return False
    except Exception:
        if re.search(r"\bwhat\s+day\s+is\s+(?:it|today)\b|\btoday'?s\s+date\b", text, re.I):
            return False
    # Live weather is a dedicated capability — not web research.
    if re.search(
        r"\b(?:weather|forecast|temperature|temps?|rain(?:y|ing)?|snow(?:y|ing)?|"
        r"humid(?:ity)?|windy|cloudy|sunny)\b",
        text,
        re.I,
    ) and not _EXPLICIT_RESEARCH.search(text):
        return False
    if _STABLE_LOCAL.search(text) and not _TEMPORAL_CURRENT.search(text) and not _CONSEQUENTIAL_DOMAIN.search(text):
        # "Explain recursion" / rewrite / math — local.
        if not _EXPLICIT_RESEARCH.search(text):
            return False
    if prefers_local_reference(text) and not _TEMPORAL_CURRENT.search(text):
        # Local docs questions are reference_search, not web — unless also current/world.
        if not _EXPLICIT_RESEARCH.search(text) and not is_consequential_request(text):
            return False
    if _EXPLICIT_RESEARCH.search(text):
        return True
    if _TEMPORAL_CURRENT.search(text):
        return True
    if is_consequential_request(text):
        return True
    # Prices / officeholders / versions without explicit "latest"
    if re.search(
        r"\b(?:"
        r"price\s+of|stock\s+price|who\s+(?:is|holds)\s+(?:the\s+)?(?:president|prime\s+minister)|"
        r"what\s+version\s+of|release\s+of\b"
        r")\b",
        text,
        re.I,
    ):
        return True
    return False


def is_personal_memory_question(message: str) -> bool:
    return bool(_PERSONAL_MEMORY_ASK.search(message or ""))


def classify_task_policy(message: str) -> TaskPolicy:
    text = message or ""
    consequential = is_consequential_request(text)
    need_research = research_required(text)
    need_memory = is_personal_memory_question(text)
    local_ok = prefers_local_reference(text) and not need_research and not consequential

    if need_memory:
        task_class = "personal_memory"
    elif consequential:
        task_class = "consequential_real_world_action"
    elif need_research and _TEMPORAL_CURRENT.search(text):
        task_class = "current_information"
    elif need_research:
        task_class = "web_research"
    elif local_ok:
        task_class = "local_search"
    elif _STABLE_LOCAL.search(text):
        task_class = "knowledge"
    else:
        task_class = "conversation"

    reason_parts = []
    if need_research:
        reason_parts.append("research_required")
    if consequential:
        reason_parts.append("consequential")
    if need_memory:
        reason_parts.append("memory_required")
    if local_ok:
        reason_parts.append("local_corpus")
    return TaskPolicy(
        task_class=task_class,
        research_required=need_research,
        memory_required=need_memory,
        local_reference_ok=local_ok,
        consequential=consequential,
        reason=",".join(reason_parts) or "default",
    )


def answer_has_unverified_critical_spec(answer: str) -> bool:
    return bool(_CRITICAL_SPEC_IN_ANSWER.search(answer or ""))


_AUTHORITATIVE_HOST = re.compile(
    r"(?:"
    r"ford\.com|motorcraft|service\.ford|owner\.ford|"
    r"gm\.com|toyota\.com|nissanusa\.com|honda\.com|chrysler|stellantis|"
    r"nhtsa\.gov|iihs\.org|"
    r"ubuntu\.com|kernel\.org|python\.org|nodejs\.org|nvidia\.com|"
    r"docs\.python\.org|huggingface\.co|"
    r"docs\.docker\.com|learn\.microsoft\.com|docs\.microsoft\.com"
    r")",
    re.I,
)

_WEAK_HOST = re.compile(
    r"(?:"
    r"justanswer|quora|reddit\.com|pinterest|ebay|facebook|"
    r"answers\.yahoo|fixoverflow\.com|"  # SO ok for software, weak for torque
    r"blogspot|wordpress\.com|medium\.com/p/"
    r")",
    re.I,
)


def sources_are_authoritative_for_consequential(answer: str, results: list | None = None) -> bool:
    """True when consequential claims are backed by sufficiently authoritative URLs."""
    urls: list[str] = []
    for r in results or []:
        if isinstance(r, dict) and r.get("url"):
            urls.append(str(r.get("url")))
    urls.extend(re.findall(r"https?://[^\s\]\)]+", answer or ""))
    if not urls:
        return False
    if any(_AUTHORITATIVE_HOST.search(u) for u in urls):
        return True
    # All-weak sources (forums/Q&A) are not enough for critical specs.
    if urls and all(_WEAK_HOST.search(u) for u in urls):
        return False
    return False


def consequential_web_answer_ok(message: str, answer: str, results: list | None = None) -> str | None:
    """Return replacement text when web synthesis asserts critical specs on weak evidence."""
    if not is_consequential_request(message):
        return None
    if not answer_has_unverified_critical_spec(answer):
        return None
    if sources_are_authoritative_for_consequential(answer, results):
        return None
    return (
        "I found online discussion of this topic, but not an authoritative manufacturer "
        "or official specification I trust enough to quote as fact. "
        "Please use the OEM service manual (or a dealer/service portal) for torque and "
        "safety-critical figures — I will not invent or promote unverified numbers."
    )


def strip_or_refuse_unverified_specs(
    message: str,
    answer: str,
    *,
    verified: bool,
) -> str | None:
    """If consequential + critical specs + not verified, refuse instead of asserting.

    Returns None when the answer may stand; otherwise a replacement reply.
    """
    if verified:
        return None
    if not is_consequential_request(message):
        return None
    if not answer_has_unverified_critical_spec(answer):
        return None
    return (
        "I should not give precise safety-critical specifications "
        "(such as torque, electrical ratings, or dosages) without verifying them "
        "from an authoritative source. I was unable to verify those figures for your "
        "request. Please check the manufacturer service information, or ask me to "
        "research a specific official source."
    )


def memory_honesty_refusal(message: str) -> str:
    return (
        "I don't have a stored memory that answers that. "
        "If you tell me the fact again, I can remember it for next time."
    )


def should_apply_memory_honesty(message: str, answer: str, *, had_memory_hits: bool) -> bool:
    """True when chat is about to invent personal recall without evidence."""
    if had_memory_hits:
        return False
    if not is_personal_memory_question(message):
        return False
    # If the model hedges honestly, leave it.
    if re.search(
        r"\b(?:i\s+don'?t\s+(?:remember|know|have)|no\s+record|not\s+sure|"
        r"you\s+(?:haven'?t|have\s+not)\s+told\s+me|still\s+learning\s+about\s+you)\b",
        answer or "",
        re.I,
    ):
        return False
    # Confident personal assertions without memory evidence → rewrite.
    if re.search(
        r"\b(?:you\s+(?:were|are|mentioned|told|said)|your\s+(?:computer|laptop|project|gpu)|"
        r"it(?:'s|\s+is)\s+a\s+\d{4}\s+model)\b",
        answer or "",
        re.I,
    ):
        return True
    return bool(_MEMORY_EVIDENCE_MARKERS.search(answer or ""))


def tool_result_answers_request(message: str, tool_name: str, tool_preview: str) -> bool:
    """Heuristic relevance check — tool success ≠ task success."""
    msg = (message or "").lower()
    preview = (tool_preview or "").lower()
    name = (tool_name or "").lower()
    if name.startswith("reference") or name == "reference_search":
        if prefers_local_reference(message):
            return True
        # Local changelog/readme answering a world how-to is irrelevant.
        if re.search(r"changelog|v\d+\.\d+|ai platform|generated_at|python_files", preview):
            if is_consequential_request(message) or research_required(message):
                return False
        # Require at least one non-trivial content overlap beyond stopwords.
        terms = [t for t in re.findall(r"[a-z0-9]{4,}", msg) if t not in {
            "show", "change", "with", "that", "this", "have", "from", "your", "what", "how",
        }]
        hits = sum(1 for t in terms[:12] if t in preview)
        return hits >= 2
    return True


def route_override_for_policy(message: str, action: str) -> dict[str, Any] | None:
    """If the selected action conflicts with task policy, return a corrected intent."""
    policy = classify_task_policy(message)
    act = (action or "chat").strip()

    # P0: never emit actionable system-wipe commands (warning ≠ refusal).
    if is_destructive_system_request(message):
        return {
            "action": "chat",
            "params": {
                "policy_fixed_reply": destructive_system_refusal(message),
                "policy_refusal": "destructive_system",
            },
            "thinking": "orchestration_policy_destructive_refusal",
            "route_reason": "policy_destructive_system_refusal",
            "route_handler": "Conversation",
            "route_confidence": 1.0,
            "task_class": "destructive_system_refusal",
        }

    # Never answer world/consequential how-tos from local project docs.
    if act in ("reference_search", "documentation_search") or act.startswith("reference_"):
        if not policy.local_reference_ok:
            if policy.research_required or policy.consequential:
                return {
                    "action": "web_search",
                    "params": {"query": message},
                    "thinking": "orchestration_policy_research",
                    "route_reason": "policy_research_required",
                    "route_handler": "WebSearch",
                    "route_confidence": 0.9,
                    "task_class": policy.task_class,
                }
            # Ambiguous how-to with no local cue → chat (may clarify), not docs.
            return {
                "action": "chat",
                "params": {},
                "thinking": "orchestration_policy_not_local_docs",
                "route_reason": "policy_reject_reference_catchall",
                "route_handler": "Conversation",
                "route_confidence": 0.7,
                "task_class": policy.task_class,
            }

    # Subject-change discourse ("forget the truck, let's work on…") is chat —
    # do not steal into web_search merely because the discarded topic named a vehicle (RW-009).
    if re.search(
        r"\bforget\s+(?:the\s+|about\s+)?(?!that\s+i\b).{0,40}?"
        r"(?:let'?s|i\s+want|we\s+(?:should|can)|switch\s+to)\b",
        message or "",
        re.I,
    ):
        if act in ("web_search", "chat") or str(act).startswith("runtime_"):
            if act != "chat":
                return {
                    "action": "chat",
                    "params": {},
                    "thinking": "orchestration_policy_subject_change",
                    "route_reason": "policy_conversational_subject_change",
                    "route_handler": "Conversation",
                    "route_confidence": 0.9,
                    "task_class": "conversation",
                }
            return None

    # Current/research questions stuck on bare chat → web_search action.
    if act == "chat" and policy.research_required and not policy.memory_required:
        return {
            "action": "web_search",
            "params": {"query": message},
            "thinking": "orchestration_policy_research",
            "route_reason": "policy_research_required",
            "route_handler": "WebSearch",
            "route_confidence": 0.85,
            "task_class": policy.task_class,
        }

    # Mission Control must not steal world/current research (GPU drivers, official docs, etc.).
    if (
        policy.research_required
        and not policy.memory_required
        and str(act).startswith("runtime_")
    ):
        return {
            "action": "web_search",
            "params": {"query": message},
            "thinking": "orchestration_policy_research_over_runtime",
            "route_reason": "policy_research_over_runtime",
            "route_handler": "WebSearch",
            "route_confidence": 0.9,
            "task_class": policy.task_class,
        }

    # Writing requests must stay conversational prose — never runtime_status (RW-010)
    # and never web_search template scraping for draft text/email.
    try:
        from jarvis.runtime_routing import is_writing_request

        if is_writing_request(message) and (
            str(act).startswith("runtime_")
            or act in ("status_summary", "web_search")
        ):
            return {
                "action": "chat",
                "params": {},
                "thinking": "orchestration_policy_writing",
                "route_reason": "policy_writing_over_runtime",
                "route_handler": "Conversation",
                "route_confidence": 0.9,
                "task_class": "writing",
            }
    except Exception:
        pass

    # Personal memory questions should hit Memory Authority, not fly/runtime/chat invention.
    if policy.memory_required and (
        act in ("chat", "fly_search", "fly_ask", "reference_search")
        or str(act).startswith("runtime_")
    ):
        return {
            "action": "memory_about_user",
            "params": {"question": message},
            "thinking": "orchestration_policy_memory",
            "route_reason": "policy_personal_memory",
            "route_handler": "MemoryEngine",
            "route_confidence": 0.85,
            "task_class": policy.task_class,
        }

    # User assertion of a consequential spec is not independent verification —
    # do not store/confirm as fact via remember/memory; research or refuse.
    if (
        act in ("remember", "memory_correct", "memory_about_user", "chat")
        and is_consequential_request(message)
        and re.search(
            r"\b(?:confirm|verify)\b.+\b(?:torque|spec|correct)\b|"
            r"\buses?\s+a\s+\d+[^\n]{0,40}\b(?:nm|ft[- ]?lbf?)\b.+\bconfirm\b|"
            r"\bconfirm\b.+\buses?\s+a\s+\d+",
            message or "",
            re.I,
        )
    ):
        return {
            "action": "web_search",
            "params": {"query": message},
            "thinking": "orchestration_policy_user_assertion_not_verified",
            "route_reason": "policy_consequential_assertion",
            "route_handler": "WebSearch",
            "route_confidence": 0.85,
            "task_class": policy.task_class,
        }

    return None
