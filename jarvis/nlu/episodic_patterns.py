"""Shared episodic autobiographical patterns for Aria routing guards.

Cognition lives in ACM; these patterns only prevent Mission Control / search
mis-routes and steer declarative events to Memory Authority.
"""

from __future__ import annotations

import re

_TEMPORAL = (
    r"(?:yesterday|today|this\s+morning|this\s+afternoon|this\s+evening|"
    r"last\s+night|last\s+week|last\s+month|"
    r"last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))"
)
_ACTION = (
    r"(?:bought|cleaned|went|installed|visited|built|finished|started|"
    r"drove|flew|walked|called|met|watched|read|wrote|cooked|fixed|"
    r"moved|painted|planted|hiked|ran|swam|played|taught|learned|"
    r"attended|joined|left|opened|closed|replaced|upgraded|"
    r"purchased|ordered|picked\s+up|dropped\s+off|"
    r"caught|fished|hooked|landed|released|cast)"
)

EPISODIC_TEACHING = re.compile(
    rf"(?:^\s*{_TEMPORAL}\s+i\s+{_ACTION}\s+.+\.?\s*$|"
    rf"^\s*i\s+{_ACTION}\s+.+\s+{_TEMPORAL}\s*[.!?]?\s*$)",
    re.I,
)

EPISODIC_MEMORY_QUERY = re.compile(
    rf"\b(?:"
    rf"what\s+happened(?:\s+{_TEMPORAL})?|"
    rf"what\s+did\s+i\s+\w+(?:\s+{_TEMPORAL})?|"
    rf"what\s+have\s+i\s+(?:caught|installed|bought|upgraded|visited|done|built)\b|"
    rf"where\s+did\s+i\s+go(?:\s+{_TEMPORAL})?|"
    rf"what\s+happened\s+(?:before|after)|"
    rf"explain\s+what\s+happened|"
    rf"tell\s+me\s+about\s+(?:buying|cleaning|installing|visiting|going|catching|fishing)|"
    rf"did\s+i\s+tell\s+you\b|"
    rf"what\s+(?:gpu|ram|cpu|ssd|hardware|graphics\s+card|fish)\s+did\s+i\b|"
    rf"what\s+kind\s+of\s+.+\s+do\s+i\s+prefer"
    rf")\b",
    re.I,
)

# Live workstation hardware — Mission Control, never user memory search.
LIVE_HARDWARE_QUESTION = re.compile(
    r"\b(?:"
    r"what(?:'s|\s+is)\s+my(?:\s+current)?\s+(?:gpu|cpu|ram|vram|disk|storage|graphics\s+card)\b|"
    r"what\s+(?:gpu|cpu|ram|vram|graphics\s+card|hardware)\s+do\s+i\s+have\b|"
    r"how\s+much\s+(?:ram|vram|memory|disk|storage|space|disk\s+space)\s+(?:is\s+)?(?:installed|available|free|left)\b|"
    r"how\s+much\s+(?:ram|vram|memory|disk|storage)\s+do\s+i\s+have\b|"
    r"show\s+(?:my\s+)?(?:storage\s+devices?|disk|storage|filesystem|drive|drives)\b|"
    r"show\s+(?:gpu|memory|ram|cpu|disk|storage|vram)\s+(?:status|usage)\b|"
    r"show\s+memory\s+usage\b|"
    r"show\s+gpu\s+status\b|"
    r"(?:list|show)\s+(?:my\s+)?(?:mounted\s+)?(?:drives?|volumes?|filesystems?)\b"
    r")\b",
    re.I,
)

_PAST_EVENT_CUE = re.compile(
    rf"\b(?:"
    rf"did\s+i\s+tell\s+you|"
    rf"did\s+you\s+remember|"
    rf"what\s+did\s+i\s+(?:install|buy|upgrade|replace|get|do|catch|visit|go)\b|"
    rf"where\s+did\s+i\s+go\b|"
    rf"what\s+(?:gpu|ram|cpu|ssd|hardware|fish)\s+did\s+i\b|"
    rf"what\s+kind\s+of\s+.+\s+(?:do\s+i|you)\s+prefer\b|"
    rf"(?:{_TEMPORAL})\s+i\s+{_ACTION}|"
    rf"i\s+{_ACTION}.+(?:{_TEMPORAL})"
    rf")\b",
    re.I,
)

