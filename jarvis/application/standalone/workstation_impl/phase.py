"""Workstation lifecycle phase — avoids misleading acceptance during startup."""

from __future__ import annotations

import json
import time
from enum import StrEnum
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_PHASE_FILE = PROJECT_ROOT / "data" / "automation" / "workstation_phase.json"

_TRANSITIONAL = frozenset(
    {
        "STARTING",
        "INITIALIZING",
        "RECOVERING",
        "STOPPING",
    }
)


class WorkstationPhase(StrEnum):
    STARTING = "STARTING"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RECOVERING = "RECOVERING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


def _default() -> dict[str, Any]:
    return {"phase": WorkstationPhase.STOPPED.value, "detail": "", "since": 0.0}


def _load() -> dict[str, Any]:
    if not _PHASE_FILE.is_file():
        return _default()
    try:
        data = json.loads(_PHASE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_default(), **data}
    except (json.JSONDecodeError, OSError):
        pass
    return _default()


def _save(data: dict[str, Any]) -> None:
    _PHASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PHASE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def current_phase() -> WorkstationPhase:
    raw = str(_load().get("phase") or WorkstationPhase.STOPPED.value)
    try:
        return WorkstationPhase(raw)
    except ValueError:
        return WorkstationPhase.STOPPED


def phase_snapshot() -> dict[str, Any]:
    return dict(_load())


def is_transitional() -> bool:
    return current_phase().value in _TRANSITIONAL


def set_phase(phase: WorkstationPhase | str, *, detail: str = "") -> dict[str, Any]:
    name = phase.value if isinstance(phase, WorkstationPhase) else str(phase)
    payload = {
        "phase": name,
        "detail": detail.strip(),
        "since": time.time(),
    }
    _save(payload)
    return payload


def mark_ready(*, detail: str = "") -> dict[str, Any]:
    return set_phase(WorkstationPhase.READY, detail=detail or "services healthy")


def mark_degraded(*, detail: str = "") -> dict[str, Any]:
    return set_phase(WorkstationPhase.DEGRADED, detail=detail or "issues detected")
