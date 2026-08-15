"""Lightweight intent classification for corpus routing."""

from __future__ import annotations

import re
from typing import Any

from jarvis.search_product.terminology import FACETS

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("provider_health", re.compile(r"\b(provider health|stream.?idle|ollama (down|stuck|timeout)|model (crash|timeout)|provider (timeout|recover|restart))\b", re.I)),
    ("notifications", re.compile(r"\b(notification|notifications|activity center|unread alerts|what.?s wrong)\b", re.I)),
    ("health", re.compile(r"\b(blood pressure|blood sugar|medication|medications|\bmeds\b|supplement|allerg(?:y|ies)|a1c|cholesterol|personal health|phr|health record|vaccin|health timeline|wellness coach|doctor visit|workout|second opinion)\b", re.I)),
    ("layouts", re.compile(r"\b(layout|layouts|shell layout|apply coding layout|starter layout)\b", re.I)),
    ("dashboard", re.compile(r"\b(home dashboard|daily brief|attention strip|home screen|dashboard home|ctrl\+home)\b", re.I)),
    ("settings", re.compile(r"\b(settings|preference|theme|accent|pin lock|whisper|speak replies)\b", re.I)),
    ("web", re.compile(r"\b(latest|news|current|today|online|google|web|internet|look up)\b", re.I)),
    ("code", re.compile(r"\b(code|function|class|import|repo|git|python|typescript|def |grep|symbol)\b", re.I)),
    ("memory", re.compile(r"\b(remember|we discussed|conversation|said|told you|recall)\b", re.I)),
    ("documents", re.compile(r"\b(pdf|docx|document|warranty|manual|paper|file)\b", re.I)),
    ("graph", re.compile(r"\b(related to|connection|entity|relationship|who is|linked)\b", re.I)),
    ("home_assistant", re.compile(r"\b(light|switch|sensor|home assistant|ha entity|thermostat|climate)\b", re.I)),
    ("media", re.compile(r"\b(image|photo|gallery|transcript|audio|recording|video)\b", re.I)),
    ("planner", re.compile(r"\b(task|todo|planner|due|deadline)\b", re.I)),
    ("calendar", re.compile(r"\b(calendar|schedule|meeting|appointment|work block)\b", re.I)),
    ("projects", re.compile(r"\bprojects?\b", re.I)),
    ("flytying", re.compile(r"\b(fly|pattern|hackle|hook|tying|nymph|streamer)\b", re.I)),
    ("journal", re.compile(r"\b(journal|bujo|bullet|daily log|reflection)\b", re.I)),
    # Require automation-specific cues — bare "workflow" matches project titles like "QA Workflow".
    ("automation", re.compile(r"\b(automation|n8n|cron job|triggered workflow|workflow rule|workflow trigger)\b", re.I)),
    ("audio", re.compile(r"\b(transcript|podcast|recording|audio)\b", re.I)),
    ("gallery", re.compile(r"\b(gallery|comfy|image prompt|sdxl|flux)\b", re.I)),
]

# Map media → concrete facets
_MEDIA_EXPAND = ("gallery", "audio")


def classify_intent(query: str) -> dict[str, Any]:
    q = (query or "").strip()
    matched: list[str] = []
    for name, pat in _PATTERNS:
        if pat.search(q):
            matched.append(name)
    expanded: list[str] = []
    for m in matched:
        if m == "media":
            expanded.extend(_MEDIA_EXPAND)
        elif m == "graph":
            expanded.extend(["graph", "connections"])
        else:
            expanded.append(m)
    # de-dupe preserve order
    seen: set[str] = set()
    intents: list[str] = []
    for x in expanded:
        if x not in seen:
            seen.add(x)
            intents.append(x)
    primary = intents[0] if intents else "everything"
    return {
        "query": q,
        "primary": primary,
        "intents": intents or ["everything"],
        "answer_leaning": bool(
            re.search(r"\b(what|who|when|where|why|how|explain|summarize|tell me)\b", q, re.I)
        ),
        "browse_leaning": bool(re.search(r"\b(find|list|show|search|locate)\b", q, re.I)),
    }


# Generic "everything" must not fan out to every heavy corpus (web/code/automation…).
# Measured: documents+code+web+automation alone ≫ 4s each; parallel wall ~5–9s.
# Explicit facets or matched intents still reach those corpora.
_FAST_EVERYTHING: tuple[str, ...] = (
    "memory",
    "journal",
    "chat",
    "planner",
    "calendar",
    "projects",
    "settings",
    "notifications",
    "health",
    "dashboard",
    "layouts",
    "learned",
    # Local recipe index — pattern-name searches (e.g. "Adams") must hit Fly
    # without requiring the owner to type "fly" / open the Fly facet.
    "flytying",
)


def select_corpora(
    intent: dict[str, Any],
    *,
    facets: list[str] | None,
    enabled: set[str],
) -> list[str]:
    """Pick corpora to query. Explicit facets win; else intent; else a fast local set."""
    if facets:
        cleaned = [f for f in facets if f and f != "everything"]
        if not cleaned or "everything" in facets:
            # Explicit "everything" facet = full federation (operator choice).
            if "everything" in (facets or []):
                return [c for c in FACETS if c != "everything" and c in enabled] or sorted(enabled)
            return [c for c in _FAST_EVERYTHING if c in enabled] or sorted(enabled)
        return [f for f in cleaned if f in enabled or f == "web"]
    intents = intent.get("intents") or ["everything"]
    if intents == ["everything"] or intent.get("primary") == "everything":
        return [c for c in _FAST_EVERYTHING if c in enabled] or [
            c for c in FACETS if c != "everything" and c in enabled
        ] or sorted(enabled)
    picked = [i for i in intents if i in enabled or i == "web"]
    # Always include memory for AI OS unless explicitly facet-limited
    if "memory" in enabled and "memory" not in picked and "web" not in (facets or []):
        picked.insert(0, "memory")
    return picked or [c for c in _FAST_EVERYTHING if c in enabled] or sorted(enabled)
