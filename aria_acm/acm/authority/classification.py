"""Memory request classification — cognitive gate before language generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class MemoryIntent(StrEnum):
    """Which cognitive memory surface a request requires."""

    IDENTITY = "identity"
    EXPERIENCE = "experience"
    REMEMBERING = "remembering"
    REFLECTION = "reflection"
    LEARNING = "learning"
    CONCEPT = "concept"
    ASSOCIATION = "association"
    GOAL = "goal"
    PREFERENCE = "preference"
    CONFIDENCE = "confidence"
    RECONCILIATION = "reconciliation"
    PROJECT = "project"
    HISTORY = "history"
    AUTOBIOGRAPHY = "autobiography"
    PATTERN = "pattern"
    GENERAL_MEMORY = "general_memory"
    NOT_MEMORY = "not_memory"


@dataclass(frozen=True)
class MemoryRequestClassification:
    """Structured classification of an inbound request."""

    is_memory_request: bool
    intent: MemoryIntent
    confidence: float
    matched_signals: tuple[str, ...]
    reason: str

    def to_public(self) -> dict:
        return {
            "is_memory_request": self.is_memory_request,
            "intent": self.intent.value,
            "confidence": self.confidence,
            "matched_signals": list(self.matched_signals),
            "reason": self.reason,
        }


# Ordered: first match wins for intent specialization.
_INTENT_PATTERNS: list[tuple[MemoryIntent, re.Pattern[str], str]] = [
    (
        MemoryIntent.IDENTITY,
        re.compile(
            r"\b(who\s+am\s+i|who\s+are\s+you|what(?:'s|\s+is)\s+your\s+name|"
            r"your\s+identity|my\s+identity|who\s+is\s+(?:the\s+)?(?:user|assistant))\b",
            re.I,
        ),
        "identity_cue",
    ),
    (
        MemoryIntent.LEARNING,
        re.compile(
            r"\b(what\s+have\s+you\s+learned|what\s+did\s+you\s+learn|"
            r"how\s+has\s+your\s+(?:understanding|knowledge)\s+changed|"
            r"what\s+changed\s+in\s+your\s+(?:understanding|beliefs?))\b",
            re.I,
        ),
        "learning_cue",
    ),
    (
        MemoryIntent.REFLECTION,
        re.compile(
            r"\b(what\s+do\s+you\s+think\s+about|reflect(?:ion|ing)?\s+on|"
            r"why\s+do\s+you\s+(?:believe|think)|how\s+certain|"
            r"are\s+you\s+(?:sure|confident))\b",
            re.I,
        ),
        "reflection_or_metacog_cue",
    ),
    (
        MemoryIntent.CONFIDENCE,
        re.compile(
            r"\b(how\s+certain|how\s+confident|how\s+sure|"
            r"confidence\s+(?:in|about)|uncertainty)\b",
            re.I,
        ),
        "confidence_cue",
    ),
    (
        MemoryIntent.RECONCILIATION,
        re.compile(
            r"\b(conflict(?:ing)?\s+memor|reconcil|which\s+(?:is\s+)?(?:true|correct)|"
            r"contested\s+fact)\b",
            re.I,
        ),
        "reconciliation_cue",
    ),
    (
        MemoryIntent.PREFERENCE,
        re.compile(
            r"\b(prefer(?:ence|s)?|favorite|favourite|what\s+do\s+i\s+like|"
            r"what\s+do\s+you\s+know\s+about\s+my\s+preferences)\b",
            re.I,
        ),
        "preference_cue",
    ),
    (
        MemoryIntent.GOAL,
        re.compile(
            r"\b(what\s+(?:are\s+)?(?:my|your)\s+goals?|current\s+goal|"
            r"project\s+(?:goal|plan)|what\s+(?:am\s+i|are\s+we)\s+working\s+on)\b",
            re.I,
        ),
        "goal_cue",
    ),
    (
        MemoryIntent.ASSOCIATION,
        re.compile(
            r"\b(how\s+(?:are|is).+related|associat(?:e|ion)|connected\s+to|"
            r"what\s+links)\b",
            re.I,
        ),
        "association_cue",
    ),
    (
        MemoryIntent.CONCEPT,
        re.compile(
            r"\b(what\s+(?:is|are)\s+(?:a|an|the)\s+\w+|define|concept\s+of|"
            r"what\s+does\s+.+\s+mean\s+to\s+you)\b",
            re.I,
        ),
        "concept_cue",
    ),
    (
        MemoryIntent.EXPERIENCE,
        re.compile(
            r"\b(what\s+happened|what\s+occurred|past\s+experience|"
            r"when\s+did\s+(?:we|i|you)|episodic)\b",
            re.I,
        ),
        "experience_cue",
    ),
    (
        MemoryIntent.HISTORY,
        re.compile(
            r"\b(conversation\s+history|what\s+did\s+we\s+(?:discuss|talk)|"
            r"earlier\s+(?:today|we)|previous\s+(?:chat|session))\b",
            re.I,
        ),
        "history_cue",
    ),
    (
        MemoryIntent.PROJECT,
        re.compile(
            r"\b(project\s+history|this\s+project|about\s+the\s+project|"
            r"where\s+(?:did|do)\s+we\s+leave\s+off)\b",
            re.I,
        ),
        "project_cue",
    ),
    (
        MemoryIntent.PATTERN,
        re.compile(
            r"\b(pattern|what\s+do\s+you\s+usually|tend\s+to|"
            r"in\s+general\s+(?:i|you)\s+)\b",
            re.I,
        ),
        "pattern_cue",
    ),
    (
        MemoryIntent.AUTOBIOGRAPHY,
        re.compile(
            r"\b(what\s+do\s+you\s+know\s+about\s+me|tell\s+me\s+about\s+me|"
            r"about\s+myself|my\s+(?:life|background|story))\b",
            re.I,
        ),
        "autobiography_cue",
    ),
    (
        MemoryIntent.REMEMBERING,
        re.compile(
            r"\b(what\s+do\s+you\s+remember|do\s+you\s+remember|"
            r"recall|what\s+do\s+you\s+know\s+about|"
            r"what(?:'s|\s+is)\s+my\b|remember\s+(?:that|when|my))\b",
            re.I,
        ),
        "remembering_cue",
    ),
]

_GENERAL_MEMORY = re.compile(
    r"^\s*(who|what|when|where|why|how)\b.+"
    r"|\b(memor(?:y|ies|ize)|know\s+about\s+me|learned\s+about)\b",
    re.I | re.S,
)

# Pure procedural / non-cognitive host tasks (explicit negatives)
_NOT_MEMORY = re.compile(
    r"\b(write\s+(?:a\s+)?(?:poem|code|email)|translate\s+to|"
    r"generate\s+(?:an?\s+)?(?:image|story)|how\s+do\s+i\s+(?:install|compile)|"
    r"what\s+is\s+\d+\s*[\+\-\*/])\b",
    re.I,
)


def classify_memory_request(text: str) -> MemoryRequestClassification:
    """Classify whether a request requires ACM cognitive memory before speech."""
    raw = (text or "").strip()
    if not raw:
        return MemoryRequestClassification(
            is_memory_request=False,
            intent=MemoryIntent.NOT_MEMORY,
            confidence=1.0,
            matched_signals=("empty",),
            reason="empty_request",
        )

    if _NOT_MEMORY.search(raw):
        return MemoryRequestClassification(
            is_memory_request=False,
            intent=MemoryIntent.NOT_MEMORY,
            confidence=0.85,
            matched_signals=("explicit_non_memory",),
            reason="matches_non_memory_task_pattern",
        )

    signals: list[str] = []
    for intent, pattern, signal in _INTENT_PATTERNS:
        if pattern.search(raw):
            signals.append(signal)
            return MemoryRequestClassification(
                is_memory_request=True,
                intent=intent,
                confidence=0.92,
                matched_signals=tuple(signals),
                reason=f"matched_{intent.value}",
            )

    if _GENERAL_MEMORY.search(raw):
        return MemoryRequestClassification(
            is_memory_request=True,
            intent=MemoryIntent.GENERAL_MEMORY,
            confidence=0.7,
            matched_signals=("general_interrogative_or_memory_lemma",),
            reason="general_memory_heuristic",
        )

    return MemoryRequestClassification(
        is_memory_request=False,
        intent=MemoryIntent.NOT_MEMORY,
        confidence=0.6,
        matched_signals=("no_memory_signal",),
        reason="no_memory_classification",
    )
