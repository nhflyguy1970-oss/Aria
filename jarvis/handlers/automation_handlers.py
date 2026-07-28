"""Chat handlers for Automation Home — consistent routing with skills/workflows."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("automation_home", module="general", description="Open or summarize Automation Home", info=True)
def automation_home(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.home import home_snapshot

    snap = home_snapshot()
    s = snap.get("summary") or {}
    lines = [
        "**Automation Home** — schedules and orchestrates work (not Job Center, Activity, or View Paths).",
        f"· Engine: {'running' if s.get('engine_running') else 'stopped'}",
        f"· Rules: {s.get('rules_enabled', 0)} enabled / {s.get('rules_disabled', 0)} disabled",
        f"· Recent failures: {s.get('failures_recent', 0)}",
        f"· Skills: {s.get('skills', 0)} · Learned workflows: {s.get('learned', 0)}",
        "",
        "Open the **Automation** view for Rule Editor, Dry Run, and Webhook setup.",
        "View Paths are navigation shortcuts only (Ctrl+Shift+V).",
    ]
    return ok("\n".join(lines), module="general", summary=s)


@register_action("automation_status", module="general", description="Automation status", info=True)
def automation_status(assistant, params: dict, message: str) -> dict:
    return automation_home(assistant, params, message)


@register_action("automation_pause", module="general", description="Pause all automations")
def automation_pause(assistant, params: dict, message: str) -> dict:
    from jarvis.intelligence.automation_engine import set_paused

    set_paused(True)
    return ok("Automations **paused**. Say **resume automations** when ready.", module="general")


@register_action("automation_resume", module="general", description="Resume automations")
def automation_resume(assistant, params: dict, message: str) -> dict:
    from jarvis.intelligence.automation_engine import set_paused, start_engine

    set_paused(False)
    start_engine()
    return ok("Automations **resumed**.", module="general")


@register_action("automation_failures", module="general", description="List recent automation failures", info=True)
def automation_failures(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.history import recent_failures

    fails = recent_failures(10)
    if not fails:
        return ok("No recent automation failures.", module="general")
    lines = [f"· **{f.get('name')}** — {f.get('status')}: {f.get('why')}" for f in fails]
    return ok("**Recent automation failures**\n\n" + "\n".join(lines), module="general", failures=fails)


def parse_automation_intent(message: str) -> dict | None:
    lower = (message or "").strip().lower()
    if not lower:
        return None
    if re.search(r"\b(open|show)\s+automation(s| home)?\b", lower) or lower in (
        "automation status",
        "what's scheduled",
        "what is scheduled",
    ):
        return {"action": "automation_home", "params": {}}
    if re.search(r"\bpause\s+automation", lower):
        return {"action": "automation_pause", "params": {}}
    if re.search(r"\bresume\s+automation", lower):
        return {"action": "automation_resume", "params": {}}
    if re.search(r"\bautomation\s+fail", lower) or "recent failures" in lower and "automation" in lower:
        return {"action": "automation_failures", "params": {}}
    if re.search(r"\brun\s+automation\b", lower):
        return {"action": "automation_home", "params": {"hint": "run"}}
    return None
