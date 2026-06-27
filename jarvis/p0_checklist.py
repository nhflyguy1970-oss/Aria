"""First-flight checklist for P0/P1 smoke tests."""

from __future__ import annotations

import time
from typing import Any


def run_checklist(*, assistant, full: bool = False) -> dict[str, Any]:
    """Run first-flight checks. Set full=True for deeper smoke tests."""
    started = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "", ms: int | None = None) -> None:
        row: dict[str, Any] = {"name": name, "ok": bool(ok), "detail": detail}
        if ms is not None:
            row["ms"] = ms
        checks.append(row)

    add("assistant", assistant is not None, "JarvisAssistant loaded")
    try:
        from jarvis.planner_store import planner_snapshot

        snap = planner_snapshot()
        add("planner", bool(snap.get("enabled", True)), f"{len(snap.get('tasks') or [])} tasks")
    except Exception as exc:
        add("planner", False, str(exc))
    try:
        from jarvis.system_monitor import collect_stats

        stats = collect_stats()
        add("monitor", "cpu_percent" in stats, f"CPU {stats.get('cpu_percent', '?')}%")
    except Exception as exc:
        add("monitor", False, str(exc))
    if full:
        try:
            from jarvis.voice_smoke import run_voice_smoke

            t0 = time.time()
            voice = run_voice_smoke(assistant=assistant)
            add("voice smoke", bool(voice.get("ok")), voice.get("message", ""), ms=int((time.time() - t0) * 1000))
        except Exception as exc:
            add("voice smoke", False, str(exc))
    passed = sum(1 for c in checks if c["ok"])
    return {
        "ok": passed == len(checks),
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "full": bool(full),
        "elapsed_ms": int((time.time() - started) * 1000),
    }
