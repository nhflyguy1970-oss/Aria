"""Memory action handlers."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _namespace(assistant) -> str:
    from jarvis.config import load_memory_namespace
    from jarvis.memory_context import resolve_project_namespace

    ns = assistant.session.memory_namespace
    if ns and ns != "default":
        return ns
    if load_memory_namespace() == "auto":
        return resolve_project_namespace()
    return load_memory_namespace()


@register_action("remember", module="memory", description="Store a fact in memory")
def remember(assistant, params: dict, message: str) -> dict:
    text = (params.get("text") or message or "").strip()
    text = re.sub(
        r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
        "",
        text,
        flags=re.I,
    ).strip()
    if not text:
        return err("What should I remember?")
    ns = params.get("namespace") or _namespace(assistant)
    entry = assistant.memory.add(text, entry_type="fact", namespace=ns)
    assistant.session.note_module("memory")
    assistant.refresh_system_prompt()
    return ok(f"Got it — I'll remember:\n\n{entry['content']}", module="memory", remembered=entry["content"])


@register_action("recall", module="memory", description="Recall memories")
def recall(assistant, params: dict, message: str) -> dict:
    query = (params.get("query") or message or "").strip()
    query = re.sub(r"^(please\s+)?(what do you remember|recall|my memories)\s*(about\s+)?", "", query, flags=re.I).strip()
    if not query:
        query = message
    hits = assistant.memory.search(query, limit=12, namespace=_namespace(assistant))
    if not hits:
        return ok("I don't have memories matching that yet.", module="memory")
    lines = [f"• {h.get('content', '')}" for h in hits]
    return ok("Here's what I remember:\n\n" + "\n".join(lines), module="memory")


@register_action("memory_search", module="memory", description="Search memory")
def memory_search(assistant, params: dict, message: str) -> dict:
    query = (params.get("query") or "").strip()
    if not query:
        query = re.sub(
            r"^(please\s+)?(search my memory|search memory|find in memory|memory search)\s*(for\s+)?",
            "",
            message,
            flags=re.I,
        ).strip()
    if not query:
        return err("Search for what?")
    hits = assistant.memory.search(query, limit=15, namespace=_namespace(assistant))
    if not hits:
        return ok("No matches in memory.", module="memory")
    lines = [f"• ({h.get('type', 'note')}) {h.get('content', '')}" for h in hits]
    return ok("Memory search:\n\n" + "\n".join(lines), module="memory")


@register_action("memory_about_user", module="memory", description="User profile from memory")
def memory_about_user(assistant, params: dict, message: str) -> dict:
    question = params.get("question") or message
    hits = assistant.memory.search(question, limit=10, namespace=_namespace(assistant))
    prefs = [h for h in hits if h.get("type") in ("preference", "fact", "note")]
    if not prefs:
        return ok("I don't know much about you yet — tell me what to remember.", module="memory")
    lines = [f"• {h.get('content', '')}" for h in prefs[:8]]
    return ok("About you:\n\n" + "\n".join(lines), module="memory")
