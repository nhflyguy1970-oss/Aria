"""HTTP API for Latency Observability."""

from __future__ import annotations


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    from fastapi import Request
    from fastapi.responses import JSONResponse, PlainTextResponse, Response

    @app.get("/api/latency/live")
    def latency_live():
        from jarvis.latency_observability.trace import live_traces

        return {"ok": True, "live": live_traces()}

    @app.get("/api/latency/stats")
    def latency_stats():
        from jarvis.latency_observability.metrics import stats_payload

        return stats_payload()

    @app.get("/api/latency/diagnostics")
    def latency_diagnostics():
        from jarvis.latency_observability.metrics import diagnostics

        return diagnostics()

    @app.get("/api/latency/trace/{trace_id}")
    def latency_trace(trace_id: str):
        from jarvis.latency_observability.export import resolve_trace

        row = resolve_trace(trace_id)
        if not row:
            return JSONResponse({"ok": False, "message": "not found"}, status_code=404)
        return {"ok": True, "trace": row}

    @app.get("/api/latency/search")
    def latency_search(
        q: str = "",
        provider: str = "",
        model: str = "",
        subsystem: str = "",
        min_ms: float | None = None,
        error: str = "",
        limit: int = 40,
    ):
        from jarvis.latency_observability.store import search_traces

        return {
            "ok": True,
            "results": search_traces(
                q,
                limit=max(1, min(200, int(limit or 40))),
                provider=provider,
                model=model,
                subsystem=subsystem,
                min_latency_ms=min_ms,
                error_class=error,
            ),
        }

    @app.get("/api/latency/export")
    def latency_export(trace_id: str = "", format: str = "json"):
        from jarvis.latency_observability.export import (
            export_csv,
            export_json,
            export_waterfall,
            mission_snapshot,
        )

        fmt = (format or "json").lower().strip()
        if fmt == "csv":
            return Response(
                export_csv(trace_id),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="latency-{trace_id}.csv"'},
            )
        if fmt == "waterfall":
            return export_waterfall(trace_id)
        if fmt == "mission":
            return mission_snapshot(trace_id)
        if fmt == "overlay":
            row = export_json(trace_id)
            if not row.get("ok"):
                return JSONResponse(row, status_code=404)
            return {
                "ok": True,
                "overlay": (row.get("trace") or {}).get("developer_overlay") or [],
                "trace_id": (row.get("trace") or {}).get("trace_id"),
            }
        return export_json(trace_id)

    @app.get("/api/latency/mission")
    def latency_mission():
        from jarvis.latency_observability.mission_bridge import mission_panel

        return {"ok": True, **mission_panel()}

    @app.get("/api/mission-control/latency")
    def mc_latency():
        from jarvis.latency_observability.mission_bridge import mission_panel

        return {"ok": True, **mission_panel()}
