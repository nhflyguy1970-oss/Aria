"""Which turns carry continuity — decisions, ideas, rejections, corrections, work.

Deterministic and lexical on purpose: it runs on every archived turn, must not
load a model (the chat model and the embedder share one GPU slot), and its
mistakes have to be explainable. It decides only *what kind of statement* a
turn is. It never decides that something is true.

Only user turns can produce decisions, rejections, corrections, ideas or tasks:
ARIA proposing something is a suggestion until the user acts on it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.continuity import store

_DECISION = re.compile(
    r"\b(?:"
    r"let'?s\s+(?:go\s+with|use|stick\s+with|do|keep|build|make|choose|pick)|"
    r"we(?:'ll|\s+will)\s+(?:go\s+with|use|stick\s+with|build)|"
    r"(?:i|we)(?:'ve|\s+have)?\s+decided|"
    r"(?:i|we)\s+(?:decide|choose|chose|pick|picked)\b|"
    r"(?:we(?:'re|\s+are)|i(?:'m|\s+am))\s+going\s+(?:to\s+go\s+)?with|"
    r"decision\s*(?:is|:)|"
    r"(?:settled|agreed)\s+on|"
    r"final\s+(?:answer|decision|choice)|"
    r"go\s+with\s+(?:the\s+)?(?:\w+\s+){0,3}(?:option|approach|plan|design|idea)"
    r")",
    re.I,
)

_REJECTION = re.compile(
    r"\b(?:"
    r"(?:let'?s|we(?:'ll|\s+will)?)\s+not\s+(?:use|go|do|build)|"
    r"don'?t\s+(?:use|want|go\s+with|build|do\s+that)|"
    r"(?:we|i)\s+(?:won'?t|will\s+not|shouldn'?t)\s+(?:use|go\s+with|build|do)|"
    r"(?:not|never)\s+going\s+(?:to\s+go\s+)?with|"
    r"(?:reject|rejected|scrap|scrapped|drop|dropped|ditch|ditched)\s+(?:that|the|this|it)\b|"
    r"forget\s+(?:about\s+)?the\s+\w+\s+(?:idea|option|approach|plan)|"
    r"no,?\s+(?:not|we\s+won'?t|let'?s\s+not)|"
    r"instead\s+of\b|"
    r"rule\s+out|ruled\s+out"
    r")",
    re.I,
)

_CORRECTION = re.compile(
    r"(?:^|\b)(?:"
    r"actually,?\s|"
    r"correction\s*[:,-]|"
    r"i\s+meant\b|"
    r"that'?s\s+(?:wrong|not\s+right|incorrect)|"
    r"(?:change|update)\s+(?:that|it)\s+to\b|"
    r"not\s+\w+(?:\s+\w+)?,\s+but\b|"
    r"i\s+was\s+wrong\b|"
    r"scratch\s+that"
    r")",
    re.I,
)

_IDEA = re.compile(
    r"\b(?:"
    r"(?:i\s+have|i'?ve\s+got|here'?s)\s+an?\s+(?:\w+\s+){0,2}idea|"
    r"(?:app|application|project|business|product)\s+idea|"
    r"idea\s*(?:is|:)|"
    r"what\s+if\s+(?:we|i)\s+(?:built|build|made|make|created|create|wrote|write)|"
    r"i(?:'m|\s+am)\s+thinking\s+(?:about|of)\s+(?:building|making|creating|writing|starting)|"
    r"(?:we|i)\s+could\s+(?:build|make|create|write|start)|"
    r"i\s+want\s+to\s+(?:build|make|create|write|start)\s+(?:an?\s+)?(?:\w+\s+){0,3}"
    r"(?:app|application|tool|project|site|program|system|game)"
    r")",
    re.I,
)

_TASK = re.compile(
    r"\b(?:"
    r"(?:next|still|we|i)\s+(?:need|have|has|got)\s+to\b|"
    r"next\s+step|to-?do\b|"
    r"(?:haven'?t|have\s+not|didn'?t)\s+(?:finished|done|started)|"
    r"remaining\s+(?:work|tasks?|items?)|"
    r"(?:tomorrow|later|next\s+time)\s+(?:i|we)(?:'ll|\s+will)|"
    r"let'?s\s+(?:finish|continue|pick\s+up)|"
    r"(?:left|still)\s+to\s+do|"
    r"unfinished"
    r")",
    re.I,
)

_DONE = re.compile(
    r"\b(?:i|we)(?:'ve|\s+have)?\s+(?:finished|completed|done\s+with|shipped|implemented|fixed)\b",
    re.I,
)

_SUGGESTION = re.compile(
    r"\b(?:"
    r"i\s+(?:would\s+)?(?:suggest|recommend|propose)|"
    r"(?:my\s+)?recommendation\s*(?:is|:)|"
    r"you\s+(?:could|might|should)\s+(?:consider|use|try|go\s+with)|"
    r"consider\s+(?:using|adding|switching)|"
    r"(?:option|approach)\s+(?:\d|one|two|three|a|b)\b|"
    r"one\s+(?:option|approach)\s+(?:is|would\s+be)"
    r")",
    re.I,
)

# Questions are requests, not statements of decision or intent — except
# rhetorical "what if we built ..." ideas, handled by _IDEA itself.
_QUESTION = re.compile(r"\?\s*$")


@dataclass(frozen=True)
class Classification:
    kind: str | None  # a store record kind, or None for ordinary conversation
    status: str = ""
    acm_eligible: bool = False  # a user statement worth encoding into ACM


def classify(role: str, content: str) -> Classification:
    text = (content or "").strip()
    if not text or len(text) > 4000:
        return Classification(None)
    if role == "assistant":
        if _SUGGESTION.search(text):
            return Classification(store.SUGGESTION, store.PROPOSED)
        return Classification(None)
    if role != "user":
        return Classification(None)

    question = bool(_QUESTION.search(text))
    if _CORRECTION.search(text) and not question:
        return Classification(store.CORRECTION, store.OPEN, acm_eligible=True)
    if _REJECTION.search(text) and not question:
        return Classification(store.REJECTION, store.REJECTED, acm_eligible=True)
    if _DECISION.search(text) and not question:
        return Classification(store.DECISION, store.OPEN, acm_eligible=True)
    if _IDEA.search(text):
        return Classification(store.IDEA, store.OPEN, acm_eligible=True)
    if _DONE.search(text) and not question:
        return Classification(store.TASK, store.DONE, acm_eligible=True)
    if _TASK.search(text) and not question:
        return Classification(store.TASK, store.OPEN, acm_eligible=True)
    return Classification(None)


_STOP = frozenset(
    """a an the and or of to in on at by for with from as is are was were be been it its
    this that these those we i you our my your me us let lets let's use using go going
    with not no don't dont won't will would should could can just really actually
    instead option approach plan idea then than so also""".split()
)


def key_terms(text: str) -> set[str]:
    """Content words, for matching a user's decision to the suggestion it answers."""
    words = re.findall(r"[a-z0-9][a-z0-9+#.-]*", (text or "").lower())
    return {w.strip(".") for w in words if len(w) > 2 and w not in _STOP}
