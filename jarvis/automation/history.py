"""Automation run history — durable local log for Automation Home + Activity."""

from __future__ import annotations

import json
import threading
import time
import uuid
from typing import Any

from jarvis.automation.paths import RUN_HISTORY_FILE, ensure_dirs

_lock = threading.RLock()
MAX_RUNS = 300


def _load() -> list[dict[str, Any]]:
    ensure_dirs()
    if not RUN_HISTORY_FILE.is_file():
        return []
    try:
        data = json.loads(RUN_HISTORY_FILE.read_text(encoding="utf-8"))
        runs = data.get("runs") if isinstance(data, dict) else data
        return list(runs or [])
    except Exception:
        return []


def _save(runs: list[dict[str, Any]]) -> None:
    ensure_dirs()
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(RUN_HISTORY_FILE)
    except Exception:
        pass
    RUN_HISTORY_FILE.write_text(
        json.dumps({"version": 1, "runs": runs[:MAX_RUNS]}, indent=2),
        encoding="utf-8",
    )


def record_run(
    *,
    kind: str,
    name: str,
    status: str,
    source: str = "",
    target_id: str = "",
    why: str = "",
    what_changed: Any = None,
    what_did_not: Any = None,
    dry_run: bool = False,
    executed: bool = False,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "id": f"run_{uuid.uuid4().hex[:12]}",
        "ts": time.time(),
        "kind": kind,
        "name": name,
        "status": status,
        "source": source,
        "target_id": target_id,
        "why": why,
        "what_changed": what_changed,
        "what_did_not": what_did_not,
        "dry_run": dry_run,
        "executed": executed,
        "detail": detail or {},
    }
    with _lock:
        runs = _load()
        runs.insert(0, entry)
        _save(runs)
    return entry


def list_runs(
    *,
    limit: int = 50,
    status: str | None = None,
    kind: str | None = None,
    q: str = "",
) -> list[dict[str, Any]]:
    with _lock:
        runs = _load()
    q = (q or "").strip().lower()
    out = []
    for r in runs:
        if status and r.get("status") != status:
            continue
        if kind and r.get("kind") != kind:
            continue
        if q:
            hay = f"{r.get('name')} {r.get('why')} {r.get('source')} {r.get('kind')}".lower()
            if q not in hay:
                continue
        out.append(r)
        if len(out) >= limit:
            break
    return out


def recent_failures(limit: int = 20) -> list[dict[str, Any]]:
    return list_runs(limit=limit, status="failed")


def clear_history() -> dict[str, Any]:
    with _lock:
        _save([])
    return {"ok": True}
