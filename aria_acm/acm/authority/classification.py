"""Cognitive Intent Classification — determine ownership before any speech.

Every inbound request passes through this classifier. The language model
never decides which cognitive organ answers. Uncertain classifications do
**not** silent-bypass to the language model for autobiographical/cognitive
questions (D039).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from acm.authority.taxonomy import (
    COGNITIVE_INTENTS,
    NON_COGNITIVE_INTENTS,
    CognitiveIntent,
)

# Backward-compatible alias (v0.15 Memory Authority).
MemoryIntent = CognitiveIntent


@dataclass(frozen=True)
class MemoryRequestClassification:
    """Structured classification of an inbound request.

    ``uncertain`` is True when ACM cannot assign a specialized intent with
    high confidence. Cognitive-conservative policy: when autobiographical or
    agent/user self cues are present without a clear non-cognitive match,
    ``is_memory_request`` remains True (route through Memory Authority).
    """

    is_memory_request: bool
    intent: CognitiveIntent
    confidence: float
    matched_signals: tuple[str, ...]
    reason: str
    uncertain: bool = False
    ownership_hint: str = ""  # primary organ hint (filled/confirmed by routing)

    def to_public(self) -> dict:
        return {
            "is_memory_request": self.is_memory_request,
            "intent": self.intent.value,
            "confidence": self.confidence,
            "matched_signals": list(self.matched_signals),
            "reason": self.reason,
            "uncertain": self.uncertain,
            "ownership_hint": self.ownership_hint,
            "schema": "cognitive_intent_classification.v1",
        }


# ---------------------------------------------------------------------------
# Pattern tables — ordered: first match wins within each priority band.
# ---------------------------------------------------------------------------

_Pattern = tuple[CognitiveIntent, re.Pattern[str], str, float]

# Band A: Non-cognitive (explicit host tasks) — checked first.
_NON_COGNITIVE: list[_Pattern] = [
    (
        CognitiveIntent.PROCEDURAL,
        re.compile(
            r"\b(write\s+(?:a\s+)?(?:poem|code|email|script|function)|"
            r"generate\s+(?:an?\s+)?(?:image|story|song)|"
            r"how\s+do\s+i\s+(?:install|compile|configure|setup|set\s+up)|"
            r"refactor\s+(?:this|the)|fix\s+(?:this\s+)?(?:bug|error))\b",
            re.I,
        ),
        "procedural_task",
        0.92,
    ),
    (
        CognitiveIntent.TOOL_REQUEST,
        re.compile(
            r"\b(run\s+(?:the\s+)?(?:command|script|test)|call\s+(?:the\s+)?(?:api|tool)|"
            r"use\s+(?:the\s+)?(?:tool|browser|shell)|execute\s+)\b",
            re.I,
        ),
        "tool_request",
        0.9,
    ),
    (
        CognitiveIntent.CONVERSATION_MANAGEMENT,
        re.compile(
            r"^\s*(hi|hello|hey|thanks|thank\s+you|ok(?:ay)?|goodbye|bye)\s*[!.]?\s*$|"
            r"\b(stop\s+talking|be\s+quiet|never\s+mind|nevermind)\b",
            re.I,
        ),
        "conversation_management",
        0.88,
    ),
    (
        CognitiveIntent.GENERAL_KNOWLEDGE,
        re.compile(
            r"\b(what\s+is\s+\d+\s*[\+\-\*/]|capital\s+of\s+\w+|"
            r"translate\s+(?:.+?\s+)?to\s+\w+|definition\s+of\s+(?!my|your|our)\w+)\b",
            re.I,
        ),
        "general_knowledge",
        0.85,
    ),
    (
        CognitiveIntent.PLANNING,
        re.compile(
            r"\b(help\s+me\s+plan|make\s+(?:me\s+)?a\s+(?:plan|itinerary)|"
            r"brainstorm\s+(?:ideas|options)|draft\s+a\s+(?:roadmap|agenda))\b",
            re.I,
        ),
        "host_planning",
        0.82,
    ),
    (
        CognitiveIntent.REASONING,
        re.compile(
            r"\b(solve\s+(?:this\s+)?(?:equation|puzzle)|prove\s+that|"
            r"logic\s+puzzle|what\s+is\s+\d+\s*(?:plus|minus|times))\b",
            re.I,
        ),
        "pure_reasoning",
        0.8,
    ),
]

# Band B: Specialized cognitive intents (most specific first).
_COGNITIVE_SPECIALIZED: list[_Pattern] = [
    # Identity — assistant vs user (critical: must not swap ownership).
    (
        CognitiveIntent.ASSISTANT_IDENTITY,
        re.compile(
            r"\b(who\s+are\s+you|what(?:'s|\s+is)\s+your\s+name|"
            r"tell\s+me\s+about\s+yourself|introduce\s+yourself|"
            r"your\s+identity|what\s+are\s+you|"
            r"who\s+is\s+(?:the\s+)?assistant)\b",
            re.I,
        ),
        "assistant_identity_cue",
        0.95,
    ),
    (
        CognitiveIntent.USER_IDENTITY,
        re.compile(
            r"\b(who\s+am\s+i|what(?:'s|\s+is)\s+my\s+name|"
            r"my\s+identity|who\s+is\s+(?:the\s+)?user|"
            r"what\s+do\s+you\s+know\s+about\s+(?:who\s+)?i\s+am)\b",
            re.I,
        ),
        "user_identity_cue",
        0.95,
    ),
    (
        CognitiveIntent.IDENTITY,
        re.compile(
            r"\b(identity\s+(?:of|for)|self[- ](?:model|schema))\b",
            re.I,
        ),
        "generic_identity_cue",
        0.85,
    ),
    (
        CognitiveIntent.LEARNING,
        re.compile(
            r"\b(what\s+have\s+you\s+learned|what\s+did\s+you\s+learn|"
            r"what\s+changed\s+in\s+your\s+(?:understanding|beliefs?)|"
            r"what\s+did\s+you\s+(?:pick\s+up|take\s+away)|"
            r"lessons?\s+learned)\b",
            re.I,
        ),
        "learning_cue",
        0.94,
    ),
    (
        CognitiveIntent.CONFIDENCE,
        re.compile(
            r"\b(how\s+certain|how\s+confident|how\s+sure|"
            r"confidence\s+(?:in|about)|(?:your|the)\s+uncertainty|"
            r"are\s+you\s+(?:sure|confident)\b)",
            re.I,
        ),
        "confidence_cue",
        0.93,
    ),
    (
        CognitiveIntent.PREDICTION,
        re.compile(
            r"\b(?:"
            r"what\s+am\s+i\s+likely\b|"
            r"when\s+am\s+i\s+likely\b|"
            r"what\s+is\s+likely\b|"
            r"what(?:'s|\s+is)\s+likely\s+to\s+happen\b|"
            r"if\s+i\b.+\bwhat\s+is\s+likely\b|"
            r"why\s+do\s+you\s+think\s+that\s+is\s+likely\b|"
            r"why\s+(?:is|was)\s+that\s+likely\b|"
            r"based\s+upon\s+memory,?\s+what\s+is\s+likely\b|"
            r"what\s+will\s+happen\b|"
            r"will\s+(?:it|i|we)\b|"
            r"am\s+i\s+(?:going\s+to|likely\s+to)\b"
            r")",
            re.I,
        ),
        "prediction_cue",
        0.95,
    ),
    (
        CognitiveIntent.REFLECTION,
        re.compile(
            r"\b(what\s+do\s+you\s+think\s+about|reflect(?:ion|ing)?\s+on|"
            r"why\s+do\s+you\s+(?:believe|think)(?!\s+that\s+is\s+likely)|"
            r"how\s+do\s+you\s+(?:see|view|interpret)|"
            r"your\s+(?:opinion|reflection)\s+on|"
            r"how\s+has\s+your\s+(?:understanding|knowledge)\s+changed)\b",
            re.I,
        ),
        "reflection_cue",
        0.93,
    ),
    (
        CognitiveIntent.RECONCILIATION,
        re.compile(
            r"\b(conflict(?:ing)?\s+memor|reconcil|"
            r"which\s+(?:is\s+)?(?:true|correct)|contested\s+fact|"
            r"inconsisten(?:t|cy)\s+(?:in\s+)?(?:your\s+)?memor)\b",
            re.I,
        ),
        "reconciliation_cue",
        0.93,
    ),
    (
        CognitiveIntent.REMEMBERING,
        re.compile(
            r"\b(?:"
            r"why\s+(?:did|do|am)\s+i\b|"
            r"why\s+is\s+my\b.+\bbetter\b|"
            r"how\s+are\s+aria\s+and\s+acm\s+related\b|"
            r"how\s+does\s+.+\s+relate\s+to\s+my\s+goal\b|"
            r"how\s+does\s+.+\s+fit\s+into\s+my\s+projects?\b|"
            r"would\s+.+\s+fit\s+my\s+preferences?\b|"
            r"what\s+(?:programming\s+)?language\s+do\s+i\s+prefer\b|"
            r"which\s+(?:of\s+my\s+)?computers?\s+should\s+i\s+use\b|"
            r"which\s+should\s+i\s+use\s+for\b"
            r")",
            re.I,
        ),
        "autobiographical_relational_reasoning_cue",
        0.96,
    ),
    (
        CognitiveIntent.ASSOCIATION,
        re.compile(
            r"\b(how\s+(?:are|is).{0,40}related|associat(?:e|ion)|"
            r"connected\s+to|what\s+links|how\s+do(?:es)?\s+.+\s+relate|"
            r"relationship\s+between)\b",
            re.I,
        ),
        "association_cue",
        0.92,
    ),
    (
        CognitiveIntent.GOAL,
        re.compile(
            r"\b((?:what\s+(?:is|are)|what'?s)\s+(?:my|your|our|"
            r"the)\s+(?:long[- ]?term\s+)?goals?|"
            r"(?:long[- ]?term|primary|current)\s+goal|"
            r"what\s+(?:am\s+i|are\s+we|are\s+you)\s+working\s+(?:toward|towards|on)|"
            r"what(?:'s|\s+is)\s+our\s+(?:plan|objective|aim)|"
            r"our\s+(?:long[- ]?term\s+)?(?:goal|objective))\b",
            re.I,
        ),
        "goal_cue",
        0.94,
    ),
    (
        CognitiveIntent.PROJECT,
        re.compile(
            r"\b((?:what\s+)?projects?\s+(?:are\s+)?(?:we|you|i)\s+"
            r"(?:working\s+on|doing)|"
            r"what\s+projects?\s+am\s+i\s+(?:work(?:ing)?\s+on|building)|"
            r"what\s+ai\s+projects?\b|"
            r"what(?:'s|\s+is)\s+(?:the|our|this)\s+project|"
            r"project\s+(?:history|status|progress)|"
            r"about\s+(?:the|this|our)\s+project|"
            r"where\s+(?:did|do)\s+we\s+leave\s+off|"
            r"what\s+(?:are\s+we|have\s+i\s+been)\s+building)\b",
            re.I,
        ),
        "project_cue",
        0.94,
    ),
    (
        CognitiveIntent.REMEMBERING,
        re.compile(
            r"\b("
            r"what\s+operating\s+system\b|"
            r"what\s+os\s+does\s+my\b|"
            r"what\s+graphics\s+card\b|"
            r"what\s+gpu\b|"
            r"how\s+much\s+ram\b|"
            r"know\s+about\s+my\s+(?:computer|laptop|desktop|ai|setup|machines?)|"
            r"tell\s+me\s+what\s+you\s+know\s+about\s+my\b|"
            r"which\s+computer\b.+\b(?:better|training)|"
            r"better\s+for\s+training|"
            r"do\s+i\s+prefer\s+local|"
            r"local\s+or\s+cloud|"
            r"what\s+kind\s+of\s+responses?\b.+\bdebug|"
            r"summarize\s+what\s+you\s+know\s+about\s+me|"
            r"has\s+my\s+(?:desktop|laptop|computer|hardware|gpu)\b.+\bchanged\b|"
            r"have\s+my\s+(?:ai\s+)?preferences?\s+changed\b|"
            r"how\s+has\s+my\s+(?:ai\s+setup|computer|computers?)\s+changed\b|"
            r"what\s+operating\s+systems?\s+has\s+my\b|"
            r"what\s+projects?\s+have\s+i\s+worked\b|"
            r"tell\s+me\s+about\s+my\s+computers?\b|"
            r"what\s+(?:phone|printer|truck|vehicle|kayak)\s+do\s+i\b"
            r")\b",
            re.I,
        ),
        "semantic_autobiography_cue",
        0.94,
    ),
    (
        CognitiveIntent.REMEMBERING,
        re.compile(
            r"\b((?:show|tell|give|list|what(?:'s|\s+is))\s+(?:me\s+)?(?:the\s+)?evidence|"
            r"evidence\s+for|supporting\s+evidence|what\s+supports)\b",
            re.I,
        ),
        "evidence_cue",
        0.95,
    ),
    (
        CognitiveIntent.REMEMBERING,
        re.compile(
            r"\bwhy\b.+\b(?:favorite|favourite)\b|"
            r"\bwhy\b.+\b(?:isn'?t|is\s+not|no\s+longer)\b.+\bactive\b|"
            r"\bwhy\b.+\bactive\b|"
            r"\bwhat\s+replaced\b",
            re.I,
        ),
        "memory_explanation_cue",
        0.94,
    ),
    (
        CognitiveIntent.PREFERENCE,
        re.compile(
            r"\b(prefer(?:ence|s)?|favorite|favourite|"
            r"what\s+do\s+i\s+like|"
            r"what\s+kind\s+of\s+\w+\s+do\s+i\s+prefer|"
            r"what\s+kind\s+of\s+responses?\s+do\s+i\s+like|"
            r"what\s+do\s+you\s+know\s+about\s+my\s+preferences|"
            r"what(?:'s|\s+is)\s+my\s+favorite|"
            r"do\s+i\s+prefer\b|"
            r"what\s+do\s+i\s+prefer)\b",
            re.I,
        ),
        "preference_cue",
        0.93,
    ),
    (
        CognitiveIntent.AUTOBIOGRAPHY,
        re.compile(
            r"\b(what\s+do\s+you\s+know\s+about\s+me|"
            r"tell\s+me\s+about\s+me|about\s+myself|"
            r"my\s+(?:life|background|story|profile)|"
            r"what\s+have\s+you\s+learned\s+about\s+me|"
            r"summarize\s+what\s+you\s+know\s+about\s+me)\b",
            re.I,
        ),
        "autobiography_cue",
        0.93,
    ),
    (
        CognitiveIntent.EXPERIENCE,
        re.compile(
            r"\b(what\s+happened|what\s+occurred|past\s+experience|"
            r"when\s+did\s+(?:we|i|you)|episodic|"
            r"remember\s+when\s+(?:we|i|you)|"
            r"where\s+did\s+i\s+(?:go|visit)|"
            r"what\s+(?:\w+\s+)?did\s+i\s+(?:buy|clean|install|visit|do|go|get|"
            r"build|finish|start|watch|read|write|cook|fix|"
            r"purchase|order|attend|join|catch|fish|land|harvest|observe)|"
            r"what\s+happened\s+(?:before|after)|"
            r"what\s+happened\s+(?:yesterday|today|last\s+week|"
            r"last\s+month|this\s+morning|last\s+\w+)|"
            r"tell\s+me\s+about\s+(?:buying|cleaning|installing|"
            r"visiting|going|catching|fishing|the\s+(?:kayak|garage|gpu|trip))|"
            r"explain\s+what\s+happened)\b",
            re.I,
        ),
        "experience_cue",
        0.91,
    ),
    (
        CognitiveIntent.HISTORY,
        re.compile(
            r"\b(conversation\s+history|what\s+did\s+we\s+(?:discuss|talk)|"
            r"earlier\s+(?:today|we)|previous\s+(?:chat|session)|"
            r"what\s+were\s+we\s+(?:talking|discussing))\b",
            re.I,
        ),
        "history_cue",
        0.9,
    ),
    (
        CognitiveIntent.DECISION_HISTORY,
        re.compile(
            r"\b(what\s+did\s+we\s+decide|decision\s+history|"
            r"why\s+did\s+we\s+(?:choose|decide)|past\s+decisions?|"
            r"what\s+we\s+decided|explain\s+what\s+we\s+decided)\b",
            re.I,
        ),
        "decision_history_cue",
        0.9,
    ),
    (
        CognitiveIntent.WORKING_MEMORY,
        re.compile(
            r"\b(working\s+memory|what\s+(?:am\s+i|are\s+we)\s+"
            r"(?:holding|keeping)\s+in\s+mind|"
            r"what(?:'s|\s+is)\s+(?:on\s+)?(?:the\s+)?(?:table|agenda)\s+right\s+now)\b",
            re.I,
        ),
        "working_memory_cue",
        0.88,
    ),
    (
        CognitiveIntent.CURRENT_CONTEXT,
        re.compile(
            r"\b(current\s+context|what(?:'s|\s+is)\s+the\s+context|"
            r"where\s+are\s+we\s+(?:in|at)\s+(?:this|the)\s+(?:conversation|task))\b",
            re.I,
        ),
        "current_context_cue",
        0.88,
    ),
    (
        CognitiveIntent.PATTERN,
        re.compile(
            r"\b(?:"
            r"what\s+(?:patterns?|habits?)\s+(?:do\s+)?(?:you|i|we)|"
            r"what\s+do\s+you\s+usually|tend\s+to|"
            r"in\s+general\s+(?:i|you)\s+|"
            # Declarative recurring-experience teachings (Prediction evidence)
            r"every\s+time\s+i\b|"
            r"whenever\s+i\b|"
            r"every\s+(?:saturday|sunday|monday|tuesday|wednesday|thursday|friday|weekend)\b|"
            r"i\s+usually\b|"
            r"it\s+has\s+rained\s+every\s+day\b|"
            r"\w+\s+sometimes\s+helps?\s+me\b|"
            r"(?:coffee|tea|alcohol)\s+causes?\b"
            r")",
            re.I,
        ),
        "pattern_cue",
        0.88,
    ),
    (
        CognitiveIntent.CONCEPT,
        re.compile(
            r"\b(what\s+does\s+.+\s+mean\s+to\s+you|"
            r"concept\s+of|how\s+do\s+you\s+(?:define|understand)|"
            r"your\s+(?:understanding|concept)\s+of)\b",
            re.I,
        ),
        "concept_cue",
        0.88,
    ),
    (
        CognitiveIntent.LONG_TERM_MEMORY,
        re.compile(
            r"\b(long[- ]term\s+memor(?:y|ies)|what\s+do\s+you\s+"
            r"(?:retain|keep)\s+(?:over\s+time|long[- ]term))\b",
            re.I,
        ),
        "long_term_memory_cue",
        0.87,
    ),
    (
        CognitiveIntent.REMEMBERING,
        re.compile(
            r"\b(what\s+do\s+you\s+remember|do\s+you\s+remember|"
            r"recall|what\s+do\s+you\s+know\s+about|"
            r"what(?:'s|\s+is)\s+my\b|remember\s+(?:that|when|my))\b",
            re.I,
        ),
        "remembering_cue",
        0.92,
    ),
]

# Soft autobiographical / cognitive ownership cues (band C).
_SELF_OR_SHARED = re.compile(
    r"\b(i|me|my|mine|you|your|yours|we|us|our|ours|"
    r"myself|yourself|ourselves)\b",
    re.I,
)
_COGNITIVE_VERB = re.compile(
    r"\b(remember|recall|know|learned?|believe|think|decid\w*|"
    r"prefer|goal|project|identity|associat|"
    r"confident|certain|experienc|understand)\w*\b",
    re.I,
)
_INTERROGATIVE = re.compile(
    r"^\s*(who|what|when|where|why|how)\b",
    re.I,
)

_CONFIDENCE_HIGH = 0.85
_CONFIDENCE_SPECIALIZED = 0.8
_UNCERTAIN_FLOOR = 0.45


def classify_memory_request(text: str) -> MemoryRequestClassification:
    """Classify cognitive intent and whether Memory Authority must own the answer.

    Policy:
    1. Explicit non-cognitive task patterns → not a memory request.
    2. Specialized cognitive pattern → memory request with that intent.
    3. Soft cognitive + self/shared cues without specialist match →
       ``GENERAL_MEMORY`` or ``UNCERTAIN`` (still memory request — no LM ownership).
    4. No signals → ``NOT_MEMORY``.
    """
    raw = (text or "").strip()
    if not raw:
        return MemoryRequestClassification(
            is_memory_request=False,
            intent=CognitiveIntent.NOT_MEMORY,
            confidence=1.0,
            matched_signals=("empty",),
            reason="empty_request",
            uncertain=False,
            ownership_hint="none",
        )

    for intent, pattern, signal, conf in _NON_COGNITIVE:
        if pattern.search(raw):
            return MemoryRequestClassification(
                is_memory_request=False,
                intent=intent,
                confidence=conf,
                matched_signals=(signal,),
                reason=f"matched_{intent.value}",
                uncertain=False,
                ownership_hint="none",
            )

    for intent, pattern, signal, conf in _COGNITIVE_SPECIALIZED:
        if pattern.search(raw):
            return MemoryRequestClassification(
                is_memory_request=True,
                intent=intent,
                confidence=conf,
                matched_signals=(signal,),
                reason=f"matched_{intent.value}",
                uncertain=False,
                ownership_hint=_hint_for(intent),
            )

    # Soft cognitive conservation: do not silent-bypass autobiographical questions.
    signals: list[str] = []
    has_self = bool(_SELF_OR_SHARED.search(raw))
    has_cog = bool(_COGNITIVE_VERB.search(raw))
    has_q = bool(_INTERROGATIVE.search(raw))

    if has_self:
        signals.append("self_or_shared_referent")
    if has_cog:
        signals.append("cognitive_verb")
    if has_q:
        signals.append("interrogative")

    if has_self and (has_cog or has_q):
        # Likely cognitive; specialized intent unknown → GENERAL_MEMORY with uncertainty.
        conf = 0.72 if (has_cog and has_q) else 0.62
        uncertain = conf < _CONFIDENCE_SPECIALIZED
        return MemoryRequestClassification(
            is_memory_request=True,
            intent=CognitiveIntent.GENERAL_MEMORY if conf >= 0.65 else CognitiveIntent.UNCERTAIN,
            confidence=conf,
            matched_signals=tuple(signals),
            reason="soft_cognitive_self_referent",
            uncertain=uncertain,
            ownership_hint="remembering",
        )

    if has_q and has_cog:
        return MemoryRequestClassification(
            is_memory_request=True,
            intent=CognitiveIntent.GENERAL_MEMORY,
            confidence=0.68,
            matched_signals=tuple(signals) or ("interrogative_cognitive",),
            reason="soft_cognitive_interrogative",
            uncertain=True,
            ownership_hint="remembering",
        )

    if has_q:
        # Bare interrogative without self/cognitive cues — likely general knowledge.
        return MemoryRequestClassification(
            is_memory_request=False,
            intent=CognitiveIntent.GENERAL_KNOWLEDGE,
            confidence=0.55,
            matched_signals=("interrogative_only",),
            reason="interrogative_without_cognitive_or_self_cues",
            uncertain=True,
            ownership_hint="none",
        )

    return MemoryRequestClassification(
        is_memory_request=False,
        intent=CognitiveIntent.NOT_MEMORY,
        confidence=0.6,
        matched_signals=("no_memory_signal",),
        reason="no_memory_classification",
        uncertain=False,
        ownership_hint="none",
    )


def classify_request(text: str) -> MemoryRequestClassification:
    """Public alias — every request enters Cognitive Intent Classification."""
    return classify_memory_request(text)


def is_cognitive_intent(intent: CognitiveIntent | str) -> bool:
    if isinstance(intent, str):
        try:
            intent = CognitiveIntent(intent)
        except ValueError:
            return False
    return intent in COGNITIVE_INTENTS


def is_non_cognitive_intent(intent: CognitiveIntent | str) -> bool:
    if isinstance(intent, str):
        try:
            intent = CognitiveIntent(intent)
        except ValueError:
            return False
    return intent in NON_COGNITIVE_INTENTS


_OWNERSHIP_HINTS: dict[CognitiveIntent, str] = {
    CognitiveIntent.ASSISTANT_IDENTITY: "identity",
    CognitiveIntent.USER_IDENTITY: "identity",
    CognitiveIntent.IDENTITY: "identity",
    CognitiveIntent.AUTOBIOGRAPHY: "remembering",
    CognitiveIntent.EXPERIENCE: "remembering",
    CognitiveIntent.REMEMBERING: "remembering",
    CognitiveIntent.LONG_TERM_MEMORY: "remembering",
    CognitiveIntent.WORKING_MEMORY: "working_memory",
    CognitiveIntent.CURRENT_CONTEXT: "context",
    CognitiveIntent.HISTORY: "remembering",
    CognitiveIntent.DECISION_HISTORY: "remembering",
    CognitiveIntent.PROJECT: "remembering",
    CognitiveIntent.PATTERN: "remembering",
    CognitiveIntent.GENERAL_MEMORY: "remembering",
    CognitiveIntent.CONCEPT: "concepts",
    CognitiveIntent.ASSOCIATION: "associations",
    CognitiveIntent.PREFERENCE: "remembering",
    CognitiveIntent.GOAL: "goals",
    CognitiveIntent.PREDICTION: "prediction",
    CognitiveIntent.REFLECTION: "reflection",
    CognitiveIntent.LEARNING: "learning",
    CognitiveIntent.CONFIDENCE: "confidence",
    CognitiveIntent.RECONCILIATION: "reconciliation",
    CognitiveIntent.UNCERTAIN: "remembering",
}


def _hint_for(intent: CognitiveIntent) -> str:
    return _OWNERSHIP_HINTS.get(intent, "remembering")
