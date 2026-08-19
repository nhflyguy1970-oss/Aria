"""Autonomy levels and safe mode.

This is not a permission system. Every authority question — may this agent run
this action, may this skill reach that provider, may this model be used — is
still answered by the system that owns it. What lives here is the orthogonal
question of how much ARIA may do *without being asked again*, and a switch to
stop autonomous execution without losing any stored state.

Because it only ever narrows what the existing systems already allow, a wrapper
here cannot become a way around them.
"""

from __future__ import annotations

import os
from typing import Any

# Autonomy levels, least to most independent.
DIRECT = "direct"  # the user drives; ARIA answers
ASSISTED = "assisted"  # ARIA may use skills and tools for this request
BOUNDED = "bounded"  # ARIA may run a bounded workflow to completion
CONTINUOUS = "continuous"  # ARIA may keep working across restarts
LEVELS = (DIRECT, ASSISTED, BOUNDED, CONTINUOUS)
_ORDER = {level: index for index, level in enumerate(LEVELS)}

DEFAULT_LEVEL = BOUNDED

# What each level may reach for. Deliberately additive and small.
_CAPABILITIES = {
    DIRECT: {"answer"},
    ASSISTED: {"answer", "skill", "agent", "tool", "model"},
    BOUNDED: {
        "answer",
        "skill",
        "agent",
        "tool",
        "model",
        "workflow",
        "mission",
        "research",
        "browser",
        "coding",
    },
    CONTINUOUS: {
        "answer",
        "skill",
        "agent",
        "tool",
        "model",
        "workflow",
        "mission",
        "research",
        "browser",
        "coding",
        "scheduled",
    },
}

# Per-level ceilings, applied on top of each subsystem's own bounds. These can
# only tighten what a workflow already limits.
_BOUNDS = {
    DIRECT: {"max_steps": 1, "max_runtime_s": 120, "max_child_agents": 1},
    ASSISTED: {"max_steps": 6, "max_runtime_s": 600, "max_child_agents": 2},
    BOUNDED: {"max_steps": 25, "max_runtime_s": 1800, "max_child_agents": 4},
    CONTINUOUS: {"max_steps": 40, "max_runtime_s": 3600, "max_child_agents": 8},
}

AUTONOMY_ENV = "JARVIS_AUTONOMY"
SAFE_MODE_ENV = "JARVIS_SAFE_MODE"
WORKER_ENV = "JARVIS_MISSION_WORKER"


class PolicyError(ValueError):
    pass


def normalise(level: str) -> str:
    name = (level or "").strip().lower()
    if not name:
        return DEFAULT_LEVEL
    if name not in LEVELS:
        raise PolicyError(f"Unknown autonomy level {level!r}; allowed: {', '.join(LEVELS)}")
    return name


def configured_level() -> str:
    """The deployment's autonomy level. Safe mode overrides it entirely."""
    if safe_mode():
        return DIRECT
    try:
        return normalise(os.getenv(AUTONOMY_ENV, "") or DEFAULT_LEVEL)
    except PolicyError:
        return DEFAULT_LEVEL


def safe_mode() -> bool:
    """Autonomy off. State stays durable and inspectable; nothing new starts."""
    return (os.getenv(SAFE_MODE_ENV, "0") or "0").strip().lower() in ("1", "true", "yes", "on")


def worker_enabled() -> bool:
    return (os.getenv(WORKER_ENV, "0") or "0").strip() == "1"


def effective_level(requested: str = "") -> str:
    """The lower of what was asked for and what the deployment allows."""
    ceiling = configured_level()
    asked = normalise(requested) if requested else ceiling
    return asked if _ORDER[asked] <= _ORDER[ceiling] else ceiling


def permits(capability: str, level: str = "") -> bool:
    return capability in _CAPABILITIES[effective_level(level)]


def bounds_for(level: str = "") -> dict[str, int]:
    return dict(_BOUNDS[effective_level(level)])


def apply_bounds(limits: dict[str, Any] | None, level: str = "") -> dict[str, Any]:
    """Tighten a workflow's limits to the autonomy level. Never loosens them."""
    merged = dict(limits or {})
    for name, ceiling in bounds_for(level).items():
        asked = merged.get(name)
        merged[name] = ceiling if asked is None else min(int(asked), ceiling)
    return merged


def check(capability: str, *, level: str = "", detail: str = "") -> None:
    """Raise if the environment's autonomy level does not extend this far."""
    if safe_mode() and capability != "answer":
        raise PolicyError(
            f"safe mode is on: {capability} is not started. Existing state is unchanged "
            "and remains inspectable; clear JARVIS_SAFE_MODE to resume."
        )
    if not permits(capability, level):
        raise PolicyError(
            f"autonomy level {effective_level(level)} does not permit {capability}"
            + (f" ({detail})" if detail else "")
        )


def snapshot() -> dict[str, Any]:
    """What the environment is currently allowed to do, and why."""
    level = configured_level()
    return {
        "autonomy": level,
        "requested_autonomy": (os.getenv(AUTONOMY_ENV, "") or DEFAULT_LEVEL).strip().lower(),
        "safe_mode": safe_mode(),
        "worker_enabled": worker_enabled(),
        "capabilities": sorted(_CAPABILITIES[level]),
        "bounds": bounds_for(level),
        "levels": list(LEVELS),
        "notes": (
            "safe mode forces direct autonomy; queued work stays durable and nothing new starts"
            if safe_mode()
            else "autonomy narrows what runs unattended; each subsystem still enforces its own"
            " permissions"
        ),
    }
