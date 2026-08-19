"""Startup recovery, run before the environment accepts new autonomous work.

Each subsystem already knows how to find work its process abandoned. What was
missing was anyone calling them at startup: a restart left interrupted missions
and workflows sitting in a live state with nothing to pick them up, and new work
could start competing with them.

Recovery here only makes work *resumable*. It never re-executes a completed
step, and it never retries an operation whose outcome is unknown — an
interrupted step is handed back to its own subsystem, which decides.

Recovery is deliberately a *startup* operation. "Interrupted" is inferred from
a live state in a durable store, and that inference is only sound while nothing
is executing: at startup, anything still marked running belongs to a process
that is gone. Once the service is up, the same rows are healthy work in flight,
and resetting a running step to pending lets a second driver pick it up and run
it again — the side effect happens twice. So the on-demand entry point reports
by default and mutates only when a caller explicitly declares the owning
process dead.
"""

from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger("jarvis.integration.recovery")

# What this process made resumable when it booted. Kept so the environment can
# answer "what did the last restart pick up?" without re-running recovery.
_STARTUP_OUTCOME: dict[str, Any] | None = None

REFUSAL = (
    "Recovery is a startup operation. While the service is running, work in a "
    "live state belongs to this process; resetting it would let a second driver "
    "execute the same step again. Pass force=true only when the process that "
    "owned this work is known to be dead."
)


def _collect(label: str, loader) -> tuple[list[str], str]:
    try:
        return list(loader() or []), ""
    except Exception as exc:  # noqa: BLE001 - one subsystem must not block the rest
        log.warning("recovery: %s failed", label, exc_info=True)
        return [], f"{type(exc).__name__}: {exc}"


# Report-only probes. These read the same rows the mutating recovery would act
# on, so a dry run tells the truth about what applying would touch.
def _pending_missions() -> list[str]:
    from jarvis.missions import store

    return [m["id"] for m in store.interrupted_missions()]


def _pending_workflows() -> list[str]:
    from jarvis.autonomous_workflows import store

    return list(store.interrupted())


def _pending_coding() -> list[str]:
    from jarvis.dev_agent import store

    return [t["id"] for t in store.interrupted_tasks()]


def _missions() -> list[str]:
    from jarvis import missions

    return missions.recover()


def _workflows() -> list[str]:
    from jarvis import autonomous_workflows as wf

    return wf.recover()


def _coding() -> list[str]:
    from jarvis import dev_agent

    return dev_agent.recover()


def _subsystems() -> tuple[tuple[str, Any, Any], ...]:
    """Resolved per call, so a subsystem can be substituted or fail in isolation.

    Missions first: a workflow's durability rests on its mission, so the mission
    must be resumable before the workflow is looked at.
    """
    return (
        ("missions", _missions, _pending_missions),
        ("workflows", _workflows, _pending_workflows),
        ("coding_tasks", _coding, _pending_coding),
    )


def recover_all(*, apply: bool = True) -> dict[str, Any]:
    """Ask every durable subsystem to make its interrupted work resumable.

    With ``apply=False`` nothing is written: the same rows are reported, so a
    caller can see what recovery would touch before it touches it.
    """
    started = time.time()
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for label, mutate, probe in _subsystems():
        recovered, error = _collect(label, mutate if apply else probe)
        results[label] = recovered
        if error:
            errors[label] = error

    total = sum(len(v) for v in results.values())
    if total and apply:
        log.info("environment recovery: %s item(s) made resumable", total)
    return {
        "ok": not errors,
        "applied": apply,
        "recovered": results,
        "total": total,
        "errors": errors,
        "duration_ms": round((time.time() - started) * 1000, 2),
    }


def pending_recovery() -> dict[str, Any]:
    """What recovery would touch right now, without touching it."""
    return recover_all(apply=False)


def recover_on_startup() -> dict[str, Any]:
    """Called from the service lifespan, before the worker takes new work.

    Safe mode still recovers: knowing what was interrupted is inspection, not
    execution, and losing that knowledge would be the more dangerous default.
    """
    global _STARTUP_OUTCOME
    from jarvis.integration import policy

    outcome = recover_all(apply=True)
    outcome["safe_mode"] = policy.safe_mode()
    outcome["autonomy"] = policy.configured_level()
    outcome["at"] = time.time()
    if outcome["total"] and policy.safe_mode():
        outcome["note"] = "recovered work is resumable but will not start while safe mode is on"
    _STARTUP_OUTCOME = outcome
    return outcome


def last_startup_recovery() -> dict[str, Any] | None:
    """What this process recovered at boot, or None if it has not booted here."""
    return _STARTUP_OUTCOME


def recover_on_demand(*, apply: bool = False, force: bool = False) -> dict[str, Any]:
    """The operator-facing entry point: reports by default, mutates on demand.

    Applying is refused unless `force`, because after startup a live state means
    "executing", not "abandoned" — see the module docstring.
    """
    outcome = recover_all(apply=False)
    outcome["startup"] = _STARTUP_OUTCOME
    if not apply:
        return outcome
    if not force:
        outcome["refused"] = REFUSAL
        return outcome

    applied = recover_all(apply=True)
    applied["forced"] = True
    applied["startup"] = _STARTUP_OUTCOME
    return applied
