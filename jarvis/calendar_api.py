"""Calendar HTTP API — owned by Calendar (not Planner)."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:

    @app.get("/api/calendar/product")
    def calendar_product():
        from jarvis.calendar_bridges import product_status

        return product_status()

    @app.get("/api/calendar/mission")
    def calendar_mission():
        from jarvis.calendar_bridges import mission_status

        return mission_status()

    @app.get("/api/calendar/dashboard")
    def calendar_dashboard():
        from jarvis.calendar_bridges import dashboard_summary

        return dashboard_summary(getattr(assistant, "journal", None))

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
        from jarvis.calendar_time import today_iso

        return day_detail(assistant.journal, day or today_iso())

    @app.get("/api/calendar/week")
    def calendar_week(anchor: str = ""):
        from jarvis.calendar_tab import week_overview

        return week_overview(assistant.journal, anchor or None)

    @app.get("/api/calendar/agenda")
    def calendar_agenda(days: int = 7, start: str = ""):
        from jarvis.calendar_tab import agenda_overview

        return agenda_overview(assistant.journal, days=min(max(days, 1), 21), start=start or None)

    @app.get("/api/calendar/timeline")
    def calendar_timeline(day: str = ""):
        from jarvis.calendar_tab import timeline_overview

        return timeline_overview(assistant.journal, day or None)

    @app.post("/api/calendar/items")
    async def calendar_create_item(request: Request):
        from jarvis.calendar_notify import notify_commitment_created
        from jarvis.calendar_schedule import create_commitment

        body = await request.json()
        try:
            out = create_commitment(
                assistant.journal,
                title=body.get("title") or body.get("content") or "",
                day=body.get("day") or body.get("date"),
                time=body.get("time"),
                target=body.get("target") or "planner",
                duration_min=int(body.get("duration_min") or 30),
            )
            notify_commitment_created(out)
            return out
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/calendar/items/{item_id}/update")
    async def calendar_update_item(item_id: str, request: Request):
        from jarvis.calendar_schedule import update_commitment

        body = await request.json()
        try:
            return update_commitment(
                assistant.journal,
                item_id,
                title=body.get("title") or body.get("content"),
                time=body.get("time"),
                day=body.get("day") or body.get("date"),
                duration_min=body.get("duration_min"),
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.delete("/api/calendar/items/{item_id}")
    def calendar_delete_item(item_id: str):
        from jarvis.calendar_schedule import delete_commitment

        try:
            return delete_commitment(assistant.journal, item_id)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/calendar/items/{item_id}/duplicate")
    async def calendar_duplicate_item(item_id: str, request: Request):
        from jarvis.calendar_schedule import duplicate_commitment

        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            return duplicate_commitment(assistant.journal, item_id, day=body.get("day"))
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/calendar/items/{item_id}/complete")
    def calendar_complete_item(item_id: str):
        from jarvis.calendar_schedule import complete_commitment

        try:
            return complete_commitment(assistant.journal, item_id)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.get("/api/calendar/ics/status")
    def calendar_ics_status():
        from jarvis.calendar_ics import sync_status

        return {"ok": True, **sync_status()}

    @app.post("/api/calendar/ics/refresh")
    def calendar_ics_refresh():
        from jarvis.calendar_ics import refresh_ics
        from jarvis.calendar_notify import notify_ics_issue

        out = refresh_ics(force=True)
        if not out.get("ok"):
            notify_ics_issue(out.get("message") or "ICS refresh failed")
        return out

    @app.post("/api/calendar/ics")
    async def calendar_ics_save(request: Request):
        """Save or validate ICS URL (Calendar-owned; wraps env persistence helpers)."""
        from jarvis.movie_tiers import save_ics_url, validate_ics_url

        try:
            body = await request.json()
        except Exception:
            body = {}
        url = (body.get("url") or "").strip()
        if body.get("test_only"):
            return validate_ics_url(url)
        return save_ics_url(url)

    @app.post("/api/calendar/nl")
    async def calendar_nl(request: Request):
        from jarvis.calendar_services import parse_natural_schedule

        body = await request.json()
        return parse_natural_schedule(body.get("text") or body.get("message") or "")

    @app.post("/api/calendar/nl/confirm")
    async def calendar_nl_confirm(request: Request):
        from jarvis.calendar_notify import notify_commitment_created
        from jarvis.calendar_schedule import create_commitment

        body = await request.json()
        proposal = body.get("proposal") or body
        if not body.get("confirmed"):
            return {"ok": False, "message": "Confirmation required"}
        try:
            out = create_commitment(
                assistant.journal,
                title=proposal.get("title") or "",
                day=proposal.get("day"),
                time=proposal.get("time"),
                target=proposal.get("target") or "planner",
            )
            notify_commitment_created(out)
            return out
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.get("/api/calendar/conflicts")
    def calendar_conflicts(day: str = ""):
        from jarvis.calendar_notify import notify_conflicts
        from jarvis.calendar_services import detect_conflicts

        out = detect_conflicts(assistant.journal, day or None)
        conflicts = out.get("conflicts") or []
        if conflicts:
            notify_conflicts(out.get("day") or "", len(conflicts))
        return out

    @app.post("/api/calendar/prep")
    async def calendar_prep(request: Request):
        from jarvis.calendar_services import meeting_prep

        try:
            body = await request.json()
        except Exception:
            body = {}
        return meeting_prep(assistant.journal, body.get("item_id"), assistant=assistant)

    @app.get("/api/calendar/focus-suggestions")
    def calendar_focus_suggestions(day: str = ""):
        from jarvis.calendar_services import focus_suggestions

        return focus_suggestions(assistant.journal, day or None)

    @app.get("/api/calendar/memory-dates")
    def calendar_memory_dates():
        from jarvis.calendar_services import memory_dates

        return memory_dates(assistant)

    @app.post("/api/calendar/vision/extract")
    async def calendar_vision_extract(request: Request):
        from jarvis.calendar_services import vision_extract_events

        body = await request.json()
        return vision_extract_events(body.get("path") or "")

    @app.post("/api/calendar/vision/import")
    async def calendar_vision_import(request: Request):
        from jarvis.calendar_notify import notify_commitment_created
        from jarvis.calendar_services import import_vision_events

        body = await request.json()
        out = import_vision_events(assistant.journal, body.get("candidates") or [])
        if out.get("count"):
            notify_commitment_created(
                {"title": f"Imported {out['count']} event(s)", "item_id": "vision-import"}
            )
        return out

    @app.post("/api/calendar/ha-mode")
    async def calendar_ha_mode(request: Request):
        from jarvis.calendar_services import ha_calendar_mode

        body = await request.json()
        return ha_calendar_mode(body.get("mode") or "off", enabled=body.get("enabled"))

    @app.get("/api/calendar/work-schedule")
    def calendar_work_schedule_get():
        from jarvis.calendar_ics import ics_url, sync_status
        from jarvis.calendar_store import load_work_schedule

        sched = load_work_schedule()
        sched["ics_url"] = ics_url()
        sched["ics_status"] = sync_status()
        return sched

    @app.put("/api/calendar/work-schedule")
    @app.post("/api/calendar/work-schedule")
    async def calendar_work_schedule_put(request: Request):
        from jarvis.calendar_store import save_work_schedule

        body = await request.json()
        saved = save_work_schedule(body)
        return {"ok": True, **saved}
