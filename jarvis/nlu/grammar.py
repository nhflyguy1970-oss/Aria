"""Grammar analysis — sentence structure and question type (not routing)."""

from __future__ import annotations

import re

from jarvis.nlu.types import GrammarAnalysis

_WH = re.compile(r"^(what|which|who|where|when|why|how)\b", re.I)
_IMPERATIVE = re.compile(
    r"^(show|list|get|search|find|configure|run|start|stop|restart|open|close|"
    r"export|backup|restore|commit|pull|push|remember|forget|learn|explain|teach)\b",
    re.I,
)
_COMPARISON = re.compile(r"\b(compare|versus|vs\.?|difference between)\b", re.I)
_EXPLANATION = re.compile(r"\b(explain|describe|what is|what are|tell me about)\b", re.I)
_REQUEST = re.compile(r"\b(please|could you|can you|would you)\b", re.I)
_INSTRUCTION = re.compile(r"\b(how (?:do|to)|steps to|guide to|tutorial)\b", re.I)


def analyze_grammar(text: str) -> GrammarAnalysis:
    raw = (text or "").strip()
    lower = raw.lower()
    if not lower:
        return GrammarAnalysis()

    question_type = ""
    sentence_type = "declarative"

    if raw.endswith("?"):
        sentence_type = "interrogative"
        if m := _WH.match(lower):
            question_type = m.group(1).lower()
    elif _IMPERATIVE.match(lower):
        sentence_type = "imperative"
    elif _REQUEST.search(lower):
        sentence_type = "request"

    mood = "neutral"
    if _COMPARISON.search(lower):
        mood = "comparison"
    elif _INSTRUCTION.search(lower):
        mood = "instruction"
    elif _EXPLANATION.search(lower):
        mood = "explanation"

    return GrammarAnalysis(
        sentence_type=sentence_type,
        question_type=question_type,
        mood=mood,
    )
