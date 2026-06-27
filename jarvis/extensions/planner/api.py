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
        from jarvis.planner_store import tick_alarms_and_timers

        return {"ok": True, "notifications": tick_alarms_and_timers()}

    @app.get("/api/calendar/month")
    def calendar_month(month: str = "", year: int = 0, month_num: int = 0):
        from jarvis.calendar_tab import month_overview
        from jarvis.modules.journal import _month_key

        mk = (month or "").strip()
        if not mk and year and month_num:
            mk = f"{year}-{month_num:02d}"
        return month_overview(assistant.journal, mk or _month_key())

    @app.get("/api/calendar/day")
    def calendar_day(day: str = ""):
        from jarvis.calendar_tab import day_detail
        from jarvis.modules.journal import _today

        return day_detail(assistant.journal, day or _today())

    @app.get("/api/calendar/work-schedule")
    def calendar_work_schedule_get():
        from jarvis.calendar_ics import ics_url
        from jarvis.calendar_store import load_work_schedule

        sched = load_work_schedule()
        sched["ics_url"] = ics_url()
        return sched

    @app.put("/api/calendar/work-schedule")
    async def calendar_work_schedule_put(request: Request):
        from jarvis.calendar_store import save_work_schedule

        body = await request.json()
        saved = save_work_schedule(body)
        return {"ok": True, **saved}

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
    def curated_news_route(use_ai: bool = True):
        try:
            from jarvis.curated_news import get_curated_headlines

            return {"ok": True, **get_curated_headlines(use_ai=use_ai)}
        except Exception as exc:
            return {"ok": False, "headlines": [], "message": str(exc)}

    @app.post("/api/tool-confirm")
    async def tool_confirm(request: Request):
        from jarvis.tool_permissions import pop_pending

        body = await request.json()
        confirm_id = (body.get("id") or "").strip()
        approved = bool(body.get("approved"))
        row = pop_pending(confirm_id)
        if not row:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Confirm expired."})
        if not approved:
            return {"ok": True, "approved": False, "message": "Cancelled."}
        action = row.get("action") or ""
        params = row.get("params") or {}
        message = row.get("message") or ""
        result = assistant.dispatch(action, params, message)
        return {"ok": True, "approved": True, "result": result}
