"""Syntax — subject / verb / object relationships (not routing)."""

from __future__ import annotations

import re

from jarvis.nlu.morphology import stem_word
from jarvis.nlu.types import GrammarAnalysis, SyntaxAnalysis

_USING = re.compile(
    r"^(?:what|which)\s+(?P<object>[\w\s-]+?)\s+(?:am|are)\s+(?:i|we)\s+(?P<verb>\w+)",
    re.I,
)
_USING2 = re.compile(
    r"^(?:am|are)\s+(?:i|we)\s+(?P<verb>using)\s+(?:the\s+)?(?P<object>.+?)\??$",
    re.I,
)
_USING_YOU = re.compile(
    r"^what\s+(?P<object>[\w\s-]+?)\s+are\s+you\s+using\??$",
    re.I,
)
_MY_GPU = re.compile(
    r"^what\s+is\s+my\s+(?:current\s+)?(?P<object>gpu|graphics card|cpu|model)\??$",
    re.I,
)
_WHAT_IS = re.compile(
    r"^what\s+(?:is|are)\s+(?:a|an|the)?\s*(?P<object>.+?)\??$",
    re.I,
)
_HOW_CONFIGURE = re.compile(
    r"^how\s+(?:do|to)\s+(?:i|we)\s+(?P<verb>\w+)\s+(?P<object>.+?)\??$",
    re.I,
)
_EXPLAIN = re.compile(
    r"^(?:explain|teach me about|tell me about)\s+(?P<object>.+?)\.?$",
    re.I,
)
_SEARCH_MEMORY = re.compile(
    r"^search\s+(?:my\s+)?memory\s+(?:for\s+)?(?P<object>.+?)\.?$",
    re.I,
)
_SEARCH_WEB = re.compile(
    r"^search\s+(?:the\s+)?web\s+(?:for\s+)?(?P<object>.+?)\.?$",
    re.I,
)
_SHOW_DOCS = re.compile(
    r"^(?:show|find|get)\s+(?P<object>.+?)\s+(?:documentation|docs?)\.?$",
    re.I,
)
_SHOW_DOCS_SHORT = re.compile(r"^show\s+(?P<object>.+?)\s+docs\.?$", re.I)
_IS_RUNNING = re.compile(
    r"^is\s+(?P<object>.+?)\s+running\??$",
    re.I,
)
_WHICH_ACTIVE = re.compile(
    r"^which\s+(?P<object>[\w\s-]+?)\s+(?:is\s+)?active\??$",
    re.I,
)
_HARDWARE_INFERENCE = re.compile(
    r"^what\s+hardware\s+is\s+running\s+inference\??$",
    re.I,
)
_CONFIGURE = re.compile(
    r"^configure\s+(?P<object>.+?)\.?$",
    re.I,
)


def analyze_syntax(text: str, grammar: GrammarAnalysis) -> SyntaxAnalysis:
    raw = (text or "").strip()
    lower = raw.lower()
    subject = verb = obj = ""
    modifiers: list[str] = []

    if m := _USING.match(lower):
        obj = m.group("object").strip()
        verb = stem_word(m.group("verb"))
        subject = "i"
    elif m := _USING2.match(lower):
        verb = stem_word(m.group("verb"))
        obj = m.group("object").strip()
        subject = "i"
    elif m := _MY_GPU.match(lower):
        obj = m.group("object").strip()
        verb = "using"
        subject = "i"
    elif m := _USING_YOU.match(lower):
        obj = m.group("object").strip()
        verb = "using"
        subject = "you"
    elif m := _WHAT_IS.match(lower):
        obj = m.group("object").strip().rstrip("?")
        verb = "explain"
        subject = ""
    elif m := _HOW_CONFIGURE.match(lower):
        verb = stem_word(m.group("verb"))
        obj = m.group("object").strip().rstrip("?")
        subject = "i"
    elif m := _EXPLAIN.match(lower):
        obj = m.group("object").strip()
        verb = "explain"
    elif m := _SEARCH_MEMORY.match(lower):
        obj = m.group("object").strip()
        verb = "search"
        subject = "memory"
    elif m := _SEARCH_WEB.match(lower):
        obj = m.group("object").strip()
        verb = "search"
        subject = "web"
    elif m := _SHOW_DOCS_SHORT.match(lower):
        obj = m.group("object").strip()
        verb = "show"
        subject = "reference"
    elif m := _SHOW_DOCS.match(lower):
        obj = m.group("object").strip()
        verb = "show"
        subject = "reference"
    elif m := _IS_RUNNING.match(lower):
        obj = m.group("object").strip()
        verb = "running"
        subject = "i"
    elif m := _WHICH_ACTIVE.match(lower):
        obj = m.group("object").strip()
        verb = "active"
        subject = "i"
    elif _HARDWARE_INFERENCE.match(lower):
        obj = "hardware"
        verb = "running"
        subject = "inference"
    elif m := _CONFIGURE.match(lower):
        obj = m.group("object").strip()
        verb = "configure"
        subject = "i"

    if grammar.mood == "comparison" and not obj:
        obj = raw
        verb = "compare"
    if grammar.mood == "instruction" and not verb:
        verb = "configure"

    return SyntaxAnalysis(subject=subject, verb=verb, object=obj, modifiers=modifiers)
