"""Natural language → automation rule drafts (confirm required — never auto-enable)."""

from __future__ import annotations

import re
from typing import Any


def parse_nl_automation(text: str) -> dict[str, Any]:
    """Parse a simple English schedule into a draft rule. Always requires confirmation."""
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "error": "Empty request"}

    lower = raw.lower()
    draft: dict[str, Any] = {
        "name": raw[:80],
        "enabled": False,  # NEVER auto-enable
        "kind": "interval",
        "expression": "3600",
        "action": "briefing",
        "params": {},
        "confirmation_required": True,
    }

    # Weekday 7am briefing
    if re.search(r"every weekday|weekdays|monday.?friday", lower):
        draft["kind"] = "cron"
        hour = 7
        m = re.search(r"(\d{1,2})\s*(am|pm)?", lower)
        if m:
            hour = int(m.group(1))
            if (m.group(2) or "").lower() == "pm" and hour < 12:
                hour += 12
            if (m.group(2) or "").lower() == "am" and hour == 12:
                hour = 0
        draft["expression"] = f"0 {hour} * * 1-5"
        # Note: our cron matcher is exact ints only for dow — document limitation
        # Use interval fallback message
        draft["expression"] = f"0 {hour} * * *"
        draft["name"] = f"Weekday {hour}:00 routine"
        draft["cron_note"] = "Minimal cron supports exact fields; review before enabling."

    if re.search(r"every\s+(\d+)\s*(minute|min|hour|hr|second|sec)", lower):
        m = re.search(r"every\s+(\d+)\s*(minute|min|hour|hr|second|sec)", lower)
        n = int(m.group(1))
        unit = m.group(2)
        secs = n * 60
        if unit.startswith("hour") or unit.startswith("hr"):
            secs = n * 3600
        elif unit.startswith("sec"):
            secs = max(30, n)
        draft["kind"] = "interval"
        draft["expression"] = str(max(30, secs))
        draft["name"] = f"Every {n} {unit}"

    if re.search(r"\b(pdf|document|documents)\b", lower) and re.search(r"\b(index|reindex|arrive|new)\b", lower):
        draft["kind"] = "watch"
        draft["expression"] = "~/Documents"
        draft["action"] = "documents_reindex"
        draft["name"] = "Watch documents folder"
        draft["params"] = {"hint": "Set expression to the folder path to watch"}

    if re.search(r"briefing|morning", lower):
        draft["action"] = "briefing"
    elif re.search(r"maintenance|nightly", lower):
        draft["action"] = "maintenance"
    elif re.search(r"memory|consolidat", lower):
        draft["action"] = "memory_consolidate"
    elif re.search(r"knowledge|sync", lower):
        draft["action"] = "knowledge_sync"
    elif re.search(r"pause|travel", lower):
        return {
            "ok": True,
            "intent": "pause_all",
            "explanation": "Pause all enabled automations (travel mode).",
            "draft": None,
            "confirmation_required": True,
            "preview": "Would disable all currently enabled rules until you resume.",
        }

    return {
        "ok": True,
        "intent": "create_rule",
        "explanation": "Draft rule from natural language. Review and confirm — not enabled yet.",
        "draft": draft,
        "confirmation_required": True,
        "preview": (
            f"{draft['kind']} · {draft['expression']} · action={draft['action']} · enabled=false"
        ),
    }
