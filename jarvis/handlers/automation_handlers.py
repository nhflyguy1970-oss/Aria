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


@register_action("pipeline_list", module="general", description="List Automation pipelines (DAGs)", info=True)
def pipeline_list(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.pipelines.storage import list_pipelines

    items = list_pipelines(q=str(params.get("q") or ""))
    if not items:
        return ok("No pipelines yet. Open **Automation** → Pipelines to create from a template.", module="general")
    lines = [f"· **{p.get('name')}** (`{p.get('id')}`) — {p.get('step_count', 0)} steps" for p in items[:20]]
    return ok("**Pipelines (DAGs)** — multi-step Automation pipelines\n\n" + "\n".join(lines), module="general", pipelines=items)


@register_action("pipeline_explain", module="general", description="Explain a pipeline", info=True)
def pipeline_explain(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.pipelines.engine import explain_pipeline
    from jarvis.automation.pipelines.storage import list_pipelines

    pid = str(params.get("workflow_id") or params.get("pipeline_id") or params.get("id") or "")
    if not pid:
        q = str(params.get("q") or message or "")
        for p in list_pipelines(q=q):
            pid = p["id"]
            break
    if not pid:
        return err("Which pipeline? Say **list pipelines** first.", module="general")
    data = explain_pipeline(pid)
    if not data.get("ok"):
        return err(data.get("error") or "not found", module="general")
    lines = [data.get("summary") or data.get("name")]
    for s in data.get("steps") or []:
        lines.append(f"· **{s.get('name')}** → `{s.get('action')}` — {(s.get('action_meta') or {}).get('ai_explain') or ''}")
    return ok("\n".join(lines), module="general", explain=data)


@register_action("pipeline_run", module="general", description="Run an Automation pipeline")
def pipeline_run(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.pipelines.engine import run_pipeline
    from jarvis.automation.pipelines.storage import list_pipelines

    pid = str(params.get("workflow_id") or params.get("pipeline_id") or params.get("id") or "")
    dry = bool(params.get("dry_run"))
    confirm = bool(params.get("confirm"))
    if not pid:
        q = str(params.get("q") or "")
        for p in list_pipelines(q=q):
            pid = p["id"]
            break
    if not pid:
        return err("Which pipeline?", module="general")
    if not dry and not confirm:
        return ok(
            f"Ready to run pipeline `{pid}`. Confirm with **run pipeline {pid} confirm** or use dry run.",
            module="general",
            status="permission_required",
            pipeline_id=pid,
        )
    result = run_pipeline(pid, dry_run=dry, trigger="chat", emit_bridges=True)
    summary = result.get("success_summary") or result.get("failure_summary") or result.get("status")
    return ok(
        f"Pipeline **{result.get('name')}**: `{result.get('status')}`\n{summary}\nRun id: `{result.get('run_id')}`",
        module="general",
        result=result,
    )


@register_action("pipeline_history", module="general", description="Show pipeline run history", info=True)
def pipeline_history(assistant, params: dict, message: str) -> dict:
    from jarvis.automation.pipelines.runs import last_failure, list_pipeline_runs

    pid = str(params.get("workflow_id") or params.get("pipeline_id") or "")
    if params.get("failures_only"):
        fail = last_failure(pid or None)
        if not fail:
            return ok("No pipeline failures recorded.", module="general")
        return ok(
            f"Last failure: **{fail.get('name')}** — {fail.get('failure_summary')}\nRun `{fail.get('id')}`",
            module="general",
            run=fail,
        )
    runs = list_pipeline_runs(limit=10, pipeline_id=pid or None)
    if not runs:
        return ok("No pipeline runs yet.", module="general")
    lines = [f"· `{r.get('id')}` **{r.get('name')}** — {r.get('status')} ({r.get('elapsed_ms')}ms)" for r in runs]
    return ok("**Recent pipeline runs**\n\n" + "\n".join(lines), module="general", runs=runs)


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

    # Pipelines (DAGs) — subsystem of Automation
    if re.search(r"\b(list|show)\s+pipelines?\b", lower) or re.search(r"\bpipelines?\s+list\b", lower):
        return {"action": "pipeline_list", "params": {}}
    if re.search(r"\bexplain\s+pipeline\b", lower) or re.search(r"\bdescribe\s+pipeline\b", lower):
        m = re.search(r"pipeline\s+([a-z0-9_-]+)", lower)
        return {"action": "pipeline_explain", "params": {"q": m.group(1) if m else ""}}
    if re.search(r"\bpipeline\s+history\b", lower) or re.search(r"\bshow\s+pipeline\s+(history|runs)\b", lower):
        return {"action": "pipeline_history", "params": {}}
    if re.search(r"\blast\s+pipeline\s+failure\b", lower) or re.search(r"\bpipeline\s+last\s+failure\b", lower):
        return {"action": "pipeline_history", "params": {"failures_only": True}}
    if re.search(r"\bdry\s*-?\s*run\s+pipeline\b", lower):
        m = re.search(r"pipeline\s+([a-z0-9_-]+)", lower)
        return {"action": "pipeline_run", "params": {"q": m.group(1) if m else "", "dry_run": True}}
    if re.search(r"\brun\s+pipeline\b", lower):
        m = re.search(r"pipeline\s+([a-z0-9_-]+)", lower)
        confirm = "confirm" in lower
        return {
            "action": "pipeline_run",
            "params": {"q": m.group(1) if m else "", "confirm": confirm, "dry_run": False},
        }
    return None
