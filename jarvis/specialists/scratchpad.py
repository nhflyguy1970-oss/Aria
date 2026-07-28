"""Durable scratchpad for Specialist Team runs."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

SCRATCH_DIR = DATA_DIR / "specialists" / "scratchpads"
_lock = threading.Lock()


class SharedScratchpad:
    def __init__(self, goal: str, run_id: str = "") -> None:
        self.goal = goal
        self.run_id = run_id
        self.notes: list[dict[str, Any]] = []
        self.artifacts: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.reasoning: list[dict[str, Any]] = []
        self.created_at = time.time()
        self.updated_at = self.created_at

    def add_note(self, agent: str, text: str) -> None:
        self.notes.append({"agent": agent, "text": str(text)[:4000], "ts": time.time()})
        self.updated_at = time.time()

    def add_artifact(self, agent: str, data: dict[str, Any], *, kind: str = "output") -> None:
        self.artifacts.append({"agent": agent, "kind": kind, "data": data, "ts": time.time()})
        self.updated_at = time.time()

    def add_failure(self, agent: str, error: str, *, recovered: bool = False) -> None:
        self.failures.append(
            {"agent": agent, "error": str(error)[:800], "recovered": recovered, "ts": time.time()}
        )
        self.updated_at = time.time()

    def add_reasoning(self, agent: str, text: str) -> None:
        self.reasoning.append({"agent": agent, "text": str(text)[:2000], "ts": time.time()})
        self.updated_at = time.time()

    def snapshot(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "run_id": self.run_id,
            "notes": list(self.notes),
            "artifacts": list(self.artifacts),
            "failures": list(self.failures),
            "reasoning": list(self.reasoning),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def persist(self) -> Path | None:
        if not self.run_id:
            return None
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        path = SCRATCH_DIR / f"{self.run_id}.json"
        with _lock:
            try:
                from jarvis.live_data_guard import assert_live_write_allowed

                assert_live_write_allowed(path)
            except Exception:
                pass
            path.write_text(json.dumps(self.snapshot(), indent=2, default=str), encoding="utf-8")
        return path

    @classmethod
    def load(cls, run_id: str) -> "SharedScratchpad | None":
        path = SCRATCH_DIR / f"{run_id}.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        pad = cls(str(data.get("goal") or ""), run_id=run_id)
        pad.notes = list(data.get("notes") or [])
        pad.artifacts = list(data.get("artifacts") or [])
        pad.failures = list(data.get("failures") or [])
        pad.reasoning = list(data.get("reasoning") or [])
        pad.created_at = float(data.get("created_at") or time.time())
        pad.updated_at = float(data.get("updated_at") or pad.created_at)
        return pad
