"""Aria Core — Runtime (delegates to jarvis.runtime_client)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("runtime")


def RuntimeClient(*args: Any, **kwargs: Any) -> Any:
    from jarvis.runtime_client import RuntimeClient as _RuntimeClient

    return _RuntimeClient(*args, **kwargs)


def execution_mode() -> str:
    try:
        from jarvis.runtime_introspection import execution_mode as _mode

        return str(_mode())
    except Exception:
        return "unknown"


def mission_control_reachable(*, timeout: float = 1.0) -> bool:
    try:
        return bool(RuntimeClient().is_mission_control_reachable(timeout=timeout))
    except Exception:
        return False
