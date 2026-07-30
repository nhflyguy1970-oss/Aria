"""Export latency traces — JSON / CSV / waterfall / Mission Control snapshot."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from jarvis.latency_observability.store import get_stored_trace
from jarvis.latency_observability.trace import get_trace


def resolve_trace(trace_id: str) -> dict[str, Any] | None:
    tid = (trace_id or "").strip()
    if not tid:
        return None
    live = get_trace(tid)
    if live is not None:
        return live.to_dict()
    return get_stored_trace(tid)


def export_json(trace_id: str) -> dict[str, Any]:
    row = resolve_trace(trace_id)
    if not row:
        return {"ok": False, "message": f"Trace not found: {trace_id}"}
    return {"ok": True, "format": "json", "trace": row}


def export_waterfall(trace_id: str) -> dict[str, Any]:
    row = resolve_trace(trace_id)
    if not row:
        return {"ok": False, "message": f"Trace not found: {trace_id}"}
    return {
        "ok": True,
        "format": "waterfall",
        "trace_id": row.get("trace_id"),
        "waterfall": row.get("waterfall")
        or [
            {
                "stage": s.get("name"),
                "elapsed_ms": s.get("elapsed_ms"),
                **{k: v for k, v in s.items() if k not in ("name", "elapsed_ms", "running")},
            }
            for s in (row.get("stages") or [])
        ],
        "context": row.get("context"),
        "provider": row.get("provider"),
        "stream": row.get("stream"),
        "developer_overlay": row.get("developer_overlay"),
    }


def export_csv(trace_id: str) -> str:
    row = resolve_trace(trace_id)
    if not row:
        return "error,trace not found\n"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["trace_id", "request_id", "stage", "elapsed_ms", "meta"])
    for s in row.get("stages") or []:
        meta = {k: v for k, v in s.items() if k not in ("name", "elapsed_ms", "running")}
        w.writerow(
            [
                row.get("trace_id"),
                row.get("request_id"),
                s.get("name"),
                s.get("elapsed_ms"),
                json.dumps(meta, default=str),
            ]
        )
    return buf.getvalue()


def mission_snapshot(trace_id: str = "") -> dict[str, Any]:
    from jarvis.latency_observability.metrics import stats_payload

    out: dict[str, Any] = {"ok": True, "stats": stats_payload()}
    if trace_id:
        out["trace"] = resolve_trace(trace_id)
    return out
