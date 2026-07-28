"""Budgets and approval gates for Specialist Team runs."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TeamBudget:
    max_specialists: int = 6
    max_steps: int = 12
    max_runtime_sec: float = 300.0
    max_model_cost_units: float = 10.0  # abstract units
    require_write_approval: bool = True
    require_confirm: bool = True
    allow_parallel_readers: bool = True
    allow_critic_loop: bool = False
    started_at: float = field(default_factory=time.time)
    cost_units: float = 0.0
    steps_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TeamBudget":
        data = data or {}
        return cls(
            max_specialists=int(data.get("max_specialists") or 6),
            max_steps=int(data.get("max_steps") or 12),
            max_runtime_sec=float(data.get("max_runtime_sec") or 300),
            max_model_cost_units=float(data.get("max_model_cost_units") or 10),
            require_write_approval=bool(data.get("require_write_approval", True)),
            require_confirm=bool(data.get("require_confirm", True)),
            allow_parallel_readers=bool(data.get("allow_parallel_readers", True)),
            allow_critic_loop=bool(data.get("allow_critic_loop", False)),
        )

    def check_start(self, team_size: int) -> dict[str, Any] | None:
        if team_size > self.max_specialists:
            return {
                "ok": False,
                "status": "failed",
                "error": f"Team size {team_size} exceeds max_specialists={self.max_specialists}",
            }
        return None

    def check_step(self) -> dict[str, Any] | None:
        if self.steps_used >= self.max_steps:
            return {"ok": False, "status": "failed", "error": "max_steps exceeded", "budget_exceeded": True}
        if (time.time() - self.started_at) > self.max_runtime_sec:
            return {"ok": False, "status": "timeout", "error": "max_runtime_sec exceeded", "timeout": True}
        if self.cost_units > self.max_model_cost_units:
            return {"ok": False, "status": "failed", "error": "max_model_cost_units exceeded", "budget_exceeded": True}
        return None

    def charge(self, units: float = 1.0) -> None:
        self.steps_used += 1
        self.cost_units += float(units)
