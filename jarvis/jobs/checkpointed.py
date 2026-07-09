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
    job = CheckpointedJob(id=uuid.uuid4().hex[:12], kind="agent_chain", goal=goal, status="running")
    job.checkpoint = {"roles": roles or [], "step": 0}
    save_job(job)

    def _run() -> None:
        try:
            from jarvis.agents.coordinator import run_agent_chain

            result = run_agent_chain(assistant, goal, roles=roles, stop_on_error=False)
            job.status = "completed" if result.get("ok") else "failed"
            job.progress = 1.0
            job.message = result.get("summary") or "done"
            job.result = result
            job.checkpoint["step"] = len(result.get("steps") or [])
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
    """Resume jobs that were running when Aria last stopped."""
    resumed: list[str] = []
    for job in list_jobs(status="running"):
        if job.id in _threads:
            continue

        def _run(existing: CheckpointedJob = job) -> None:
            try:
                from jarvis.agents.coordinator import run_agent_chain

                roles = existing.checkpoint.get("roles")
                role_list = roles if isinstance(roles, list) else None
                result = run_agent_chain(
                    assistant,
                    existing.goal,
                    roles=role_list,
                    stop_on_error=False,
                )
                existing.status = "completed" if result.get("ok") else "failed"
                existing.progress = 1.0
                existing.message = result.get("summary") or "done"
                existing.result = result
                existing.checkpoint["step"] = len(result.get("steps") or [])
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
