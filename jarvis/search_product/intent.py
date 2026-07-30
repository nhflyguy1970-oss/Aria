"""Lightweight intent classification for corpus routing."""

from __future__ import annotations

import re
from typing import Any

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("provider_health", re.compile(r"\b(provider health|stream.?idle|ollama (down|stuck|timeout)|model (crash|timeout)|provider (timeout|recover|restart))\b", re.I)),
    ("notifications", re.compile(r"\b(notification|notifications|activity center|unread alerts|what.?s wrong)\b", re.I)),
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
    ("flytying", re.compile(r"\b(fly|pattern|hackle|hook|tying|nymph|streamer)\b", re.I)),
    ("journal", re.compile(r"\b(journal|bujo|bullet|daily log|reflection)\b", re.I)),
    ("automation", re.compile(r"\b(automation|workflow|trigger|cron|n8n)\b", re.I)),
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


def select_corpora(
    intent: dict[str, Any],
    *,
    facets: list[str] | None,
    enabled: set[str],
) -> list[str]:
    """Pick corpora to query. Explicit facets win; else intent; else everything enabled."""
    if facets:
        cleaned = [f for f in facets if f and f != "everything"]
        if not cleaned or "everything" in facets:
            return sorted(enabled)
        return [f for f in cleaned if f in enabled or f == "web"]
    intents = intent.get("intents") or ["everything"]
    if intents == ["everything"] or intent.get("primary") == "everything":
        # Default federated set (always-on cores); opt-in extras only if enabled
        core = ["documents", "memory", "projects", "journal", "code", "learned", "graph", "connections", "audio", "settings", "dashboard", "layouts", "notifications"]
        return [c for c in core if c in enabled] or sorted(enabled)
    picked = [i for i in intents if i in enabled or i == "web"]
    # Always include memory for AI OS unless explicitly facet-limited
    if "memory" in enabled and "memory" not in picked and "web" not in (facets or []):
        picked.insert(0, "memory")
    return picked or sorted(enabled)
