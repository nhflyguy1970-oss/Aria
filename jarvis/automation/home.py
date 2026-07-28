"""Automation Home aggregation — single product snapshot."""

from __future__ import annotations

import time
from typing import Any

from jarvis.automation.execution import FAILED, SKIPPED, SUCCEEDED
from jarvis.automation.history import list_runs, recent_failures
from jarvis.automation.migrate import migrate_storage
from jarvis.automation.registry import list_actions


def _webhook_status() -> dict[str, Any]:
    try:
        from jarvis.home_assistant import automation_secret, status_payload

        secret = bool(automation_secret())
        payload = {}
        try:
            payload = status_payload() or {}
        except Exception:
            payload = {}
        return {
            "configured": secret,
            "url": payload.get("automation_webhook_url") or "",
            "ha_configured": bool(payload.get("configured") or payload.get("ok")),
            "message": (
                "Webhook ready — use X-Jarvis-Automation-Secret header"
                if secret
                else "Set JARVIS_AUTOMATION_SECRET to enable inbound webhooks"
            ),
        }
    except Exception as exc:
        return {"configured": False, "url": "", "message": str(exc)}


def _engine_status() -> dict[str, Any]:
    try:
        from jarvis.intelligence.automation_engine import status

        return status()
    except Exception as exc:
        return {"ok": False, "running": False, "rules": [], "error": str(exc)}


def _skills() -> list[dict[str, Any]]:
    try:
        from jarvis.skill_database import list_skills

        return [
            {
                "slug": s.get("slug"),
                "name": s.get("name"),
                "description": s.get("description"),
                "steps": len(s.get("steps") or []),
            }
            for s in list_skills()[:40]
        ]
    except Exception:
        return []


def _learned() -> list[dict[str, Any]]:
    try:
        from jarvis.workflow_learning import list_workflows

        return list_workflows()[:40]
    except Exception:
        return []


def _dags() -> list[dict[str, Any]]:
    try:
        from jarvis.intelligence.workflow_engine import TEMPLATES, list_workflows

        return {"workflows": list_workflows(), "templates": list(TEMPLATES.keys())}
    except Exception:
        return {"workflows": [], "templates": []}


def _suggestions() -> list[dict[str, Any]]:
    try:
        from jarvis.automation.suggestions import list_suggestions

        return list_suggestions()
    except Exception:
        return []


def _muted() -> list[str]:
    try:
        from jarvis.automation.mute import list_muted

        return list_muted()
    except Exception:
        return []


def home_snapshot() -> dict[str, Any]:
    migrate_storage()
    eng = _engine_status()
    rules = eng.get("rules") or []
    enabled = [r for r in rules if r.get("enabled")]
    disabled = [r for r in rules if not r.get("enabled")]
    runs = list_runs(limit=25)
    failures = recent_failures(15)
    upcoming = []
    for r in enabled:
        kind = r.get("kind")
        expr = r.get("expression")
        upcoming.append(
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "kind": kind,
                "expression": expr,
                "action": r.get("action"),
                "last_run": r.get("last_run"),
                "last_status": r.get("last_status"),
            }
        )

    dags = _dags()
    return {
        "ok": True,
        "identity": {
            "automation": "Schedules and orchestrates work",
            "skills": "Reusable procedures",
            "rules": "Trigger → Action logic",
            "workflows": "Multi-step execution pipelines",
            "view_paths": "Navigation shortcuts only",
            "job_center": "Tracks execution",
            "activity_center": "Tracks events",
            "mission_control": "Tracks infrastructure health",
            "home_assistant": "External automation provider",
        },
        "summary": {
            "engine_running": bool(eng.get("running")),
            "rules_total": len(rules),
            "rules_enabled": len(enabled),
            "rules_disabled": len(disabled),
            "failures_recent": len(failures),
            "runs_recent": len(runs),
            "skills": len(_skills()),
            "learned": len(_learned()),
            "dags": len(dags.get("workflows") or []),
        },
        "health": {
            "engine": "running" if eng.get("running") else "stopped",
            "webhook": _webhook_status(),
            "failures": len(failures),
        },
        "rules": {"enabled": enabled, "disabled": disabled, "all": rules},
        "upcoming": upcoming[:20],
        "recent_runs": runs,
        "failures": failures,
        "skills": _skills(),
        "learned_workflows": _learned(),
        "workflow_dags": dags.get("workflows") or [],
        "templates": dags.get("templates") or [],
        "suggestions": _suggestions(),
        "actions": list_actions(include_experimental=False),
        "muted": _muted(),
        "generated_at": time.time(),
    }


def search_automation(q: str, *, limit: int = 40) -> dict[str, Any]:
    q = (q or "").strip().lower()
    snap = home_snapshot()
    hits: list[dict[str, Any]] = []

    def add(kind: str, title: str, meta: dict[str, Any]):
        if not q or q in f"{title} {meta}".lower():
            hits.append({"kind": kind, "title": title, **meta})

    for r in snap["rules"]["all"]:
        add("rule", r.get("name") or r.get("id"), {"id": r.get("id"), "action": r.get("action")})
    for s in snap["skills"]:
        add("skill", s.get("name") or s.get("slug"), {"slug": s.get("slug")})
    for w in snap["learned_workflows"]:
        add("learned_workflow", w.get("name") or w.get("slug"), {"slug": w.get("slug")})
    for d in snap["workflow_dags"]:
        add("workflow_dag", d.get("name") or d.get("id"), {"id": d.get("id")})
    for t in snap["templates"]:
        add("template", str(t), {"template": t})
    for run in snap["recent_runs"]:
        add("run", run.get("name") or run.get("id"), {"id": run.get("id"), "status": run.get("status")})
    for sug in snap["suggestions"]:
        add("suggestion", sug.get("title") or sug.get("id"), {"id": sug.get("id")})

    # View Paths are client-only — return hint
    if not q or "view" in q or "path" in q or "shortcut" in q:
        hits.append(
            {
                "kind": "view_paths",
                "title": "View Paths (UI navigation shortcuts)",
                "note": "Stored in browser prefs — open View Paths from Automation Home",
            }
        )

    if q:
        hits = [h for h in hits if q in json_dumps_lower(h)]
    return {"ok": True, "query": q, "hits": hits[:limit]}


def json_dumps_lower(obj: Any) -> str:
    import json

    try:
        return json.dumps(obj, default=str).lower()
    except Exception:
        return str(obj).lower()
