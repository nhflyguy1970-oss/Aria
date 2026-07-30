"""Performance budgets — warn only, never fail the request."""

from __future__ import annotations

import os
from typing import Any

# Default budgets (ms). Override with JARVIS_LATENCY_BUDGET_<NAME>_MS.
_DEFAULTS = {
    "routing": 20.0,
    "context": 50.0,
    "prompt_build": 20.0,
    "provider_queue": 250.0,
    "first_token": 2000.0,
    "completion": float(os.getenv("JARVIS_LATENCY_BUDGET_COMPLETION_MS", "30000") or 30000),
}


def budget_ms(name: str) -> float:
    env = os.getenv(f"JARVIS_LATENCY_BUDGET_{name.upper()}_MS", "").strip()
    if env:
        try:
            return float(env)
        except ValueError:
            pass
    return float(_DEFAULTS.get(name, 0))


def evaluate_budgets(trace) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    stages = {s.name: s.elapsed_ms for s in getattr(trace, "stages", []) if s.elapsed_ms is not None}

    def _warn(budget_name: str, actual: float | None, subsystem: str) -> None:
        if actual is None:
            return
        limit = budget_ms(budget_name)
        if limit <= 0 or actual <= limit:
            return
        warnings.append(
            {
                "budget": budget_name,
                "limit_ms": limit,
                "actual_ms": round(float(actual), 2),
                "subsystem": subsystem,
                "severity": "warn",
                "message": f"{subsystem} took {actual:.0f}ms (budget {limit:.0f}ms)",
            }
        )

    _warn("routing", stages.get("routing"), "routing")
    # Context: sum of context-related stages or explicit context_assembly
    ctx = stages.get("context_assembly")
    if ctx is None:
        ctx = sum(v for k, v in stages.items() if k.startswith("context.") or k in ("memory", "planning", "knowledge", "project_extras"))
        ctx = ctx or None
    _warn("context", ctx, "context")
    _warn("prompt_build", stages.get("prompt_build"), "prompt_build")
    _warn("provider_queue", stages.get("provider_queue") or (trace.provider or {}).get("queue_ms"), "provider_queue")
    _warn("first_token", (trace.stream or {}).get("first_token_ms"), "provider")
    _warn("completion", trace.elapsed_ms(), "request")
    return warnings
