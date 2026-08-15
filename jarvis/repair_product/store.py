"""Persistent repair history and learning stats."""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

REPAIR_DIR = DATA_DIR / "repair_product"
HISTORY_PATH = REPAIR_DIR / "history.jsonl"
ISSUES_PATH = REPAIR_DIR / "issues.json"
LEARNING_PATH = REPAIR_DIR / "learning.json"
AUTO_APPROVE_PATH = REPAIR_DIR / "auto_approve.json"
KNOWLEDGE_PATH = REPAIR_DIR / "knowledge.json"
ROOT_CAUSES_PATH = REPAIR_DIR / "root_causes.json"
MAINTENANCE_PATH = REPAIR_DIR / "maintenance.json"
MONITORS_PATH = REPAIR_DIR / "monitors.json"

_lock = threading.RLock()


def ensure_dirs() -> None:
    REPAIR_DIR.mkdir(parents=True, exist_ok=True)


def new_id(prefix: str = "rep") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    ensure_dirs()
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def append_history(entry: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    row = {
        "id": entry.get("id") or new_id("hist"),
        "ts": entry.get("ts") or time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **entry,
    }
    with _lock:
        with HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
        _update_learning(row)
    try:
        from jarvis.repair_product import knowledge, root_causes

        knowledge.remember_from_history(row)
        root_causes.record_outcome(
            str(row.get("module_id") or ""),
            str(row.get("code") or ""),
            success=bool(row.get("verified_ok")),
            plan_steps=str(row.get("plan_steps") or ""),
        )
    except Exception:
        pass
    return row


def list_history(
    *,
    limit: int = 50,
    subsystem: str = "",
    result: str = "",
    successful: bool | None = None,
    module_id: str = "",
    q: str = "",
    since_ts: float | None = None,
    priority: str = "",
) -> list[dict[str, Any]]:
    if not HISTORY_PATH.is_file():
        return []
    with _lock:
        lines = HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    ql = (q or "").strip().lower()
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if subsystem and str(row.get("subsystem") or "").lower() != subsystem.lower():
            continue
        if module_id and str(row.get("module_id") or "") != module_id:
            continue
        if result and str(row.get("result") or "") != result:
            continue
        if priority and str(row.get("priority") or "") != priority:
            continue
        if successful is True and not row.get("verified_ok"):
            continue
        if successful is False and row.get("verified_ok"):
            continue
        if since_ts is not None and float(row.get("ts") or 0) < since_ts:
            continue
        if ql:
            blob = f"{row.get('title')} {row.get('diagnosis')} {row.get('message')} {row.get('subsystem')}".lower()
            if ql not in blob:
                continue
        out.append(row)
    out.sort(key=lambda r: float(r.get("ts") or 0), reverse=True)
    return out[: max(1, limit)]


def save_issue(issue: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        data = _read_json(ISSUES_PATH, {"issues": {}})
        issues = data.setdefault("issues", {})
        iid = issue.get("id") or new_id("iss")
        issue["id"] = iid
        issue["updated_at"] = time.time()
        issues[iid] = issue
        _write_json(ISSUES_PATH, data)
    return issue


def get_issue(issue_id: str) -> dict[str, Any] | None:
    data = _read_json(ISSUES_PATH, {"issues": {}})
    return (data.get("issues") or {}).get(issue_id)


def list_issues(*, active_only: bool = True) -> list[dict[str, Any]]:
    data = _read_json(ISSUES_PATH, {"issues": {}})
    rows = list((data.get("issues") or {}).values())
    if active_only:
        rows = [
            r
            for r in rows
            if r.get("state")
            not in (
                "repair_successful",
                "repair_failed",
                "unsafe_to_repair",
            )
        ]
    rows.sort(key=lambda r: float(r.get("updated_at") or r.get("created_at") or 0), reverse=True)
    return rows


def update_issue(issue_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    with _lock:
        data = _read_json(ISSUES_PATH, {"issues": {}})
        issues = data.setdefault("issues", {})
        row = issues.get(issue_id)
        if not row:
            return None
        row.update(updates)
        row["updated_at"] = time.time()
        issues[issue_id] = row
        _write_json(ISSUES_PATH, data)
        return row


def learning_stats() -> dict[str, Any]:
    return _read_json(
        LEARNING_PATH,
        {
            "common_failures": {},
            "successful_repairs": {},
            "failed_repairs": {},
            "fastest_repairs": {},
            "avg_duration": {},
            "avg_confidence": {},
            "last_success_ts": {},
            "repeat_failures": {},
            "sequences": {},
        },
    )


def _update_learning(row: dict[str, Any]) -> None:
    stats = learning_stats()
    module = str(row.get("module_id") or row.get("subsystem") or "unknown")
    code = str(row.get("code") or row.get("title") or "unknown")
    key = f"{module}:{code}"
    common = stats.setdefault("common_failures", {})
    common[key] = int(common.get(key) or 0) + 1
    bucket = "successful_repairs" if row.get("verified_ok") else "failed_repairs"
    b = stats.setdefault(bucket, {})
    b[key] = int(b.get(key) or 0) + 1
    if row.get("duration_seconds") is not None:
        avg = stats.setdefault("avg_duration", {})
        prev = avg.get(key)
        dur = float(row["duration_seconds"])
        n = int(b.get(key) or 1)
        if prev is None:
            avg[key] = dur
        else:
            avg[key] = round((float(prev) * (n - 1) + dur) / max(1, n), 3)
        fast = stats.setdefault("fastest_repairs", {})
        if row.get("verified_ok") and (fast.get(key) is None or dur < float(fast[key])):
            fast[key] = dur
    if row.get("confidence") is not None:
        ac = stats.setdefault("avg_confidence", {})
        prev = ac.get(key)
        c = float(row["confidence"])
        ac[key] = c if prev is None else round((float(prev) + c) / 2, 3)
    if row.get("verified_ok"):
        stats.setdefault("last_success_ts", {})[key] = row.get("ts") or time.time()
        stats.setdefault("repeat_failures", {})[module] = 0
    else:
        rf = stats.setdefault("repeat_failures", {})
        rf[module] = int(rf.get(module) or 0) + 1
    seq = str(row.get("plan_steps") or "")
    if seq and row.get("verified_ok"):
        sequences = stats.setdefault("sequences", {})
        sequences[seq] = int(sequences.get(seq) or 0) + 1
    _write_json(LEARNING_PATH, stats)


def auto_approve_list() -> list[str]:
    data = _read_json(AUTO_APPROVE_PATH, {"modules": []})
    return list(data.get("modules") or [])


def set_auto_approve(modules: list[str]) -> dict[str, Any]:
    payload = {"modules": sorted({str(m).strip() for m in modules if str(m).strip()})}
    _write_json(AUTO_APPROVE_PATH, payload)
    return payload


def is_auto_approved(module_id: str) -> bool:
    return module_id in set(auto_approve_list())


def knowledge_articles() -> dict[str, Any]:
    return _read_json(KNOWLEDGE_PATH, {})


def save_knowledge_article(key: str, article: dict[str, Any]) -> None:
    with _lock:
        data = knowledge_articles()
        data[key] = article
        _write_json(KNOWLEDGE_PATH, data)


def root_cause_library() -> dict[str, Any]:
    return _read_json(ROOT_CAUSES_PATH, {})


def save_root_cause_library(data: dict[str, Any]) -> None:
    _write_json(ROOT_CAUSES_PATH, data)


def maintenance_state() -> dict[str, Any]:
    return _read_json(MAINTENANCE_PATH, {"enabled": False})


def save_maintenance_state(data: dict[str, Any]) -> None:
    _write_json(MAINTENANCE_PATH, data)


def list_monitors() -> dict[str, Any]:
    return _read_json(MONITORS_PATH, {})


def get_monitor(issue_id: str) -> dict[str, Any] | None:
    return list_monitors().get(issue_id)


def save_monitor(issue_id: str, mon: dict[str, Any]) -> None:
    with _lock:
        data = list_monitors()
        data[issue_id] = mon
        _write_json(MONITORS_PATH, data)
