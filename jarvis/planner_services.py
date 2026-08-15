"""Planner intelligence services — Daily Focus, morning triage, vision capture, HA focus."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

log = logging.getLogger("jarvis.planner.services")


def daily_focus(assistant: Any | None = None) -> dict[str, Any]:
    """Assemble Daily Focus payload from planner + calendar + light AI heuristics."""
    from jarvis.planner_store import (
        active_timers,
        events_for_day,
        list_alarms,
        list_tasks,
        planner_snapshot,
        recently_completed_tasks,
    )

    snap = planner_snapshot()
    if not snap.get("enabled"):
        return {"ok": False, "enabled": False, "message": "Planner disabled"}

    tasks = list_tasks()
    events = events_for_day()
    timers = active_timers()
    alarms = list_alarms()
    completed = recently_completed_tasks(limit=5)

    # Priority: higher priority first, then due today, then creation order
    today = datetime.now().date().isoformat()
    ranked = sorted(
        tasks,
        key=lambda t: (
            -int(t.get("priority") or 0),
            0 if (t.get("due_date") or "")[:10] == today else 1,
            t.get("created_at") or "",
        ),
    )
    top3 = ranked[:3]
    at_risk = [
        t
        for t in ranked
        if (t.get("due_date") or "")[:10] and (t.get("due_date") or "")[:10] <= today
    ][:5]

    # Available focus time heuristic: waking hours minus events
    now = datetime.now()
    day_end = now.replace(hour=21, minute=0, second=0, microsecond=0)
    remaining_min = max(0, int((day_end - now).total_seconds() // 60))
    booked = 0
    for e in events:
        try:
            s = datetime.fromisoformat(e["start_time"])
            en = datetime.fromisoformat(e["end_time"]) if e.get("end_time") else s + timedelta(minutes=30)
            if en > now:
                booked += max(0, int((min(en, day_end) - max(s, now)).total_seconds() // 60))
        except Exception:
            continue
    focus_min = max(0, remaining_min - booked)

    next_action = None
    if timers:
        running = next((t for t in timers if not t.get("paused")), timers[0])
        next_action = {
            "type": "timer",
            "label": f"Focus on timer: {running.get('label') or 'timer'}",
            "id": running.get("id"),
        }
    elif top3:
        next_action = {"type": "task", "label": f"Start: {top3[0].get('text')}", "id": top3[0].get("id")}
    elif events:
        next_action = {
            "type": "event",
            "label": f"Upcoming: {events[0].get('title')}",
            "id": events[0].get("id"),
        }
    else:
        next_action = {"type": "idle", "label": "Add a task or start a focus session"}

    health = {
        "open_tasks": len(tasks),
        "events_today": len(events),
        "active_timers": len(timers),
        "upcoming_alarms": len(alarms),
        "at_risk": len(at_risk),
        "status": "healthy" if len(at_risk) == 0 else "attention",
    }

    # Local briefing only — Daily Focus must not call ACM memory.search on every poll (SYS-P01).
    # Full "what am I working on" with memory remains available via morning_triage / workflows.
    briefing_parts: list[str] = []
    try:
        from jarvis.active_project import get_active_slug

        slug = get_active_slug()
        if slug:
            briefing_parts.append(f"**Active project:** `{slug}`")
    except Exception:
        pass
    if top3:
        briefing_parts.append("**Open planner tasks:**")
        for t in top3[:5]:
            briefing_parts.append(f"- {t.get('text') or t}")
    if events:
        briefing_parts.append("**Today's planner events:**")
        for e in events[:4]:
            t = (e.get("start_time") or "")[11:16]
            briefing_parts.append(f"- {t} {e.get('title') or ''}".strip())
    briefing = "\n".join(briefing_parts)[:800]

    return {
        "ok": True,
        "enabled": True,
        "top_priorities": top3,
        "events": events,
        "timers": timers,
        "alarms": alarms,
        "focus_minutes_available": focus_min,
        "tasks_at_risk": at_risk,
        "suggested_next": next_action,
        "recently_completed": completed,
        "health": health,
        "morning_briefing": briefing,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def morning_triage(assistant: Any | None = None) -> dict[str, Any]:
    """AI-assisted morning triage using planner + optional memory/RAG/graph/reason."""
    focus = daily_focus(assistant)
    if not focus.get("ok"):
        return focus

    evidence: list[str] = []
    citations: list[dict] = []
    confidence = 0.55

    # Memory
    try:
        if assistant is not None and getattr(assistant, "memory", None):
            hits = assistant.memory.search("priority today plan tasks", limit=4) or []
            for h in hits[:3]:
                evidence.append(f"Memory: {(h.get('content') or '')[:160]}")
            if hits:
                confidence += 0.08
    except Exception as exc:
        log.debug("triage memory: %s", exc)

    # RAG
    try:
        from jarvis.intelligence.hybrid_rag import hybrid_search

        rag = hybrid_search("daily priorities planner", limit=3)
        citations = rag.get("citations") or []
        if rag.get("hits"):
            confidence += 0.05
            evidence.append("Documents retrieved for context")
    except Exception as exc:
        log.debug("triage rag: %s", exc)

    # Knowledge graph
    try:
        from jarvis.intelligence.knowledge_graph import search_graph

        g = search_graph("Planner", limit=4)
        if g.get("nodes"):
            evidence.append(f"Graph nodes: {len(g['nodes'])}")
            confidence += 0.03
    except Exception as exc:
        log.debug("triage graph: %s", exc)

    # Reasoning
    plan = []
    try:
        from jarvis.intelligence.reasoning import reason

        goal = "Plan my day with top priorities, focus blocks, and risks"
        r = reason(goal, assistant=assistant, use_rag=False)
        plan = r.get("plan") or []
        confidence = max(confidence, float(r.get("confidence") or confidence))
    except Exception as exc:
        log.debug("triage reason: %s", exc)
        plan = [
            "Review top 3 planner tasks",
            "Protect focus time around calendar events",
            "Clear at-risk due items first",
            "Start one focus session",
        ]

    schedule = []
    now = datetime.now().replace(second=0, microsecond=0)
    cursor = now + timedelta(minutes=(15 - now.minute % 15) % 15 or 15)
    for t in focus.get("top_priorities") or []:
        schedule.append(
            {
                "when": cursor.strftime("%H:%M"),
                "title": t.get("text"),
                "kind": "task",
                "id": t.get("id"),
            }
        )
        cursor += timedelta(minutes=45)

    for e in (focus.get("events") or [])[:4]:
        schedule.append(
            {
                "when": (e.get("start_time") or "")[11:16],
                "title": e.get("title"),
                "kind": "event",
                "id": e.get("id"),
            }
        )

    schedule.sort(key=lambda x: x.get("when") or "99:99")

    risks = [
        {"task": t.get("text"), "reason": "Due today or overdue", "id": t.get("id")}
        for t in (focus.get("tasks_at_risk") or [])
    ]
    if not risks and len(focus.get("top_priorities") or []) > 5:
        risks.append({"task": "(workload)", "reason": "Many open tasks — triage ruthlessly"})

    recommendations = []
    if focus.get("suggested_next"):
        recommendations.append(focus["suggested_next"].get("label"))
    if focus.get("focus_minutes_available", 0) >= 50:
        recommendations.append("Start a 25-minute focus session on your top priority")
    elif focus.get("focus_minutes_available", 0) < 30:
        recommendations.append("Day is packed — keep tasks tiny or defer non-essentials")
    if risks:
        recommendations.append("Address at-risk tasks before new work")

    return {
        "ok": True,
        "top_priorities": focus.get("top_priorities"),
        "suggested_schedule": schedule[:8],
        "risks": risks,
        "recommendations": recommendations[:6],
        "plan": plan,
        "confidence": round(min(0.95, confidence), 3),
        "evidence": evidence[:8],
        "citations": citations,
        "focus": focus,
    }


def vision_extract_tasks(path: str, *, assistant: Any | None = None) -> dict[str, Any]:
    """OCR / vision → candidate tasks via shared Vision import pipeline."""
    from jarvis.vision_product.import_pipeline import vision_import

    out = vision_import(
        path=path,
        target="planner",
        source="planner",
        assistant=assistant,
    )
    if not out.get("ok"):
        return {
            "ok": False,
            "message": out.get("error") or out.get("message") or "OCR unavailable",
            "candidates": [],
        }
    return {
        "ok": True,
        "path": out.get("path") or path,
        "raw_text": out.get("raw_text") or "",
        "candidates": out.get("candidates") or [],
        "engine": out.get("engine"),
        "confidence": out.get("confidence"),
        "pipeline": "vision_import",
        "message": out.get("message") or f"Found {len(out.get('candidates') or [])} candidate task(s) — review before import",
    }


def import_vision_tasks(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    from jarvis.planner_store import add_task

    added = []
    errors = []
    for c in candidates or []:
        if not c.get("selected", True):
            continue
        text = str(c.get("text") or "").strip()
        if not text:
            continue
        try:
            task = add_task(text)
            # mark source if schema supports
            try:
                from jarvis.planner_store import update_task

                # source set via SQL
                from jarvis.planner_store import _conn

                with _conn() as conn:
                    conn.execute("UPDATE tasks SET source = ? WHERE id = ?", ("vision", task["id"]))
            except Exception:
                pass
            added.append(task)
        except Exception as exc:
            errors.append(str(exc))
    return {"ok": True, "added": added, "count": len(added), "errors": errors[:10]}


def suggest_schedule(task_ids: list[str] | None = None) -> dict[str, Any]:
    """Recommend (not auto-apply) calendar slots for open/due tasks."""
    from jarvis.planner_store import events_for_day, list_tasks

    tasks = list_tasks()
    if task_ids:
        wanted = set(task_ids)
        tasks = [t for t in tasks if t.get("id") in wanted]
    events = events_for_day()
    busy = []
    for e in events:
        try:
            busy.append(
                (
                    datetime.fromisoformat(e["start_time"]),
                    datetime.fromisoformat(e["end_time"]) if e.get("end_time") else None,
                )
            )
        except Exception:
            continue

    suggestions = []
    cursor = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30)
    cursor = cursor.replace(minute=(cursor.minute // 15) * 15)
    for t in tasks[:6]:
        # skip busy windows
        for _ in range(12):
            conflict = False
            end = cursor + timedelta(minutes=45)
            for b0, b1 in busy:
                b1 = b1 or (b0 + timedelta(minutes=30))
                if cursor < b1 and end > b0:
                    conflict = True
                    cursor = b1 + timedelta(minutes=15)
                    break
            if not conflict:
                break
            cursor += timedelta(minutes=15)
        suggestions.append(
            {
                "task_id": t.get("id"),
                "task": t.get("text"),
                "suggested_start": cursor.isoformat(timespec="seconds"),
                "suggested_end": (cursor + timedelta(minutes=45)).isoformat(timespec="seconds"),
                "requires_confirmation": True,
            }
        )
        cursor += timedelta(minutes=60)

    return {
        "ok": True,
        "suggestions": suggestions,
        "message": "Suggestions only — confirm before creating calendar events",
    }


def apply_schedule_suggestion(suggestion: dict[str, Any]) -> dict[str, Any]:
    """Create a planner event from a confirmed suggestion."""
    from jarvis.planner_store import add_event

    title = suggestion.get("task") or suggestion.get("title") or "Scheduled task"
    start = suggestion.get("suggested_start")
    if not start:
        raise ValueError("suggested_start required")
    start_dt = datetime.fromisoformat(start)
    return add_event(
        title,
        when=start_dt.date().isoformat(),
        time_str=start_dt.strftime("%H:%M"),
        duration_min=45,
    )


def start_focus_session(
    *,
    duration: str = "25 minutes",
    label: str = "Focus",
    use_ha: bool | None = None,
) -> dict[str, Any]:
    """Start a focus timer and optionally activate HA Focus scene."""
    from jarvis.planner_store import get_pref, set_pref, set_timer

    timer = set_timer(duration, label=label or "Focus")
    ha_result = None
    prefer = get_pref("ha_focus_enabled", False) if use_ha is None else bool(use_ha)
    if prefer:
        try:
            from jarvis.scene_presets import activate_preset, list_presets

            presets = list_presets() if callable(list_presets) else []
            focus_id = None
            for p in presets or []:
                pid = (p.get("id") or p.get("name") or "").lower()
                if "focus" in pid or "focus" in (p.get("label") or "").lower():
                    focus_id = p.get("id") or p.get("name")
                    break
            if focus_id:
                ok, msg = activate_preset(focus_id)
                ha_result = {"ok": ok, "message": msg, "preset": focus_id}
                set_pref("ha_focus_last_preset", focus_id)
            else:
                ha_result = {"ok": False, "message": "No Focus scene preset found"}
        except Exception as exc:
            ha_result = {"ok": False, "message": str(exc)}
    set_pref("focus_active_timer", timer.get("id"))
    ha_requested = bool(prefer)
    ha_ok = True if not ha_requested else bool(ha_result and ha_result.get("ok"))
    warnings: list[str] = []
    if ha_requested and not ha_ok:
        warnings.append(
            (ha_result or {}).get("message") or "Home Assistant Focus scene did not activate"
        )
    return {
        "ok": True,
        "timer": timer,
        "home_assistant": ha_result,
        "ha_requested": ha_requested,
        "ha_ok": ha_ok,
        "complete": ha_ok,
        "warnings": warnings,
    }


def end_focus_session(*, restore_ha: bool = True) -> dict[str, Any]:
    from jarvis.planner_store import cancel_timer, get_pref, set_pref

    tid = get_pref("focus_active_timer")
    cancelled = None
    if tid:
        cancelled = cancel_timer(str(tid))
        set_pref("focus_active_timer", None)
    ha = None
    if restore_ha and get_pref("ha_focus_enabled", False):
        try:
            from jarvis.scene_presets import activate_preset

            # Prefer a relax/default scene if present
            for name in ("relax", "default", "evening"):
                try:
                    ok, msg = activate_preset(name)
                    if ok:
                        ha = {"ok": True, "preset": name, "message": msg}
                        break
                except Exception:
                    continue
        except Exception as exc:
            ha = {"ok": False, "message": str(exc)}
    return {"ok": True, "cancelled": cancelled, "home_assistant": ha}
