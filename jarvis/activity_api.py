"""HTTP API for server-authoritative Activity inbox."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def register_activity_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/activity/inbox")
    def activity_inbox(include_dismissed: bool = False, limit: int = 100):
        from jarvis.activity_inbox import list_items

        return list_items(include_dismissed=include_dismissed, limit=limit, channel="owner")

    @app.post("/api/activity/publish")
    async def activity_publish(request: Request):
        from jarvis.activity_inbox import publish

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON required"})
        return publish(
            kind=str(body.get("kind") or "info"),
            title=str(body.get("title") or ""),
            body=str(body.get("body") or body.get("message") or ""),
            source=str(body.get("source") or "api"),
            meta=body.get("meta") if isinstance(body.get("meta"), dict) else {},
            event_id=str(body.get("id") or body.get("event_id") or "") or None,
        )

    @app.post("/api/activity/dismiss")
    async def activity_dismiss(request: Request):
        from jarvis.activity_inbox import dismiss

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return dismiss(str((body or {}).get("id") or ""))

    @app.post("/api/activity/read")
    async def activity_read(request: Request):
        from jarvis.activity_inbox import mark_read

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return mark_read(str((body or {}).get("id") or ""))

    @app.post("/api/activity/read-all")
    def activity_read_all():
        from jarvis.activity_inbox import mark_all_read

        return mark_all_read()

    @app.post("/api/activity/clear-read")
    def activity_clear_read():
        from jarvis.activity_inbox import clear_read

        return clear_read()

    @app.post("/api/activity/clear-all")
    def activity_clear_all():
        from jarvis.activity_inbox import clear_all

        return clear_all()
