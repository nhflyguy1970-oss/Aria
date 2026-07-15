"""Cognitive Intent Taxonomy — host-, model-, and provider-independent.

Grounded in cognitive science:

- **Episodic / autobiographical retrieval** (Tulving; Conway & Pleydell-Pearce)
- **Semantic retrieval** (Tulving)
- **Self / identity models** (self-schema, autobiographical identity)
- **Goals & executive attention** (Baddeley working memory; goals as memory bias)
- **Metacognition & source monitoring** (Nelson & Narens; Johnson et al.)
- **Associative / semantic networks** (Collins & Loftus)

Categories below are the ACM normative taxonomy for Cognitive Intent
Classification (D039). Non-cognitive intents are still *classified* so the
language model never determines cognitive ownership by default.
"""

from __future__ import annotations

from enum import StrEnum


class CognitiveIntent(StrEnum):
    """Which cognitive (or host) surface owns answering a request.

    Exactly one primary owner is assigned by Cognitive Routing. Supporting
    organs may contribute. ``UNCERTAIN`` is cognitive-conservative: do not
    silently hand ownership to a language model.
    """

    # --- Identity & self --------------------------------------------------------
    ASSISTANT_IDENTITY = "assistant_identity"
    USER_IDENTITY = "user_identity"
    IDENTITY = "identity"  # generic identity (prefer specialized forms)
    AUTOBIOGRAPHY = "autobiography"

    # --- Memory retrieval -------------------------------------------------------
    EXPERIENCE = "experience"
    REMEMBERING = "remembering"
    LONG_TERM_MEMORY = "long_term_memory"
    WORKING_MEMORY = "working_memory"
    CURRENT_CONTEXT = "current_context"
    HISTORY = "history"
    DECISION_HISTORY = "decision_history"
    PROJECT = "project"
    PATTERN = "pattern"
    GENERAL_MEMORY = "general_memory"

    # --- Semantic / relational cognition ----------------------------------------
    CONCEPT = "concept"
    ASSOCIATION = "association"
    PREFERENCE = "preference"
    GOAL = "goal"

    # --- Metacognition ----------------------------------------------------------
    REFLECTION = "reflection"
    LEARNING = "learning"
    CONFIDENCE = "confidence"
    RECONCILIATION = "reconciliation"

    # --- Non-cognitive host surfaces (still classified by ACM) ------------------
    PROCEDURAL = "procedural"
    REASONING = "reasoning"
    PLANNING = "planning"
    TOOL_REQUEST = "tool_request"
    GENERAL_KNOWLEDGE = "general_knowledge"
    CONVERSATION_MANAGEMENT = "conversation_management"

    # --- Uncertainty / bypass ---------------------------------------------------
    UNCERTAIN = "uncertain"
    NOT_MEMORY = "not_memory"


# Cognitive intents that require Memory Authority before any LM generation.
COGNITIVE_INTENTS: frozenset[CognitiveIntent] = frozenset(
    {
        CognitiveIntent.ASSISTANT_IDENTITY,
        CognitiveIntent.USER_IDENTITY,
        CognitiveIntent.IDENTITY,
        CognitiveIntent.AUTOBIOGRAPHY,
        CognitiveIntent.EXPERIENCE,
        CognitiveIntent.REMEMBERING,
        CognitiveIntent.LONG_TERM_MEMORY,
        CognitiveIntent.WORKING_MEMORY,
        CognitiveIntent.CURRENT_CONTEXT,
        CognitiveIntent.HISTORY,
        CognitiveIntent.DECISION_HISTORY,
        CognitiveIntent.PROJECT,
        CognitiveIntent.PATTERN,
        CognitiveIntent.GENERAL_MEMORY,
        CognitiveIntent.CONCEPT,
        CognitiveIntent.ASSOCIATION,
        CognitiveIntent.PREFERENCE,
        CognitiveIntent.GOAL,
        CognitiveIntent.REFLECTION,
        CognitiveIntent.LEARNING,
        CognitiveIntent.CONFIDENCE,
        CognitiveIntent.RECONCILIATION,
        CognitiveIntent.UNCERTAIN,
    }
)

# Host / LM may generate (never becomes memory without encode gates).
NON_COGNITIVE_INTENTS: frozenset[CognitiveIntent] = frozenset(
    {
        CognitiveIntent.PROCEDURAL,
        CognitiveIntent.REASONING,
        CognitiveIntent.PLANNING,
        CognitiveIntent.TOOL_REQUEST,
        CognitiveIntent.GENERAL_KNOWLEDGE,
        CognitiveIntent.CONVERSATION_MANAGEMENT,
        CognitiveIntent.NOT_MEMORY,
    }
)

# Canonical primary organ names (routing vocabulary).
ORGAN_IDENTITY = "identity"
ORGAN_REMEMBERING = "remembering"
ORGAN_LEARNING = "learning"
ORGAN_REFLECTION = "reflection"
ORGAN_ASSOCIATIONS = "associations"
ORGAN_CONFIDENCE = "confidence"
ORGAN_RECONCILIATION = "reconciliation"
ORGAN_CONCEPTS = "concepts"
ORGAN_EXPERIENCES = "experiences"
ORGAN_WORKING = "working_memory"
ORGAN_CONTEXT = "context"
ORGAN_GOALS = "goals"
ORGAN_NONE = "none"  # non-cognitive — host owns execution

# Research-evaluated but deferred for this correction (documented only).
DEFERRED_INTENTS: tuple[str, ...] = (
    "simulation",
    "prediction",
    "analogy",
    "creativity",
    "emotion",
    "social_model",
    "temporal_reasoning",
)
