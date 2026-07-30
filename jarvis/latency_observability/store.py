"""Persistent latency traces (JSONL) — Search / diagnostics source."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "latency_observability" / "traces.jsonl"
_MAX_LINES = 3000


def append_trace(trace) -> dict[str, Any]:
    row = trace.to_dict() if hasattr(trace, "to_dict") else dict(trace)
    row["kind"] = "latency_trace"
    row["ts"] = time.time()
    row["iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    _trim()
    # Mirror a compact event into Provider Health history for long-term trends.
    try:
        from jarvis.provider_health.history import append_event

        append_event(
            {
                "kind": "latency",
                "trace_id": row.get("trace_id"),
                "request_id": row.get("request_id"),
                "provider": (row.get("provider") or {}).get("provider") or "ollama",
                "model": (row.get("provider") or {}).get("model")
                or (row.get("model") or {}).get("model"),
                "first_token_ms": (row.get("stream") or {}).get("first_token_ms"),
                "elapsed_ms": row.get("elapsed_ms"),
                "ok": row.get("ok"),
                "action": row.get("action"),
                "slowest": (row.get("slowest") or {}).get("name"),
            }
        )
    except Exception:
        pass
    return row


def load_traces(*, limit: int = 80) -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def get_stored_trace(trace_id: str) -> dict[str, Any] | None:
    tid = (trace_id or "").strip()
    if not tid:
        return None
    for row in load_traces(limit=800):
        if row.get("trace_id") == tid or row.get("request_id") == tid:
            return row
    return None


def search_traces(
    query: str = "",
    *,
    limit: int = 40,
    provider: str = "",
    model: str = "",
    subsystem: str = "",
    min_latency_ms: float | None = None,
    error_class: str = "",
) -> list[dict[str, Any]]:
    q = (query or "").lower().strip()
    prov = (provider or "").lower().strip()
    mod = (model or "").lower().strip()
    sub = (subsystem or "").lower().strip()
    err = (error_class or "").lower().strip()
    hits: list[dict[str, Any]] = []
    for row in load_traces(limit=800):
        if prov and prov not in str((row.get("provider") or {}).get("provider") or "").lower():
            continue
        if mod and mod not in str(
            (row.get("provider") or {}).get("model") or (row.get("model") or {}).get("model") or ""
        ).lower():
            continue
        if min_latency_ms is not None and float(row.get("elapsed_ms") or 0) < float(min_latency_ms):
            continue
        if err:
            blob_err = " ".join(str(x) for x in (row.get("errors") or [])).lower()
            if err not in blob_err and err not in str(row.get("ok")).lower():
                continue
        if sub:
            stage_names = " ".join(s.get("name", "") for s in (row.get("stages") or [])).lower()
            ctx = " ".join((row.get("context") or {}).get("sources") or {}).keys()
            if sub not in stage_names and sub not in ctx.lower() and sub not in str(row.get("slowest") or "").lower():
                continue
        if q:
            blob = json.dumps(row, default=str).lower()
            if q not in blob:
                continue
        hits.append(row)
        if len(hits) >= limit:
            break
    return hits


def _trim() -> None:
    if not HISTORY_FILE.is_file():
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > _MAX_LINES:
            HISTORY_FILE.write_text("\n".join(lines[-_MAX_LINES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def history_path() -> Path:
    return HISTORY_FILE
