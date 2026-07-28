"""Checkpointed long-running jobs — survive restart, report progress."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.jobs.checkpointed")

JOBS_DIR = DATA_DIR / "jobs" / "checkpointed"
_lock = threading.Lock()
_threads: dict[str, threading.Thread] = {}


@dataclass
class CheckpointedJob:
    id: str
    kind: str
    goal: str
    status: str = "pending"
    progress: float = 0.0
    message: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def save_job(job: CheckpointedJob) -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    job.updated_at = time.time()
    _job_path(job.id).write_text(json.dumps(job.to_dict(), indent=2), encoding="utf-8")


def load_job(job_id: str) -> CheckpointedJob | None:
    path = _job_path(job_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CheckpointedJob(**data)
    except (json.JSONDecodeError, TypeError):
        return None


def list_jobs(*, status: str | None = None) -> list[CheckpointedJob]:
    if not JOBS_DIR.is_dir():
        return []
    jobs: list[CheckpointedJob] = []
    for path in JOBS_DIR.glob("*.json"):
        job = load_job(path.stem)
        if job and (status is None or job.status == status):
            jobs.append(job)
    jobs.sort(key=lambda j: j.updated_at, reverse=True)
    return jobs


def start_agent_job(
    assistant: Any, goal: str, *, roles: list[str] | None = None
) -> CheckpointedJob:
    job = CheckpointedJob(id=uuid.uuid4().hex[:12], kind="specialist_team", goal=goal, status="running")
    job.checkpoint = {"roles": roles or [], "step": 0, "resumable": False}
    save_job(job)

    def _run() -> None:
        try:
            from jarvis.specialists.composer import map_roles_to_specialists
            from jarvis.specialists.engine import run_team

            result = run_team(
                assistant,
                goal,
                roles=roles,
                specialists=map_roles_to_specialists(roles) if roles else None,
                confirm=True,
                stop_on_error=False,
                budget={"require_confirm": False},
                trigger="agent_job",
                emit_bridges=True,
                approve_writes=True,
            )
            st = result.get("status") or ("completed" if result.get("ok") else "failed")
            # Map to checkpoint statuses
            if st == "succeeded":
                job.status = "completed"
            elif st == "partial_success":
                job.status = "completed"
                job.message = "partial_success"
            else:
                job.status = "failed" if st != "cancelled" else "cancelled"
            job.progress = 1.0
            job.message = result.get("summary") or result.get("synthesis") or job.message or st
            job.result = result
            job.checkpoint["step"] = len(result.get("steps") or [])
            job.checkpoint["run_id"] = result.get("run_id")
            job.checkpoint["resumable"] = False  # honest: full re-run only
            save_job(job)
        except Exception as exc:
            job.status = "failed"
            job.message = str(exc)[:300]
            save_job(job)
        finally:
            _threads.pop(job.id, None)

    thread = threading.Thread(target=_run, daemon=True, name=f"job-{job.id}")
    _threads[job.id] = thread
    thread.start()
    return job


def resume_incomplete_jobs(assistant: Any) -> list[str]:
    """Re-run jobs left in running state. Honest: not mid-step resume — full re-execution."""
    resumed: list[str] = []
    for job in list_jobs(status="running"):
        if job.id in _threads:
            continue

        def _run(existing: CheckpointedJob = job) -> None:
            try:
                from jarvis.specialists.composer import map_roles_to_specialists
                from jarvis.specialists.engine import run_team

                roles = existing.checkpoint.get("roles")
                role_list = roles if isinstance(roles, list) else None
                result = run_team(
                    assistant,
                    existing.goal,
                    roles=role_list,
                    specialists=map_roles_to_specialists(role_list) if role_list else None,
                    confirm=True,
                    stop_on_error=False,
                    budget={"require_confirm": False},
                    trigger="agent_job_resume",
                    emit_bridges=True,
                    approve_writes=True,
                )
                existing.status = "completed" if result.get("ok") else "failed"
                existing.progress = 1.0
                existing.message = (
                    (result.get("summary") or result.get("synthesis") or "done")
                    + " (full re-run after restart — not mid-step checkpoint)"
                )
                existing.result = result
                existing.checkpoint["step"] = len(result.get("steps") or [])
                existing.checkpoint["resumable"] = False
                save_job(existing)
            except Exception as exc:
                existing.status = "failed"
                existing.message = str(exc)[:300]
                save_job(existing)
            finally:
                _threads.pop(existing.id, None)

        thread = threading.Thread(target=_run, daemon=True, name=f"job-{job.id}")
        _threads[job.id] = thread
        thread.start()
        resumed.append(job.id)
    return resumed


def job_status(job_id: str) -> dict[str, Any]:
    job = load_job(job_id)
    if not job:
        return {"ok": False, "error": "job not found"}
    return {"ok": True, "job": job.to_dict(), "active": job.id in _threads}