_REFORMULATE_DID_I_TELL = re.compile(
    rf"did\s+i\s+tell\s+you\s+(?:that\s+)?(?:what\s+)?(?:(\w+)\s+)?i\s+"
    rf"(installed|bought|upgraded|replaced|got|caught|visited)\s+({_TEMPORAL}|yesterday|today|last\s+\w+)",
    re.I,
)

_VERB_TO_BASE = {
    "installed": "install",
    "bought": "buy",
    "upgraded": "upgrade",
    "replaced": "replace",
    "got": "get",
    "caught": "catch",
    "visited": "visit",
}

_REFORMULATE_WHAT_HW = re.compile(
    rf"what\s+(?:gpu|ram|cpu|ssd|hardware|graphics\s+card|fish)\s+did\s+i\s+"
    rf"(install|buy|upgrade|replace|get|catch)\s+({_TEMPORAL}|yesterday|today|last\s+\w+)?",
    re.I,
)

_REFORMULATE_WHERE_GO = re.compile(
    rf"where\s+did\s+i\s+go\s+({_TEMPORAL}|yesterday|today|last\s+\w+)",
    re.I,
)

_REFORMULATE_WHAT_OBJECT = re.compile(
    r"what\s+(?:(\w+(?:\s+\w+)?)\s+)?did\s+i\s+(catch|install|upgrade|replace|buy|visit)\b",
    re.I,
)

_REFORMULATE_PREFER = re.compile(
    r"what\s+kind\s+of\s+(.+?)\s+do\s+i\s+prefer\b",
    re.I,
)


def is_episodic_teaching(text: str) -> bool:
    return bool(EPISODIC_TEACHING.search((text or "").strip()))


def is_episodic_memory_query(text: str) -> bool:
    return bool(EPISODIC_MEMORY_QUERY.search(text or ""))


def is_episodic_memory_utterance(text: str) -> bool:
    """Teaching or recall — must stay on Memory Authority, not Mission Control."""
    return is_episodic_teaching(text) or is_episodic_memory_query(text)


def is_live_hardware_question(text: str) -> bool:
    """Questions about the current machine — Mission Control, not memory."""
    blob = (text or "").strip()
    if not blob:
        return False
    if is_episodic_teaching(blob) or is_past_event_memory_question(blob):
        return False
    return bool(LIVE_HARDWARE_QUESTION.search(blob))


def is_past_event_memory_question(text: str) -> bool:
    """Questions about remembered past events — ACM recall, not Mission Control."""
    blob = (text or "").strip()
    if not blob or is_episodic_teaching(blob):
        return False
    if is_episodic_memory_query(blob):
        return True
    if _REFORMULATE_PREFER.search(blob):
        return True
    return bool(_PAST_EVENT_CUE.search(blob))


def reformulate_for_acm_recall(question: str) -> str | None:
    """Rewrite recall phrasing ACM understands better (Aria-only; no ACM changes)."""
    q = (question or "").strip()
    if not q:
        return None
    m = _REFORMULATE_DID_I_TELL.search(q)
    if m:
        verb = _VERB_TO_BASE.get(m.group(2).lower(), m.group(2))
        when = m.group(3)
        return f"What did I {verb} {when}?"
    m = _REFORMULATE_WHAT_HW.search(q)
    if m:
        verb = _VERB_TO_BASE.get(m.group(1).lower(), m.group(1))
        when = (m.group(2) or "").strip()
        if when:
            return f"What did I {verb} {when}?"
        return f"What did I {verb}?"
    m = _REFORMULATE_WHERE_GO.search(q)
    if m:
        return f"What did I do {m.group(1)}?"
    m = _REFORMULATE_WHAT_OBJECT.search(q)
    if m:
        verb = _VERB_TO_BASE.get(m.group(2).lower(), m.group(2))
        return f"What did I {verb}?"
    m = _REFORMULATE_PREFER.search(q)
    if m:
        topic = m.group(1).strip()
        return f"What do I prefer about {topic}?"
    if re.search(r"\bdid\s+i\s+tell\s+you\b", q, re.I):
        stripped = re.sub(r"^did\s+i\s+tell\s+you\s+(?:that\s+)?", "", q, flags=re.I).strip(" ?.")
        if stripped and not stripped.lower().startswith(("what ", "who ", "when ", "where ")):
            return f"What {stripped}?"
    return None
