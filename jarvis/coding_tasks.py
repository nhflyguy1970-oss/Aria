"""Persistent long-running coding tasks with checkpoints and pause/resume."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

TASKS_FILE = DATA_DIR / "coding_tasks.json"


@dataclass
class TaskStep:
    step: int
    action: str
    detail: str
    ok: bool = True
    ts: float = field(default_factory=time.time)


@dataclass
class CodingTask:
    id: str
    title: str
    status: str  # running | paused | done | failed
    steps: list[TaskStep] = field(default_factory=list)
    checkpoint: dict[str, Any] = field(default_factory=dict)
    proposal_id: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    path: str = ""
    mode: str = "agent"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["steps"] = [asdict(s) for s in self.steps]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CodingTask:
        steps = [TaskStep(**s) for s in data.get("steps", [])]
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            status=data.get("status", "running"),
            steps=steps,
            checkpoint=data.get("checkpoint", {}),
            proposal_id=data.get("proposal_id", ""),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            path=data.get("path", ""),
            mode=data.get("mode", "agent"),
        )


class TaskManager:
    def __init__(self, path: Path | None = None):
        self.path = path or TASKS_FILE
        self._tasks: dict[str, CodingTask] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for item in data.get("tasks", []):
                t = CodingTask.from_dict(item)
                self._tasks[t.id] = t
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tasks": [t.to_dict() for t in self._tasks.values()]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def create(self, title: str, *, path: str = "", mode: str = "agent") -> CodingTask:
        tid = str(uuid.uuid4())[:8]
        task = CodingTask(id=tid, title=title[:200], status="running", path=path, mode=mode)
        self._tasks[tid] = task
        self._save()
        return task

    def get(self, task_id: str) -> CodingTask | None:
        return self._tasks.get(task_id)

    def active(self) -> CodingTask | None:
        for t in sorted(self._tasks.values(), key=lambda x: x.updated_at, reverse=True):
            if t.status in ("running", "paused"):
                return t
        return None

    def list_tasks(self, limit: int = 20) -> list[CodingTask]:
        return sorted(self._tasks.values(), key=lambda x: x.updated_at, reverse=True)[:limit]

    def add_step(self, task_id: str, action: str, detail: str, *, ok: bool = True) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.steps.append(TaskStep(len(task.steps) + 1, action, detail, ok))
        task.updated_at = time.time()
        self._save()

    def checkpoint(self, task_id: str, data: dict[str, Any]) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.checkpoint.update(data)
        task.updated_at = time.time()
        self._save()

    def save_state(
        self,
        task_id: str,
        *,
        task_text: str = "",
        path: str = "",
        mode: str = "",
        last_errors: str = "",
        files: list[str] | None = None,
        proposal_id: str = "",
    ) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        if task_text:
            task.checkpoint["task"] = task_text
        if path:
            task.checkpoint["path"] = path
            task.path = path
        if mode:
            task.checkpoint["mode"] = mode
            task.mode = mode
        if last_errors:
            task.checkpoint["last_errors"] = last_errors
        if files is not None:
            task.checkpoint["files"] = files
        if proposal_id:
            task.checkpoint["proposal_id"] = proposal_id
            task.proposal_id = proposal_id
        task.updated_at = time.time()
        self._save()

    def set_proposal(self, task_id: str, proposal_id: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.proposal_id = proposal_id
        task.updated_at = time.time()
        self._save()

    def pause(self, task_id: str) -> CodingTask | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "paused"
        task.updated_at = time.time()
        self._save()
        return task

    def resume(self, task_id: str) -> CodingTask | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "running"
        task.updated_at = time.time()
        self._save()
        return task

    def complete(self, task_id: str, *, ok: bool = True) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "done" if ok else "failed"
        task.updated_at = time.time()
        self._save()
