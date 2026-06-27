"""Nightly knowledge research handlers."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "knowledge_research_run",
    module="general",
    description="Run nightly knowledge research (AI news, Ollama, Zorin, dependencies)",
    queue="background",
)
def knowledge_research_run(assistant, params: dict, message: str) -> dict:
    from jarvis.knowledge_research_daily import (
        get_category,
        research_category,
        run_nightly_research,
    )

    force = (params.get("force") or "").lower() in ("1", "true", "yes") or "force" in message.lower()
    category = (params.get("category") or "").strip()
    if not category:
        if m := re.search(r"\bresearch\s+(ai news|ollama|zorin|dependencies)\b", message, re.I):
            category = m.group(1).lower().replace(" ", "_")
        elif m := re.search(r"\b(ai news|ollama updates?|zorin updates?|dependency updates?)\b", message, re.I):
            raw = m.group(1).lower()
            category = {
                "ai news": "ai_news",
                "ollama": "ollama",
                "ollama update": "ollama",
                "ollama updates": "ollama",
                "zorin": "zorin",
                "zorin update": "zorin",
                "zorin updates": "zorin",
                "dependency update": "dependencies",
                "dependency updates": "dependencies",
            }.get(raw, "")

    if category:
        cat = get_category(category.replace(" ", "_"))
        if not cat:
            return err(f"Unknown research category: {category}", module="general")
        result = research_category(cat["id"], memory=assistant.memory, force=force)
        if not result.get("ok"):
            return err(result.get("message", "Research failed."), module="general")
        if result.get("skipped"):
            return ok(f"**{cat['title']}** already researched today.", module="general")
        body = result.get("message", "Done.")
        if result.get("remembered"):
            assistant.refresh_system_prompt()
            body += f"\n\n_Remembered {result['remembered']} key point(s)._"
        return ok(body, module="general", **{k: result[k] for k in ("slug", "path") if k in result})

    results = run_nightly_research(memory=assistant.memory, force=force)
    if len(results) == 1 and results[0].get("skipped"):
        return ok(results[0].get("message", "Already completed tonight."), module="general")
    updated = [r for r in results if r.get("ok") and not r.get("skipped")]
    if not updated:
        msg = results[0].get("message") if results else "No research categories ran."
        return err(msg, module="general") if results and not results[0].get("ok") else ok(msg, module="general")
    lines = [f"• **{r.get('title') or r.get('slug')}**" for r in updated]
    remembered = sum(r.get("remembered") or 0 for r in updated)
    body = f"Nightly knowledge research ({len(updated)} topic(s)):\n\n" + "\n".join(lines)
    body += "\n\nSummaries saved under `data/knowledge/research/`."
    if remembered:
        assistant.refresh_system_prompt()
        body += f"\n\n_Remembered {remembered} key point(s) into memory._"
    return ok(body, module="general", results=updated)


@register_action(
    "knowledge_research_list",
    module="general",
    description="List saved nightly research briefs",
    info=True,
)
def knowledge_research_list(assistant, params: dict, message: str) -> dict:
    from jarvis.knowledge_research_daily import list_research_briefs

    items = list_research_briefs()
    if not items:
        return ok(
            "No nightly research briefs yet. Say **run nightly knowledge research** or wait for the 11 PM job.",
            module="general",
        )
    lines = [
        f"• **{i['title']}** (`{i['slug']}`) — last {i.get('last_day') or i.get('updated', '')}"
        for i in items
    ]
    return ok("**Saved research briefs**\n\n" + "\n".join(lines), module="general")
