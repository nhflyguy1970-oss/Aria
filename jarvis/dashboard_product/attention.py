"""Attention strip — one ranked list of things needing operator focus."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _item(
    *,
    id: str,
    title: str,
    severity: str,
    owner: str,
    deep_link: dict[str, Any],
    detail: str = "",
) -> dict[str, Any]:
    return {
        "id": id,
        "title": title,
        "severity": severity,  # critical | warn | info
        "owner": owner,
        "detail": detail,
        "deep_link": deep_link,
    }


def build_attention(*, assistant: Any = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []

    # Provider health
    try:
        from jarvis.gui.server import get_health_snapshot  # type: ignore
    except Exception:
        get_health_snapshot = None  # type: ignore
    try:
        # Prefer lightweight probe used by /api/health if available
        import urllib.request

        # Local in-process: use system heuristics
        from jarvis.feature_flags import all_flags

        flags = all_flags()
        if flags.get("ollama") is False:
            items.append(
                _item(
                    id="provider.ollama_flag",
                    title="Ollama disabled in feature flags",
                    severity="warn",
                    owner="Models",
                    deep_link={"view": "models"},
                )
            )
    except Exception:
        pass

    try:
        import httpx

        # Skip network if not needed — use assistant readiness if present
        ready = getattr(assistant, "ready", None)
        if ready is False:
            items.append(
                _item(
                    id="provider.not_ready",
                    title="Aria not fully ready",
                    severity="warn",
                    owner="Mission Control",
                    deep_link={"view": "workstation"},
                    detail="Open Mission Control for provider detail",
                )
            )
    except Exception:
        pass

    # Planner overdue / open tasks
    try:
        from jarvis.planner_store import list_tasks, planner_enabled

        if planner_enabled():
            tasks = [t for t in list_tasks() if not t.get("completed")]
            overdue = [t for t in tasks if t.get("overdue") or t.get("due_status") == "overdue"]
            if overdue:
                items.append(
                    _item(
                        id="planner.overdue",
                        title=f"{len(overdue)} overdue planner task(s)",
                        severity="warn",
                        owner="Planner",
                        deep_link={"view": "planner"},
                        detail=(overdue[0].get("text") or "")[:120],
                    )
                )
            elif len(tasks) >= 8:
                items.append(
                    _item(
                        id="planner.backlog",
                        title=f"{len(tasks)} open planner tasks",
                        severity="info",
                        owner="Planner",
                        deep_link={"view": "planner"},
                    )
                )
    except Exception:
        pass

    # Upcoming calendar / planner events (next 2h)
    try:
        from jarvis.planner_store import events_for_day, planner_enabled

        if planner_enabled():
            now = datetime.now()
            for ev in events_for_day()[:8]:
                start = ev.get("start_time") or ""
                try:
                    if "T" in start:
                        st = datetime.fromisoformat(start.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        continue
                    delta = (st - now).total_seconds()
                    if 0 <= delta <= 7200:
                        mins = int(delta // 60)
                        items.append(
                            _item(
                                id=f"planner.soon.{ev.get('id') or start}",
                                title=f"In {mins}m: {ev.get('title') or 'Event'}",
                                severity="info",
                                owner="Planner",
                                deep_link={"view": "planner"},
                            )
                        )
                except Exception:
                    continue
    except Exception:
        pass

    try:
        from jarvis.calendar_ics import fetch_events_for_day

        for ev in fetch_events_for_day(date.today())[:6]:
            t = ev.get("time") or ""
            if t:
                items.append(
                    _item(
                        id=f"calendar.{t}.{ev.get('summary')}",
                        title=f"Calendar: {ev.get('summary') or 'Event'}",
                        severity="info",
                        owner="Calendar",
                        deep_link={"view": "calendar"},
                        detail=str(t),
                    )
                )
                break  # one glance item is enough; Daily Brief has more
    except Exception:
        pass

    # Jobs (best-effort)
    try:
        from jarvis.job_center import list_jobs  # type: ignore

        jobs = list_jobs() if callable(list_jobs) else []
        running = [j for j in jobs if str(j.get("status") or "").lower() in ("running", "queued", "pending")]
        failed = [j for j in jobs if str(j.get("status") or "").lower() in ("failed", "error")]
        if failed:
            items.append(
                _item(
                    id="jobs.failed",
                    title=f"{len(failed)} failed job(s)",
                    severity="critical",
                    owner="Automation",
                    deep_link={"view": "automation"},
                    detail=str(failed[0].get("name") or failed[0].get("id") or "")[:120],
                )
            )
        if running:
            items.append(
                _item(
                    id="jobs.running",
                    title=f"{len(running)} job(s) running",
                    severity="info",
                    owner="Automation",
                    deep_link={"view": "automation"},
                )
            )
    except Exception:
        try:
            # Alternate job API surface
            from jarvis.jobs import recent_jobs  # type: ignore

            recent = recent_jobs(limit=20) or []
            failed = [j for j in recent if str(j.get("status") or "").lower() in ("failed", "error")]
            if failed:
                items.append(
                    _item(
                        id="jobs.failed",
                        title=f"{len(failed)} recent failed job(s)",
                        severity="critical",
                        owner="Automation",
                        deep_link={"view": "automation"},
                    )
                )
        except Exception:
            pass

    # Smart Home alerts (summary only)
    try:
        from jarvis.home_assistant import ha_summary_markdown

        summary = ha_summary_markdown() or ""
        if "unavailable" in summary.lower() or "error" in summary.lower():
            items.append(
                _item(
                    id="ha.alert",
                    title="Smart Home needs attention",
                    severity="warn",
                    owner="Smart Home",
                    deep_link={"view": "workstation"},
                    detail=summary[:140],
                )
            )
    except Exception:
        pass

    severity_rank = {"critical": 0, "warn": 1, "info": 2}
    items.sort(key=lambda x: (severity_rank.get(x.get("severity") or "info", 9), x.get("title") or ""))
    return {
        "count": len(items),
        "items": items[:12],
        "empty": len(items) == 0,
        "message": "Nothing urgent — you're clear." if not items else "",
    }
