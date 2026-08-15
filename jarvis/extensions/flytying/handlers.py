"""Chat/action handlers for Fly Tying fast-path routes."""

from __future__ import annotations

import re
from typing import Any

from jarvis.handlers.registry import register_action
from jarvis.response import err as _err
from jarvis.response import ok as _ok


@register_action("fly_status", module="flytying", description="Fly tying / Blackfly library status")
def fly_status(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.flytying import bridge

    st = bridge.status()
    loaded = st.get("blackfly_loaded") or st.get("loaded")
    count = st.get("recipe_count") or st.get("record_count") or 0
    potd = st.get("pattern_of_the_day") or {}
    lines = [
        f"Fly Tying library: {'loaded' if loaded else 'unavailable'} · {count} patterns",
        st.get("index_note") or "",
    ]
    if potd.get("ok") and potd.get("name"):
        lines.append(f"Pattern of the day: {potd.get('name')}")
    return _ok(
        "\n".join(ln for ln in lines if ln),
        module="flytying",
        open_view="flytying",
        status=st,
    )


@register_action("fly_gold_build", module="flytying", description="Rebuild Fly Tying gold index")
def fly_gold_build(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.flytying import bridge

    result = bridge.build_gold()
    if not result.get("ok"):
        return _err(result.get("message") or "Gold build failed", module="flytying")
    return _ok(result.get("message") or "Gold index rebuilt", module="flytying", **result)


@register_action("fly_recipe", module="flytying", description="Show a fly recipe / pattern")
def fly_recipe(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.flytying import bridge

    name = (params.get("name") or message or "").strip()
    if not name:
        return _err("Which pattern? e.g. show recipe for Adams", module="flytying")
    row = bridge.get_recipe(name)
    if not row:
        hits = bridge.search_recipes(name, limit=5) or []
        if not hits:
            return _err(f"No pattern matched “{name}”", module="flytying", open_view="flytying")
        names = ", ".join(str(h.get("name") or h.get("fly_name") or "") for h in hits[:5])
        return _ok(
            f"Closest patterns: {names}\nOpen **Fly tying** to browse.",
            module="flytying",
            open_view="flytying",
            results=hits,
        )
    text = row.get("formatted") or row.get("name") or name
    return _ok(
        str(text)[:4000],
        module="flytying",
        open_view="flytying",
        recipe_id=row.get("recipe_id") or row.get("id") or name,
        select_pattern=row.get("recipe_id") or row.get("name") or name,
    )


@register_action("fly_ask", module="flytying", description="Ask a fly-tying question (RAG)")
def fly_ask(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.flytying import bridge
    from jarvis.flytying.search import unified_search

    question = (params.get("question") or message or "").strip()
    if not question:
        return _err("What fly-tying question?", module="flytying")
    result = bridge.ask_fly_tying(question)
    answer = (result.get("answer") or result.get("message") or "").strip()
    recipes = result.get("recipes") or []
    no_hit = (not result.get("ok")) or (not recipes) or bool(
        re.search(
            r"\b(no\b.+\b(pattern|recipe|match|excerpt)|not (?:in|found)|couldn'?t find|don't have)\b",
            answer,
            re.I,
        )
    )
    if no_hit:
        # Don't dead-end Jeff — fall back to the pattern library he already owns.
        # Full natural questions often miss; extract a short library query.
        q_short = re.sub(
            r"\b(i need|what should i tie|can you|please|recommend|with|olive flash|"
            r"how (?:do|to) i tie|tie me|a |an |the )\b",
            " ",
            question,
            flags=re.I,
        )
        q_short = re.sub(r"[—\-\?\!.,]+", " ", q_short)
        q_short = re.sub(r"\s+", " ", q_short).strip()
        # Prefer distinctive fly tokens if present
        m = re.search(
            r"\b((?:woolly|wooly)\s+bugger|adams|elk hair|pheasant|cdc|nymph|streamer|"
            r"hopper|caddis|midge|leech|gonga)\b.*",
            question,
            re.I,
        )
        if m:
            q_short = m.group(0)
            q_short = re.sub(r"[—\-\?\!.,]+", " ", q_short)
            q_short = re.sub(r"\s+", " ", q_short).strip()[:60]
        for attempt in (q_short, "woolly bugger" if "bugger" in question.lower() else q_short):
            if not attempt:
                continue
            payload = unified_search(attempt, limit=8)
            rows = (payload or {}).get("results") or []
            if rows:
                lines = [
                    f"- {r.get('name') or r.get('fly_name')} ({r.get('type') or '?'})"
                    for r in rows[:8]
                ]
                return _ok(
                    "Closest patterns in your library:\n" + "\n".join(lines),
                    module="flytying",
                    open_view="flytying",
                    results=rows,
                    search_mode=(payload or {}).get("search_mode"),
                )
        if not result.get("ok"):
            return _err(result.get("message") or "Ask failed", module="flytying", open_view="flytying")
    return _ok(
        answer,
        module="flytying",
        open_view="flytying",
        recipes=recipes,
    )


@register_action("fly_search", module="flytying", description="Search fly patterns")
def fly_search(assistant, params: dict, message: str = "") -> dict[str, Any]:
    from jarvis.flytying.search import unified_search

    query = (params.get("query") or message or "").strip()
    payload = unified_search(query, limit=8)
    if not payload.get("ok"):
        return _err(payload.get("message") or "Search unavailable", module="flytying", open_view="flytying")
    rows = payload.get("results") or []
    if not rows:
        return _ok("No patterns found.", module="flytying", open_view="flytying")
    lines = [f"- {r.get('name') or r.get('fly_name')} ({r.get('type') or '?'})" for r in rows[:8]]
    return _ok(
        "Patterns:\n" + "\n".join(lines),
        module="flytying",
        open_view="flytying",
        results=rows,
        search_mode=payload.get("search_mode"),
    )
