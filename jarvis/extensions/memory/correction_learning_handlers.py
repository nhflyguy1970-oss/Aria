"""Correction learning action handlers."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _last_assistant_message(assistant) -> str:
    for msg in reversed(assistant.conversation.messages):
        if msg.get("role") == "assistant":
            return (msg.get("content") or "")[:2000]
    return ""


@register_action("correction_learn", module="memory", description="Learn from user correction")
def correction_learn(assistant, params: dict, message: str) -> dict:
    from jarvis.correction_learning import apply_correction, parse_correction

    raw = (params.get("text") or message).strip()
    intent = parse_correction(raw)
    if not intent:
        return err(
            "What should I correct? Examples:\n"
            "• **No, that's wrong — mom's birthday is June 9**\n"
            "• **You're wrong about the port; it's 8765**\n"
            "• **correct that the repo is at /media/jeff/AI/jarvis**",
            module="memory",
        )
    assistant_msg = (params.get("assistant_msg") or _last_assistant_message(assistant)).strip()
    module = (params.get("module") or assistant.session.last_module or "").strip()
    result = apply_correction(
        assistant.memory,
        intent,
        assistant_msg=assistant_msg,
        module=module,
    )
    if not result.ok:
        return err(result.message, module="memory")
    assistant.refresh_system_prompt()
    mirror = ""
    if result.mirrors:
        mirror = f"\n\n_Also: {', '.join(result.mirrors)}._"
    body = f"**Correct:** {result.correction}{mirror}"
    if result.wrong_claim:
        body = (
            f"**Wrong:** {result.wrong_claim}\n\n"
            f"**Correct:** {result.correction}{mirror}"
        )
    return ok(
        f"Got it — I'll remember this correction ({result.kind}).\n\n{body}",
        module="memory",
        correction=result.correction,
        kind=result.kind,
    )


@register_action("correction_recall", module="memory", description="Recall user corrections")
def correction_recall(assistant, params: dict, message: str) -> dict:
    from jarvis.correction_learning import (
        correction_stats,
        format_corrections_markdown,
        list_corrections,
        parse_correction_recall_query,
    )

    query = (params.get("query") or parse_correction_recall_query(message) or "").strip()
    entries = list_corrections(assistant.memory, query=query)
    stats = correction_stats()
    if not entries:
        return ok(
            "No corrections yet. When I get something wrong, say **no, that's wrong — …** "
            "or **correct that …**",
            module="memory",
        )
    title = f"Corrections about **{query}**" if query else "Your corrections"
    footer = f"\n\n_{stats['total']} correction(s) in `{stats['namespace']}`._"
    return ok(
        title + "\n\n" + format_corrections_markdown(entries) + footer,
        module="memory",
    )
