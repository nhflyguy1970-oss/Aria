"""Build rich desktop startup notification for Jeff."""

from __future__ import annotations

import os
import subprocess
from typing import Any


def _ollama_model_count() -> int:
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=8)
        if proc.returncode != 0:
            return 0
        return max(0, len((proc.stdout or "").splitlines()) - 1)
    except Exception:
        return 0


def _gpu_line() -> str:
    try:
        from jarvis.workstation.hardware_report import collect_hardware

        hw = collect_hardware(benchmark=False)
        gpus = hw.get("gpus") or []
        if not gpus:
            return "GPU: CPU mode"
        names = [g.get("name", "GPU") for g in gpus[:2]]
        return "GPU: " + " · ".join(names)
    except Exception:
        return ""


def _action_items(report: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for gap in (report.get("gap_analysis") or {}).get("gaps") or []:
        if gap.get("human_required"):
            items.append(gap.get("fix") or gap.get("label", ""))
        elif gap.get("gain_daily", 0) >= 5:
            items.append(gap.get("label", ""))
    return items[:3]


def build_startup_notification(report: dict[str, Any] | None = None) -> str:
    from jarvis.morning_briefing import time_greeting
    from jarvis.workstation.acceptance import last_acceptance, run_acceptance

    data = report or last_acceptance()
    if not data.get("items"):
        data = run_acceptance(persist=False, live=False)

    greet = time_greeting()
    name = os.getenv("JARVIS_USER_NAME", "Jeff")
    scores = data.get("score") or {}
    daily = scores.get("daily_required", 0)
    integration = scores.get("integration", 0)
    models = _ollama_model_count()
    gpu = _gpu_line()

    lines = [f"{greet}, {name}."]
    if data.get("acceptance_passed"):
        lines.append("All required services healthy.")
    else:
        lines.append(f"Services: {daily:.0f}% daily · {integration:.0f}% integration.")

    if models:
        lines.append(f"Models available: {models}.")
    if gpu:
        lines.append(gpu)

    actions = _action_items(data)
    if actions:
        lines.append("Action: " + "; ".join(actions))
    elif data.get("acceptance_passed"):
        lines.append("Ready to work.")
    else:
        lines.append("Run AI Workstation Acceptance if anything looks off.")

    return "\n".join(lines)
