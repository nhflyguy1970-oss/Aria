"""Unified workstation startup — configure, bootstrap services, wait for health."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("jarvis.workstation.startup")

DEFAULT_WAIT_SECONDS = 120.0


def _autostart_ids() -> list[str]:
    raw = os.getenv("JARVIS_AUTOSTART_SERVICES", "").strip()
    if raw:
        return [part.strip() for part in raw.split(",") if part.strip()]
    return ["postgres", "redis", "open_webui", "litellm"]


def _wait_for_health(component_ids: list[str], timeout: float) -> dict[str, Any]:
    from jarvis.workstation.registry import component

    deadline = time.time() + timeout
    pending = set(component_ids)
    results: dict[str, Any] = {}
    while pending and time.time() < deadline:
        for cid in list(pending):
            comp = component(cid)
            if comp is None:
                pending.discard(cid)
                results[cid] = {"ok": False, "detail": "unknown component"}
                continue
            if comp.healthy():
                pending.discard(cid)
                results[cid] = {"ok": True, "detail": comp.status_detail()}
        if pending:
            time.sleep(2)
    for cid in pending:
        comp = component(cid)
        results[cid] = {
            "ok": False,
            "detail": comp.status_detail() if comp else "missing",
        }
    return results


def bootstrap_workstation(*, wait_timeout: float = DEFAULT_WAIT_SECONDS) -> dict[str, Any]:
    """Apply local config, start docker profiles and autostart services, wait for health."""
    from jarvis.workstation.lifecycle import up
    from jarvis.workstation.local_config import apply_local_defaults

    config_result = apply_local_defaults()
    profile_results: list[dict[str, Any]] = []
    for profile in os.getenv("JARVIS_DOCKER_PROFILES", "data,inference").split(","):
        profile = profile.strip()
        if not profile:
            continue
        payload = up(profile=profile)
        profile_results.append({"profile": profile, "ok": payload.get("ok", False)})

    up_result = up()
    autostart = _autostart_ids()
    wait_result = _wait_for_health(autostart, wait_timeout)
    healthy = sum(1 for item in wait_result.values() if item.get("ok"))
    return {
        "ok": up_result.get("ok", False) and healthy >= max(1, len(autostart) // 2),
        "config": config_result,
        "profiles": profile_results,
        "bootstrap": up_result,
        "autostart": autostart,
        "health": wait_result,
        "healthy_count": healthy,
        "autostart_count": len(autostart),
    }


def startup_greeting() -> str:
    """Plain-language summary for desktop notification after launch."""
    from jarvis.morning_briefing import time_greeting
    from jarvis.workstation.acceptance import last_acceptance

    greet = time_greeting()
    report = last_acceptance()
    if not report.get("items"):
        return f"{greet}, Jeff. Starting AI Workstation…"

    scores = report.get("score") or {}
    daily = scores.get("daily_required", 0)
    summary = report.get("summary") or {}
    ready = summary.get("ready", 0)
    total = summary.get("total", 0)
    if report.get("acceptance_passed"):
        return f"{greet}, Jeff. All required services healthy ({daily:.0f}%). Ready to work."
    needs = summary.get("needs_configuration", 0)
    return (
        f"{greet}, Jeff. {ready}/{total} components ready ({daily:.0f}% daily). "
        f"{needs} need attention — open Acceptance for details."
    )
