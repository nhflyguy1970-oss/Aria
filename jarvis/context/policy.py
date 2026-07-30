"""Context assembly policy — lazy retrieval without removing capabilities.

Subsystems stay available; they only run when the request actually needs them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Greetings / thanks / trivial chat — almost no retrieval.
_GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|yo|sup|howdy|good\s+(morning|afternoon|evening)|"
    r"thanks?(?:\s+you)?|thx|ty|cheers|bye|goodbye|see\s+ya)[\s!.?]*$",
    re.I,
)

# Trivial arithmetic / jokes — no external grounding.
_TRIVIAL_RE = re.compile(
    r"^\s*(?:what(?:'?s|\s+is)\s+)?\d+\s*[\+\-\*/x×÷]\s*\d+\s*[?.!]?\s*$|"
    r"^\s*what\s+is\s+\d+\s*(?:\+|plus)\s*\d+\s*[?.!]?\s*$|"
    r"^\s*(?:tell\s+me\s+)?(?:a\s+)?joke\s*[?.!]*\s*$",
    re.I,
)

# Clock / calendar facts — local datetime only; not weather/docs/planner.
_CLOCK_RE = re.compile(
    r"\bwhat\s+day\s+is\s+(?:it|today)\b|"
    r"\bwhat(?:'?s|\s+is)\s+today'?s\s+date\b|"
    r"\bwhat\s+is\s+the\s+(?:date|day|time)\b|"
    r"\bwhat(?:'?s|\s+is)\s+the\s+(?:date|time)\s+today\b|"
    r"\bwhat\s+time\s+is\s+it\b|"
    r"\bday\s+of\s+the\s+week\b",
    re.I,
)

_WEATHER_RE = re.compile(
    r"\b(weather|forecast|temperature|temps?|humidity|rain(?:y|ing)?|snow(?:y|ing)?|"
    r"windy|cloudy|sunny|umbrella|how\s+(?:hot|cold|warm))\b",
    re.I,
)

_TASK_RE = re.compile(
    r"\b(journal|task|todo|to-do|priorit(?:y|ies|ize)|what(?:'s| is) on my plate|"
    r"open tasks|my\s+schedule|planner|calendar|schedule|meeting|appointment|"
    r"remind(?:er|me)?)\b",
    re.I,
)

_DOC_RE = re.compile(
    r"\b(document|documents|pdf|docx?|manual|warranty|library|rag|"
    r"summarize\s+(?:this|the)\s+(?:file|doc|pdf)|attached\s+file)\b",
    re.I,
)

_MEMORY_RE = re.compile(
    r"\b(remember|recall|what\s+do\s+you\s+know\s+about\s+me|my\s+(?:name|favorite)|"
    r"search\s+(?:my\s+)?memory|forget)\b",
    re.I,
)

_PROJECT_RE = re.compile(
    r"\b(codebase|repository|\brepo\b|\bgit\b|pull request|\bpr\b|workspace|workstation|"
    r"commit|branch|refactor|stack trace|debug this|in this project)\b",
    re.I,
)

_RELATIONSHIP_RE = re.compile(
    r"\b(who is|who's|knows|friend|colleague|connection|introduced|met with)\b",
    re.I,
)

_KNOWLEDGE_TOPIC_RE = re.compile(
    r"\b(knowledge base|saved topic|my notes|what (?:have|did) i (?:learn|save)|"
    r"learnings?\s+on|topic\s+on)\b",
    re.I,
)

# Session-stable caches (invalidate only when process restarts / explicit clear).
_STABLE: dict[str, Any] = {}


@dataclass(frozen=True)
class ContextNeeds:
    """Which context subsystems to run for this turn."""

    lightweight: bool
    memory: bool
    planning_tasks: bool
    weather: bool
    knowledge_topics: bool
    documents: bool
    web_search: bool
    project_extras: bool
    flytying: bool
    relationships: bool
    local_clock: bool


def is_lightweight_chat(message: str) -> bool:
    text = (message or "").strip()
    if not text or len(text) > 120:
        return False
    if _GREETING_RE.match(text) or _TRIVIAL_RE.match(text) or _CLOCK_RE.search(text):
        return True
    return False


def needs_weather(message: str) -> bool:
    return bool(_WEATHER_RE.search(message or ""))


def needs_planner_tasks(message: str) -> bool:
    return bool(_TASK_RE.search(message or ""))


def needs_documents(message: str) -> bool:
    return bool(_DOC_RE.search(message or ""))


def needs_memory_lookup(message: str) -> bool:
    if is_lightweight_chat(message) and not _MEMORY_RE.search(message or ""):
        return False
    return True


def needs_project_extras(message: str) -> bool:
    return bool(_PROJECT_RE.search(message or ""))


def needs_relationships(message: str) -> bool:
    return bool(_RELATIONSHIP_RE.search(message or ""))


def context_needs(message: str) -> ContextNeeds:
    text = (message or "").strip()
    light = is_lightweight_chat(text)
    weather = needs_weather(text)
    tasks = needs_planner_tasks(text)
    docs = needs_documents(text)
    clock = bool(_CLOCK_RE.search(text))
    memory_cue = bool(_MEMORY_RE.search(text))

    if light:
        return ContextNeeds(
            lightweight=True,
            memory=False,
            planning_tasks=False,
            weather=False,
            knowledge_topics=False,
            documents=False,
            web_search=False,
            project_extras=False,
            flytying=False,
            relationships=False,
            local_clock=clock,
        )

    # Narrow intents: only the subsystem that answers the question.
    if weather and not tasks and not docs and not memory_cue:
        return ContextNeeds(
            lightweight=False,
            memory=False,
            planning_tasks=False,
            weather=True,
            knowledge_topics=False,
            documents=False,
            web_search=False,
            project_extras=False,
            flytying=False,
            relationships=False,
            local_clock=False,
        )

    if tasks and not weather and not docs and not memory_cue:
        return ContextNeeds(
            lightweight=False,
            memory=False,
            planning_tasks=True,
            weather=False,
            knowledge_topics=False,
            documents=False,
            web_search=False,
            project_extras=False,
            flytying=False,
            relationships=False,
            local_clock=False,
        )

    if docs and not weather and not tasks:
        return ContextNeeds(
            lightweight=False,
            memory=True,
            planning_tasks=False,
            weather=False,
            knowledge_topics=False,
            documents=True,
            web_search=False,
            project_extras=False,
            flytying=False,
            relationships=False,
            local_clock=False,
        )

    try:
        from jarvis.flytying.knowledge import is_flytying_chat

        fly = is_flytying_chat(text)
    except Exception:
        fly = False

    web = False
    try:
        from jarvis import web_search
        from jarvis.profiles import web_search_disabled

        if (
            not web_search_disabled()
            and web_search.auto_search_enabled()
            and web_search.should_auto_search(text)
        ):
            web = True
    except Exception:
        web = False

    return ContextNeeds(
        lightweight=False,
        memory=needs_memory_lookup(text),
        planning_tasks=tasks,
        weather=weather,
        knowledge_topics=bool(_KNOWLEDGE_TOPIC_RE.search(text)),
        documents=docs,
        web_search=web,
        project_extras=needs_project_extras(text),
        flytying=fly,
        relationships=needs_relationships(text),
        local_clock=False,
    )


def local_clock_line() -> str:
    now = datetime.now().astimezone()
    return f"Local clock: {now.strftime('%A, %B %d, %Y %H:%M %Z').strip()}"


def cached_language_hint(message: str) -> str:
    """Language lock is cheap; cache English default across turns."""
    from jarvis.lang_util import detect_text_language, language_reply_hint

    lang = detect_text_language(message) or "en"
    key = f"lang:{lang}"
    if key not in _STABLE:
        _STABLE[key] = language_reply_hint(lang) or ""
    return str(_STABLE[key] or "")


def clear_stable_cache() -> None:
    _STABLE.clear()


# Last assembly inventory for diagnostics / tests (no secrets).
_LAST_INVENTORY: dict[str, Any] = {}


def record_inventory(inventory: dict[str, Any]) -> None:
    global _LAST_INVENTORY
    _LAST_INVENTORY = dict(inventory)


def last_inventory() -> dict[str, Any]:
    return dict(_LAST_INVENTORY)
