"""Syntax — subject / verb / object relationships (not routing)."""

from __future__ import annotations

import re

from jarvis.nlu.morphology import stem_word
from jarvis.nlu.types import GrammarAnalysis, SyntaxAnalysis

_USING = re.compile(
    r"^(?:what|which)\s+(?P<object>[\w\s-]+?)\s+(?:am|are)\s+(?:i|we)\s+(?P<verb>\w+)",
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
    r"^(?:show|find|get)\s+(?P<object>.+?)\s+documentation\.?$",
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
    elif m := _SHOW_DOCS.match(lower):
        obj = m.group("object").strip()
        verb = "show"
        subject = "documentation"

    if grammar.mood == "comparison" and not obj:
        obj = raw
        verb = "compare"
    if grammar.mood == "instruction" and not verb:
        verb = "configure"

    return SyntaxAnalysis(subject=subject, verb=verb, object=obj, modifiers=modifiers)
