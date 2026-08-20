"""Persistent autonomous task engine — durable, resumable ARIA missions.

Public surface kept deliberately small: create, inspect, execute, pause/resume
and cancel. Storage lives under DATA_DIR like every other ARIA store, so it
follows the existing data-root and test-isolation conventions automatically.
"""

from jarvis.missions import worker
from jarvis.missions.engine import (
    ActionStepRunner,
    MissionCancelled,
    RetryableError,
    StepFailed,
    cancel,
    create_mission,
    pause,
    recover,
    resume,
    run,
    status,
)
from jarvis.missions.store import (
    CANCELLED,
    COMPLETED,
    FAILED,
    LIVE_STATES,
    PAUSED,
    PENDING,
    RUNNING,
    STATES,
    TERMINAL_STATES,
    MissionStateError,
    checkpoints,
    get,
    history,
    list_missions,
)

__all__ = [
    "ActionStepRunner",
    "worker",
    "CANCELLED",
    "COMPLETED",
    "FAILED",
    "LIVE_STATES",
    "MissionCancelled",
    "MissionStateError",
    "PAUSED",
    "PENDING",
    "RUNNING",
    "STATES",
    "TERMINAL_STATES",
    "RetryableError",
    "StepFailed",
    "cancel",
    "checkpoints",
    "create_mission",
    "get",
    "history",
    "list_missions",
    "pause",
    "recover",
    "resume",
    "run",
    "status",
]
