"""Provider Health engine — aggregated status / diagnostics."""

from __future__ import annotations

from typing import Any

from jarvis.provider_health.history import load_history
from jarvis.provider_health.prefs import load_preferences
from jarvis.provider_health.probe import list_models, list_providers, ping_provider, resource_snapshot
from jarvis.provider_health.terminology import BOUNDARIES, HEALTH_STATES, MENTAL_MODEL, TERMINOLOGY
from jarvis.provider_health.watchdog import active_requests, stats as watchdog_stats


def health_score(ping: dict[str, Any], wd: dict[str, Any]) -> int:
    score = 100
    if not ping.get("alive"):
        return 15
    probe = ping.get("probe") or {}
    if probe.get("ok") is False:
        score -= 35
    timeouts = int(wd.get("timeouts") or 0)
    reqs = max(1, int(wd.get("requests") or 1))
    rate = timeouts / reqs
    if rate > 0.2:
        score -= 30
    elif rate > 0.05:
        score -= 15
    if int(wd.get("active") or 0) > 2:
        score -= 10
    return max(0, min(100, score))


def map_state(ping: dict[str, Any], active: list[dict[str, Any]]) -> str:
    if active:
        if any(a.get("state") == "generating" for a in active):
            return "generating"
        if any(a.get("state") == "recovering" for a in active):
            return "recovering"
        return "busy"
    state = ping.get("state") or "unknown"
    if state in HEALTH_STATES:
        return state
    if ping.get("alive"):
        return "healthy"
    if ping.get("alive") is False:
        return "disconnected"
    return "unknown"


def product_status() -> dict[str, Any]:
    ping = ping_provider("ollama", force_probe=False)
    wd = watchdog_stats()
    active = active_requests()
    state = map_state(ping, active)
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "state": state,
        "health_score": health_score(ping, wd),
        "provider": ping.get("provider") or "ollama",
        "alive": ping.get("alive"),
        "ping": ping,
        "watchdog": wd,
        "active": active,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "prefs": load_preferences(),
    }


def diagnostics() -> dict[str, Any]:
    ping = ping_provider("ollama", force_probe=True)
    models = list_models("ollama")
    resources = resource_snapshot()
    wd = watchdog_stats()
    active = active_requests()
    last = wd.get("last_completed") or {}
    return {
        "ok": True,
        "provider": ping.get("provider") or "ollama",
        "version": (list_providers()[0] if list_providers() else {}).get("version"),
        "endpoint": ping.get("host"),
        "connection": "up" if ping.get("alive") else "down",
        "state": map_state(ping, active),
        "health_score": health_score(ping, wd),
        "model": models.get("current"),
        "models": models.get("models") or [],
        "gpu": resources.get("gpu"),
        "cpu_percent": resources.get("cpu_percent"),
        "memory": resources.get("ram"),
        "vram": (resources.get("gpu") or {}).get("vram") if isinstance(resources.get("gpu"), dict) else None,
        "queue_length": len(active),
        "current_request": active[0] if active else None,
        "tokens_per_sec": last.get("tokens_per_sec"),
        "prompt_size": last.get("prompt_chars"),
        "last_token_at": last.get("last_token_at"),
        "last_successful_generation": wd.get("last_success_at"),
        "last_error": wd.get("last_error"),
        "recovery_attempts": wd.get("recoveries"),
        "recovery_success": wd.get("recovery_success"),
        "probe": ping.get("probe"),
        "recent_history": load_history(limit=20),
        "resources": resources,
    }


def stats_payload() -> dict[str, Any]:
    out = {"ok": True, **watchdog_stats(), "prefs": load_preferences()}
    # Historical latency trends (observability only — does not alter watchdog behavior).
    try:
        from jarvis.latency_observability.metrics import stats_payload as latency_stats

        out["latency_history"] = latency_stats(limit=200)
    except Exception:
        out["latency_history"] = None
    return out
