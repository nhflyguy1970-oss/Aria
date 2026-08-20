"""Planner + P0 HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/planner")
    @app.get("/api/planner/snapshot")
    def planner_get():
        from jarvis.planner_store import planner_snapshot

        return {"ok": True, **planner_snapshot()}

    @app.post("/api/planner/tasks")
    async def planner_add_task_route(request: Request):
        from jarvis.planner_store import add_task

        body = await request.json()
        text = (body.get("text") or "").strip()
        try:
            task = add_task(text)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "task": task}

    @app.post("/api/planner/tasks/{task_id}/complete")
    def planner_complete_task(task_id: str):
        from jarvis.planner_store import complete_task

        return {"ok": complete_task(task_id)}

    @app.post("/api/planner/timers")
    async def planner_timer_route(request: Request):
        from jarvis.planner_store import set_timer

        body = await request.json()
        try:
            t = set_timer(body.get("duration") or "", body.get("label"))
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "timer": t}

    @app.post("/api/planner/alarms")
    async def planner_alarm_route(request: Request):
        from jarvis.planner_store import set_alarm

        body = await request.json()
        try:
            a = set_alarm(body.get("time") or "", body.get("label"))
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "alarm": a}

    @app.post("/api/planner/events")
    async def planner_event_route(request: Request):
        from jarvis.planner_store import add_event

        body = await request.json()
        try:
            ev = add_event(
                body.get("title") or "",
                when=body.get("date") or body.get("when"),
                time_str=body.get("time"),
                duration_min=int(body.get("duration_min") or 15),
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "event": ev}

    @app.post("/api/planner/tick")
    def planner_tick():
        from jarvis.planner_store import active_timers, list_alarms, tick_alarms_and_timers

        notes = tick_alarms_and_timers()
        timers = active_timers() or []
        alarms = [a for a in (list_alarms() or []) if a.get("enabled") and not a.get("fired")]
        return {
            "ok": True,
            "notifications": notes,
            "has_active_timers": bool(timers),
            "has_alarms": bool(alarms),
        }

    @app.post("/api/planner/tasks/{task_id}/update")
    async def planner_update_task(task_id: str, request: Request):
        from jarvis.planner_store import update_task

        body = await request.json()
        try:
            task = update_task(
                task_id,
                text=body.get("text"),
                due_date=body.get("due_date"),
                priority=body.get("priority"),
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "task": task}

    @app.delete("/api/planner/tasks/{task_id}")
    def planner_delete_task(task_id: str):
        from jarvis.planner_store import delete_task

        return delete_task(task_id)

    @app.post("/api/planner/timers/{timer_id}/pause")
    def planner_pause_timer(timer_id: str):
        from jarvis.planner_store import pause_timer

        try:
            return {"ok": True, "timer": pause_timer(timer_id)}
        except ValueError as exc:
            return JSONResponse(status_code=404, content={"ok": False, "message": str(exc)})

    @app.post("/api/planner/timers/{timer_id}/resume")
    def planner_resume_timer(timer_id: str):
        from jarvis.planner_store import resume_timer

        try:
            return {"ok": True, "timer": resume_timer(timer_id)}
        except ValueError as exc:
            return JSONResponse(status_code=404, content={"ok": False, "message": str(exc)})

    @app.post("/api/planner/timers/{timer_id}/cancel")
    @app.delete("/api/planner/timers/{timer_id}")
    def planner_cancel_timer(timer_id: str):
        from jarvis.planner_store import cancel_timer

        return cancel_timer(timer_id)

    @app.post("/api/planner/timers/{timer_id}/update")
    async def planner_update_timer(timer_id: str, request: Request):
        from jarvis.planner_store import update_timer

        body = await request.json()
        try:
            return {
                "ok": True,
                "timer": update_timer(
                    timer_id, label=body.get("label"), duration=body.get("duration")
                ),
            }
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/planner/timers/{timer_id}/duplicate")
    def planner_duplicate_timer(timer_id: str):
        from jarvis.planner_store import duplicate_timer

        try:
            return {"ok": True, "timer": duplicate_timer(timer_id)}
        except ValueError as exc:
            return JSONResponse(status_code=404, content={"ok": False, "message": str(exc)})

    @app.post("/api/planner/alarms/{alarm_id}/cancel")
    @app.delete("/api/planner/alarms/{alarm_id}")
    def planner_cancel_alarm(alarm_id: str):
        from jarvis.planner_store import cancel_alarm

        return cancel_alarm(alarm_id)

    @app.post("/api/planner/alarms/{alarm_id}/update")
    async def planner_update_alarm(alarm_id: str, request: Request):
        from jarvis.planner_store import update_alarm

        body = await request.json()
        try:
            return {
                "ok": True,
                "alarm": update_alarm(alarm_id, time_str=body.get("time"), label=body.get("label")),
            }
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/planner/events/{event_id}/update")
    async def planner_update_event(event_id: str, request: Request):
        from jarvis.planner_store import update_event

        body = await request.json()
        try:
            return {
                "ok": True,
                "event": update_event(
                    event_id,
                    title=body.get("title"),
                    time_str=body.get("time"),
                    when=body.get("date") or body.get("when"),
                    duration_min=body.get("duration_min"),
                    description=body.get("description"),
                ),
            }
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.delete("/api/planner/events/{event_id}")
    def planner_delete_event(event_id: str):
        from jarvis.planner_store import delete_event

        return delete_event(event_id)

    @app.post("/api/planner/undo")
    def planner_undo():
        from jarvis.planner_store import undo_last

        return undo_last()

    @app.get("/api/planner/focus")
    def planner_focus():
        from jarvis.planner_services import daily_focus

        return daily_focus(assistant)

    @app.post("/api/planner/triage")
    def planner_triage():
        from jarvis.planner_services import morning_triage

        return morning_triage(assistant)

    @app.post("/api/planner/focus/start")
    async def planner_focus_start(request: Request):
        from jarvis.planner_services import start_focus_session

        try:
            body = await request.json()
        except Exception:
            body = {}
        return start_focus_session(
            duration=body.get("duration") or "25 minutes",
            label=body.get("label") or "Focus",
            use_ha=body.get("use_ha"),
        )

    @app.post("/api/planner/focus/end")
    async def planner_focus_end(request: Request):
        from jarvis.planner_services import end_focus_session

        try:
            body = await request.json()
        except Exception:
            body = {}
        return end_focus_session(restore_ha=body.get("restore_ha", True))

    @app.post("/api/planner/vision/extract")
    async def planner_vision_extract(request: Request):
        from jarvis.planner_services import vision_extract_tasks

        body = await request.json()
        return vision_extract_tasks(str(body.get("path") or ""), assistant=assistant)

    @app.post("/api/planner/vision/import")
    async def planner_vision_import(request: Request):
        from jarvis.planner_services import import_vision_tasks

        body = await request.json()
        return import_vision_tasks(body.get("candidates") or [])

    @app.post("/api/planner/schedule/suggest")
    async def planner_schedule_suggest(request: Request):
        from jarvis.planner_services import suggest_schedule

        try:
            body = await request.json()
        except Exception:
            body = {}
        return suggest_schedule(body.get("task_ids"))

    @app.post("/api/planner/schedule/apply")
    async def planner_schedule_apply(request: Request):
        from jarvis.planner_services import apply_schedule_suggestion

        body = await request.json()
        try:
            ev = apply_schedule_suggestion(body.get("suggestion") or body)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "event": ev}

    @app.get("/api/planner/prefs")
    def planner_prefs_get():
        from jarvis.planner_store import get_pref

        return {
            "ok": True,
            "ha_focus_enabled": bool(get_pref("ha_focus_enabled", False)),
            "notify_sound": bool(get_pref("notify_sound", True)),
        }

    @app.post("/api/planner/prefs")
    async def planner_prefs_set(request: Request):
        from jarvis.planner_store import get_pref, set_pref

        body = await request.json()
        if "ha_focus_enabled" in body:
            set_pref("ha_focus_enabled", bool(body.get("ha_focus_enabled")))
        if "notify_sound" in body:
            set_pref("notify_sound", bool(body.get("notify_sound")))
        return {
            "ok": True,
            "ha_focus_enabled": bool(get_pref("ha_focus_enabled", False)),
            "notify_sound": bool(get_pref("notify_sound", True)),
        }

    @app.get("/api/system-info")
    def system_info_route():
        from jarvis.system_info import build_system_info

        return {"ok": True, **build_system_info(assistant=assistant)}

    @app.get("/api/monitor")
    def monitor_route():
        from jarvis.system_monitor import collect_stats

        return {"ok": True, **collect_stats()}

    @app.get("/api/checklist")
    def checklist_route(full: bool = False):
        from jarvis.p0_checklist import run_checklist

        return run_checklist(assistant=assistant, full=full)

    @app.get("/api/world-state")
    @app.get("/api/world_state")
    def world_state_route(force: bool = False):
        from jarvis.world_state import refresh_world_state_cache, world_state_enabled

        if not world_state_enabled():
            return {"ok": True, "enabled": False, "state": {}}
        state = refresh_world_state_cache(force=force, memory_store=assistant.memory)
        return {"ok": True, "enabled": True, "state": state}

    @app.get("/api/curated-news")
    def curated_news_route(use_ai: bool = True, category: str = ""):
        try:
            from jarvis.curated_news import get_curated_headlines

            return {"ok": True, **get_curated_headlines(use_ai=use_ai, category=category)}
        except Exception as exc:
            return {"ok": False, "headlines": [], "message": str(exc)}

    @app.post("/api/tool-confirm")
    async def tool_confirm(request: Request):
        from jarvis.tool_permissions import execute_confirm

        body = await request.json()
        confirm_id = (body.get("id") or "").strip()
        approved = bool(body.get("approved"))
        outcome = execute_confirm(confirm_id, approved, assistant=assistant)
        status = outcome["status"]
        if status == "expired":
            return JSONResponse(
                status_code=404, content={"ok": False, "message": outcome["message"]}
            )
        if status == "declined":
            return {"ok": True, "approved": False, "message": outcome["message"]}
        if status == "unknown_action":
            return {"ok": False, "approved": True, "message": outcome["message"]}
        return {"ok": True, "approved": True, "result": outcome["result"]}
