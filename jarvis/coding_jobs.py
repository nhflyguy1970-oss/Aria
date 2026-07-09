"""Background queue for long coding-agent runs (LLM-heavy, non-GPU)."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Callable

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.coding_jobs")

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_queue: queue.Queue[tuple[str, Callable[[], dict]]] | None = None
_workers: list[threading.Thread] = []
_active_ids: set[str] = set()
_history: deque[str] = deque(maxlen=32)
_state_file = DATA_DIR / "coding_jobs_state.json"
_loaded = False

JOB_TIMEOUT_SEC = float(os.getenv("JARVIS_CODING_JOB_TIMEOUT_SEC", "1800"))
WORKER_COUNT = max(1, min(4, int(os.getenv("JARVIS_CODING_WORKERS", "1"))))
_stats = {"completed": 0, "failed": 0, "cancelled": 0}


def _cap_job_result(result: dict) -> dict:
    """Strip heavy proposal fields before UI poll (WebKit/pywebview OOM)."""
    if not isinstance(result, dict):
        return result
    from jarvis.response import cap_stream_payload

    out = cap_stream_payload(dict(result), lite_ui=True)
    out.pop("agent_steps", None)
    diags = out.get("diagnostics")
    if isinstance(diags, list) and len(diags) > 4:
        out["diagnostics"] = diags[:4]
    impact = out.get("test_impact")
    if isinstance(impact, str) and len(impact) > 400:
        out["test_impact"] = impact[:400] + "…"
    return out


def _persist_state() -> None:
    try:
        _state_file.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            payload = {
                "jobs": [dict(_jobs[i]) for i in _history if i in _jobs][-24:],
                "stats": dict(_stats),
            }
        _state_file.write_text(json.dumps(payload, default=str), encoding="utf-8")
    except OSError:
        pass


def _load_persisted_state() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    if not _state_file.is_file():
        return
    try:
        data = json.loads(_state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    with _lock:
        for key, val in (data.get("stats") or {}).items():
            if key in _stats and isinstance(val, int):
                _stats[key] = val
        for item in data.get("jobs", []):
            jid = item.get("id")
            if jid and jid not in _jobs:
                _jobs[jid] = dict(item)
                _history.append(jid)


def job_stats() -> dict[str, Any]:
    with _lock:
        pending = _queue.qsize() if _queue else 0
        return {
            "busy": bool(_active_ids),
            "pending": pending,
            "active_id": next(iter(_active_ids), None),
            "active_ids": list(_active_ids),
            "workers": WORKER_COUNT,
            "completed": _stats["completed"],
            "failed": _stats["failed"],
            "cancelled": _stats["cancelled"],
        }


def has_active_work() -> bool:
    """True while a coding job is queued or running (survives until worker finishes)."""
    st = job_stats()
    return bool(st.get("busy") or st.get("pending"))


def _ensure_workers() -> None:
    global _queue, _workers
    _load_persisted_state()
    if _queue is None:
        _queue = queue.Queue()
    alive = [w for w in _workers if w.is_alive()]
    _workers = alive
    while len(_workers) < WORKER_COUNT:
        t = threading.Thread(
            target=_worker_loop,
            name=f"jarvis-coding-queue-{len(_workers)}",
            daemon=True,
        )
        t.start()
        _workers.append(t)


def _is_cancelled(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        return bool(job and job.get("cancelled"))


def append_step(job_id: str, step: dict[str, Any]) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        steps = job.setdefault("steps", [])
        steps.append(step)
        if len(steps) > 40:
            job["steps"] = steps[-40:]
        job["message"] = f"{step.get('action', 'step')}: {step.get('detail', '')}"[:120]


def cancel_job(job_id: str) -> bool:
    from jarvis.modules.workflow_orchestration_adapter import workflow_cancel

    return workflow_cancel("coding", job_id, _cancel_job_impl, job_id)


def _cancel_job_impl(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job or job.get("done"):
            return False
        job["cancelled"] = True
        job["message"] = "Cancelling…"
        if job_id not in _active_ids:
            job["done"] = True
            job["pct"] = 100
            job["result"] = {"ok": False, "message": "Cancelled before start"}
            job["error"] = "Cancelled"
            _stats["cancelled"] += 1
        return True


def _worker_loop() -> None:
    global _queue
    assert _queue is not None
    while True:
        job_id, fn = _queue.get()
        try:
            if _is_cancelled(job_id):
                continue
            deadline = time.time() + JOB_TIMEOUT_SEC
            with _lock:
                job = _jobs.get(job_id)
                if not job or job.get("cancelled"):
                    if job and job.get("cancelled") and not job.get("done"):
                        job["done"] = True
                        job["pct"] = 100
                        job["result"] = {"ok": False, "message": "Cancelled"}
                        job["error"] = "Cancelled"
                        _stats["cancelled"] += 1
                    continue
                _active_ids.add(job_id)
                job["message"] = "Running…"
                job["pct"] = 5
            try:
                result = fn()
                if _is_cancelled(job_id):
                    result = {"ok": False, "message": "Cancelled"}
                elif time.time() > deadline:
                    result = {"ok": False, "message": f"Coding task timed out after {int(JOB_TIMEOUT_SEC)}s"}
            except Exception as exc:
                logger.exception("Coding job %s failed", job_id)
                result = {"ok": False, "message": str(exc)}
            if isinstance(result, dict) and result.get("ok") and result.get("proposal_id"):
                result = _cap_job_result(result)
            with _lock:
                job = _jobs.get(job_id)
                if job:
                    job["done"] = True
                    job["pct"] = 100
                    job["result"] = result
                    if job.get("cancelled"):
                        job["message"] = "Cancelled"
                        job["error"] = "Cancelled"
                        _stats["cancelled"] += 1
                    elif result.get("ok"):
                        job["message"] = "Complete"
                        _stats["completed"] += 1
                    else:
                        job["message"] = result.get("message") or "Failed"
                        job["error"] = job["message"]
                        _stats["failed"] += 1
                    try:
                        from jarvis.events import emit_job_done

                        emit_job_done(
                            queue="coding",
                            job_id=job_id,
                            result=result,
                            label=job.get("label") or "coding",
                        )
                    except Exception:
                        pass
            _persist_state()
        finally:
            with _lock:
                _active_ids.discard(job_id)
            _queue.task_done()


def submit(label: str, fn: Callable[[], dict]) -> str:
    from jarvis.modules.workflow_orchestration_adapter import workflow_enqueue

    return workflow_enqueue("coding", label, _submit_impl, label, fn)


def _submit_impl(label: str, fn: Callable[[], dict]) -> str:
    _ensure_workers()
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "label": label,
            "pct": 0,
            "message": "Queued…",
            "done": False,
            "error": "",
            "result": None,
            "steps": [],
            "cancelled": False,
            "started": time.time(),
        }
        _history.append(job_id)
    assert _queue is not None
    _queue.put((job_id, fn))
    _persist_state()
    return job_id


def submit_coding_agent(assistant, params: dict, message: str) -> str:
    job_id_ref: dict[str, str] = {"id": ""}

    def _run() -> dict:
        def on_step(step: dict) -> None:
            append_step(job_id_ref["id"], step)

        return assistant._coding_agent(params, message, on_step=on_step)

    job_id = submit(
        params.get("task") or message[:80] or "Coding agent",
        _run,
    )
    job_id_ref["id"] = job_id
    return job_id


def submit_fix_tests(assistant, params: dict, message: str) -> str:
    path = (params.get("path") or "tests").strip()
    label = f"Fix tests: {path}"[:80]
    return submit(label, lambda: assistant._coding_fix_tests(params, message))


def submit_coding_create(assistant, params: dict, message: str) -> str:
    label = (params.get("description") or message or "Create script")[:80]
    return submit(label, lambda: assistant._coding_create(params, message))


def submit_coding_propose(
    assistant,
    path: str,
    mode: str,
    *,
    task: str | None = None,
    editor_prompt: str = "",
) -> str:
    label = f"{mode} {path}"[:80]
    return submit(
        label,
        lambda: assistant._coding_propose(
            path, mode, task=task, editor_prompt=editor_prompt,
        ),
    )


def get_job(job_id: str) -> dict | None:
    _load_persisted_state()
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def list_recent(limit: int = 10) -> list[dict]:
    with _lock:
        ids = list(_history)[-limit:]
        return [dict(_jobs[i]) for i in reversed(ids) if i in _jobs]
