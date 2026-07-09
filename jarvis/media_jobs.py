"""Serial background queue for GPU-heavy media work (image, video, meme, inpaint)."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.media_jobs")

_lock = threading.Lock()
_tls = threading.local()
_jobs: dict[str, dict[str, Any]] = {}
_queue: queue.Queue[tuple[str, Callable[[], dict]]] | None = None
_worker: threading.Thread | None = None
_active_id: str | None = None
_active_label: str = ""
_history: deque[str] = deque(maxlen=48)
_state_file = DATA_DIR / "media_jobs_state.json"

JOB_TIMEOUT_SEC = float(os.getenv("JARVIS_MEDIA_JOB_TIMEOUT_SEC", "900"))
JOB_TTL_SEC = float(os.getenv("JARVIS_MEDIA_JOB_TTL_SEC", "86400"))
_stats = {"completed": 0, "failed": 0, "cancelled": 0, "timed_out": 0}
_recovered = False

QUEUED_ACTIONS = frozenset({
    "generate_image",
    "generate_video",
    "generate_meme",
    "upscale_image",
    "inpaint_image",
    "edit_image",
})

ACTION_LABELS = {
    "generate_image": "Image generation",
    "generate_video": "Video render",
    "generate_meme": "Meme generation",
    "upscale_image": "Image upscale",
    "inpaint_image": "Inpaint region",
    "edit_image": "Image edit",
}

ACTION_MODULES = {
    "generate_image": "image",
    "generate_video": "video",
    "generate_meme": "meme",
    "upscale_image": "image",
    "inpaint_image": "image",
    "edit_image": "image",
}

ETA_HINTS = {
    "generate_image": "typically 30–90 seconds",
    "generate_video": "typically 3–10 minutes",
    "generate_meme": "typically 30–90 seconds",
    "upscale_image": "usually under 10 seconds",
    "inpaint_image": "typically 30–120 seconds",
    "edit_image": "typically 30–90 seconds",
}


def eta_hint(action: str) -> str:
    if action == "generate_video":
        try:
            from jarvis.gpu import is_low_vram
            from jarvis.gpu_routing import compute_vram_mb, nvidia_compute_active

            if nvidia_compute_active() and compute_vram_mb() > 10240:
                return "typically 2–8 minutes on NVIDIA GPU"
            if is_low_vram(10240):
                return "may take 5–15 minutes on 8GB GPU"
        except Exception:
            pass
    return ETA_HINTS.get(action, "")


class MediaJobCancelled(Exception):
    pass


def _set_active_job(job_id: str | None) -> None:
    _tls.job_id = job_id


def job_cancelled(job_id: str | None = None) -> bool:
    """True if the given job (or current worker job) was cancelled."""
    jid = job_id or getattr(_tls, "job_id", None)
    if not jid:
        return False
    with _lock:
        job = _jobs.get(jid)
        return bool(job and job.get("cancelled"))


def job_timed_out() -> bool:
    deadline = getattr(_tls, "deadline", None)
    return bool(deadline and time.time() > deadline)


def should_abort_job() -> bool:
    return job_cancelled() or job_timed_out()


def raise_if_cancelled() -> None:
    if job_cancelled():
        raise MediaJobCancelled("Cancelled by user")
    if job_timed_out():
        raise MediaJobCancelled(f"Timed out after {int(JOB_TIMEOUT_SEC)}s")


def job_stats() -> dict[str, Any]:
    with _lock:
        pending = _queue.qsize() if _queue else 0
        return {
            "busy": _active_id is not None,
            "pending": pending,
            "active_id": _active_id,
            "active_label": _active_label,
            "completed": _stats["completed"],
            "failed": _stats["failed"],
            "cancelled": _stats["cancelled"],
            "timed_out": _stats["timed_out"],
            "tracked_jobs": len(_jobs),
        }


def _persist_state() -> None:
    try:
        _state_file.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            payload = {
                "jobs": [dict(_jobs[i]) for i in _history if i in _jobs][-48:],
                "stats": dict(_stats),
            }
        _state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _load_persisted_state() -> None:
    """Restore recent job records after a server restart."""
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


def recover_stale_jobs() -> int:
    """Mark jobs left incomplete after a server crash/restart as failed."""
    global _recovered
    if _recovered:
        return 0
    _recovered = True
    _load_persisted_state()
    count = 0
    with _lock:
        for job in _jobs.values():
            if job.get("done"):
                continue
            count += 1
            job["done"] = True
            job["pct"] = 100
            job["error"] = "Interrupted by server restart"
            job["message"] = job["error"]
            job["result"] = {
                "ok": False,
                "message": (
                    "Image job was interrupted when the server restarted. "
                    "Check **Gallery** — your image may still be there."
                ),
                "module": ACTION_MODULES.get(job.get("kind") or "", "image"),
            }
            _stats["failed"] += 1
            logger.warning("Recovered stale media job %s (%s)", job.get("id"), job.get("kind"))
    if count:
        from jarvis.action_log import log_event

        log_event("media_jobs_recovered", count=count)
        _persist_state()
    return count


def _purge_old_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SEC
    with _lock:
        stale = [jid for jid, job in _jobs.items() if job.get("started", 0) < cutoff]
        for jid in stale:
            _jobs.pop(jid, None)


def _log_job_event(event: str, job_id: str, kind: str, *, ok: bool | None = None, detail: str = "") -> None:
    try:
        from jarvis.action_log import log_event

        log_event(event, job_id=job_id, kind=kind, ok=ok, detail=detail[:300])
    except Exception:
        pass


def _ensure_worker() -> None:
    global _queue, _worker
    recover_stale_jobs()
    if _worker and _worker.is_alive():
        return
    _queue = queue.Queue()
    _worker = threading.Thread(target=_worker_loop, name="jarvis-media-queue", daemon=True)
    _worker.start()


def _worker_loop() -> None:
    global _active_id, _active_label
    assert _queue is not None
    while True:
        job_id, fn = _queue.get()
        try:
            with _lock:
                job = _jobs.get(job_id)
                if not job or job.get("cancelled"):
                    if job:
                        job["done"] = True
                        job["error"] = "Cancelled before start"
                        job["message"] = job["error"]
                    continue
                _active_id = job_id
                _active_label = job.get("label") or job.get("kind") or "Media job"
                job["message"] = "Running…"
                job["pct"] = 5
            _notify_busy_start(_active_label, job.get("kind", ""))
            _set_active_job(job_id)
            _tls.deadline = time.time() + JOB_TIMEOUT_SEC
            kind = job.get("kind") or "media"
            _log_job_event("media_job_start", job_id, kind)
            try:
                from jarvis.resource_router import prepare_for_media_job, record_media_outcome

                prepare_for_media_job(kind)
                result = fn()
                if job_timed_out() and result.get("ok"):
                    result = {"ok": False, "message": f"Timed out after {int(JOB_TIMEOUT_SEC)}s"}
                if result.get("ok"):
                    detail = str(result.get("message") or "")[:200]
                    method = str(
                        result.get("generation_method")
                        or result.get("video_method")
                        or result.get("method")
                        or ""
                    )

                    def _record() -> None:
                        try:
                            record_media_outcome(
                                kind, ok=True, method=method, detail=detail,
                            )
                        except Exception:
                            logger.debug("record_media_outcome failed", exc_info=True)

                    threading.Thread(target=_record, name="jarvis-media-record", daemon=True).start()
            except MediaJobCancelled as exc:
                result = {"ok": False, "message": str(exc) or "Cancelled by user"}
            except Exception as exc:
                logger.exception("Media job %s failed", job_id)
                result = {"ok": False, "message": str(exc)}
            with _lock:
                job = _jobs.get(job_id)
                if job:
                    job["done"] = True
                    job["pct"] = 100
                    job["result"] = result
                    if not result.get("ok"):
                        job["error"] = result.get("message") or "Failed"
                        job["message"] = job["error"]
                        low = job["message"].lower()
                        if "timed out" in low:
                            _stats["timed_out"] += 1
                        elif "cancel" in low:
                            _stats["cancelled"] += 1
                        else:
                            _stats["failed"] += 1
                    else:
                        job["message"] = "Complete"
                        job["error"] = ""
                        _stats["completed"] += 1
                        _notify_busy_done(job.get("label") or kind, result)
                    _log_job_event(
                        "media_job_done",
                        job_id,
                        kind,
                        ok=bool(result.get("ok")),
                        detail=job.get("message") or "",
                    )
                    try:
                        from jarvis.events import emit_job_done

                        emit_job_done(
                            queue="media",
                            job_id=job_id,
                            result=result,
                            label=job.get("label") or kind,
                        )
                    except Exception:
                        pass
            _persist_state()
            _purge_old_jobs()
        finally:
            _set_active_job(None)
            if hasattr(_tls, "deadline"):
                del _tls.deadline
            with _lock:
                _active_id = None
                _active_label = ""
            _queue.task_done()


def _notify_busy_start(label: str, kind: str) -> None:
    from jarvis.branding import assistant_name

    name = assistant_name()
    hint = eta_hint(kind)
    body = f"{label} started."
    if hint:
        body += f" {hint.capitalize()}."
    body += f" {name} stays responsive — other chat still works."
    try:
        from jarvis.notify_util import notify_jarvis

        notify_jarvis(f"{name} busy", body)
    except Exception:
        pass


def _notify_busy_done(label: str, result: dict) -> None:
    from jarvis.branding import assistant_name

    msg = result.get("message") or "Done"
    short = msg.split("\n")[0][:120]
    try:
        from jarvis.notify_util import notify_jarvis

        notify_jarvis(f"{assistant_name()} ready", f"{label} finished — {short}")
    except Exception:
        pass


def submit(action: str, label: str, fn: Callable[[], dict]) -> str:
    from jarvis.modules.workflow_orchestration_adapter import workflow_enqueue

    return workflow_enqueue("media", action, _submit_impl, action, label, fn)


def _submit_impl(action: str, label: str, fn: Callable[[], dict]) -> str:
    """Enqueue work; returns job id."""
    _ensure_worker()
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "kind": action,
            "label": label or ACTION_LABELS.get(action, action),
            "pct": 0,
            "message": "Queued…",
            "done": False,
            "cancelled": False,
            "error": "",
            "result": None,
            "started": time.time(),
        }
        _history.append(job_id)
    assert _queue is not None
    _queue.put((job_id, fn))
    _persist_state()
    return job_id


def submit_assistant_action(assistant, action: str, params: dict, message: str) -> str:
    from jarvis.handlers.media import MediaHandler

    handler = MediaHandler(assistant)
    runners = {
        "generate_image": lambda: handler.generate_image(params, message),
        "generate_video": lambda: handler.generate_video(params, message),
        "generate_meme": lambda: handler.generate_meme(params, message),
        "upscale_image": lambda: handler.upscale_image(params, message),
        "inpaint_image": lambda: handler.inpaint_image(params, message),
        "edit_image": lambda: handler.edit_image(params, message),
    }
    fn = runners.get(action)
    if not fn:
        raise ValueError(f"Unknown media action: {action}")
    label = ACTION_LABELS.get(action, action)
    return submit(action, label, fn)


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def cancel_job(job_id: str) -> bool:
    from jarvis.modules.workflow_orchestration_adapter import workflow_cancel

    return workflow_cancel("media", job_id, _cancel_job_impl, job_id)


def _cancel_job_impl(job_id: str) -> bool:
    active = False
    with _lock:
        job = _jobs.get(job_id)
        if not job or job.get("done"):
            return False
        job["cancelled"] = True
        job["message"] = "Cancelling…"
        active = job_id == _active_id
    if active:
        try:
            from jarvis.comfyui import interrupt_running

            interrupt_running()
        except Exception:
            pass
    return True


def is_busy() -> bool:
    with _lock:
        return _active_id is not None or (_queue is not None and not _queue.empty())


def has_active_work_persisted(max_age_sec: float = 900.0) -> bool:
    """True if state file shows a recent incomplete media job (survives server restart)."""
    if not _state_file.is_file():
        return False
    try:
        data = json.loads(_state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    now = time.time()
    for item in data.get("jobs", []):
        if item.get("done"):
            continue
        started = float(item.get("started") or 0)
        if started and (now - started) > max_age_sec:
            continue
        return True
    return False


def has_active_work() -> bool:
    """True if any media job is queued or running (including just-submitted)."""
    if has_active_work_persisted():
        return True
    with _lock:
        if _active_id is not None:
            return True
        if _queue is not None and not _queue.empty():
            return True
        return any(not j.get("done") for j in _jobs.values())


def busy_state() -> dict:
    with _lock:
        pending = _queue.qsize() if _queue else 0
        return {
            "busy": _active_id is not None,
            "pending": pending,
            "label": _active_label,
            "job_id": _active_id,
            "queue_depth": pending + (1 if _active_id else 0),
        }


def list_recent(limit: int = 10) -> list[dict]:
    with _lock:
        ids = list(_history)[-limit:]
        return [dict(_jobs[i]) for i in reversed(ids) if i in _jobs]
