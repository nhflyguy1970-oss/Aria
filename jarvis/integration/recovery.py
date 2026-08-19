"""Startup recovery, run before the environment accepts new autonomous work.

Each subsystem already knows how to find work its process abandoned. What was
missing was anyone calling them at startup: a restart left interrupted missions
and workflows sitting in a live state with nothing to pick them up, and new work
could start competing with them.

Recovery here only makes work *resumable*. It never re-executes a completed
step, and it never retries an operation whose outcome is unknown — an
interrupted step is handed back to its own subsystem, which decides.
"""

from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger("jarvis.integration.recovery")


def _recover(label: str, loader) -> tuple[list[str], str]:
    try:
        return list(loader() or []), ""
    except Exception as exc:  # noqa: BLE001 - one subsystem must not block the rest
        log.warning("recovery: %s failed", label, exc_info=True)
        return [], f"{type(exc).__name__}: {exc}"


def recover_all() -> dict[str, Any]:
    """Ask every durable subsystem to make its interrupted work resumable."""
    started = time.time()
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    # Missions first: a workflow's durability rests on its mission, so the
    # mission must be resumable before the workflow is looked at.
    for label, loader in (
        ("missions", _missions),
        ("workflows", _workflows),
        ("coding_tasks", _coding),
    ):
        recovered, error = _recover(label, loader)
        results[label] = recovered
        if error:
            errors[label] = error

    total = sum(len(v) for v in results.values())
    if total:
        log.info("environment recovery: %s item(s) made resumable", total)
    return {
        "ok": not errors,
        "recovered": results,
        "total": total,
        "errors": errors,
        "duration_ms": round((time.time() - started) * 1000, 2),
    }


def _missions() -> list[str]:
    from jarvis import missions

    return missions.recover()


def _workflows() -> list[str]:
    from jarvis import autonomous_workflows as wf

    return wf.recover()


def _coding() -> list[str]:
    from jarvis import dev_agent

    return dev_agent.recover()


def recover_on_startup() -> dict[str, Any]:
    """Called from the service lifespan, before the worker takes new work.

    Safe mode still recovers: knowing what was interrupted is inspection, not
    execution, and losing that knowledge would be the more dangerous default.
    """
    from jarvis.integration import policy

    outcome = recover_all()
    outcome["safe_mode"] = policy.safe_mode()
    outcome["autonomy"] = policy.configured_level()
    if outcome["total"] and policy.safe_mode():
        outcome["note"] = "recovered work is resumable but will not start while safe mode is on"
    return outcome
