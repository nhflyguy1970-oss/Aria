"""Safe automatic recovery pipeline for provider failures."""

from __future__ import annotations

import time
from typing import Any

from jarvis.provider_health.classify import classify_failure, operator_copy
from jarvis.provider_health.history import append_event
from jarvis.provider_health.prefs import load_preferences
from jarvis.provider_health.probe import list_models, ping_provider
from jarvis.provider_health.watchdog import note_recovery


def recover(
    *,
    code: str = "",
    message: str = "",
    provider: str = "ollama",
    model: str = "",
    got_progress: bool = False,
    auto: bool = True,
) -> dict[str, Any]:
    """
    Run safe recovery steps:
    ping → retry-ready → reconnect/ensure → optional restart → classify.
    Does not invent a second inference path — returns guidance + steps taken.
    """
    prefs = load_preferences()
    attempts = max(1, int(prefs.get("recovery_attempts") or 3))
    delay_ms = int(prefs.get("retry_delay_ms") or 1200)
    steps: list[dict[str, Any]] = []

    ping = ping_provider(provider, force_probe=True)
    steps.append({"id": "ping", "ok": bool(ping.get("alive")), "detail": ping.get("detail") or ping.get("state")})

    classified = classify_failure(
        code=code,
        message=message,
        provider_alive=ping.get("alive"),
        got_progress=got_progress,
        probe=ping.get("probe") if isinstance(ping.get("probe"), dict) else None,
    )

    # Step: reconnect / ensure provider
    if not ping.get("alive") and auto and prefs.get("auto_restart", True):
        recon = _reconnect(provider)
        steps.append({"id": "reconnect", **recon})
        time.sleep(delay_ms / 1000.0)
        ping = ping_provider(provider, force_probe=True)
        steps.append({"id": "ping_after_reconnect", "ok": bool(ping.get("alive")), "detail": ping.get("state")})
        classified = classify_failure(
            code=code,
            message=message,
            provider_alive=ping.get("alive"),
            got_progress=got_progress,
            probe=ping.get("probe") if isinstance(ping.get("probe"), dict) else None,
        )

    # Step: restart when alive but wedged / stalled
    restarted = False
    if (
        auto
        and prefs.get("auto_restart", True)
        and ping.get("alive")
        and classified.get("class") in ("stream_stalled", "first_token_timeout", "provider_overloaded")
    ):
        # Prefer soft reconnect first; hard restart only if probe failed
        probe = ping.get("probe") or {}
        if probe.get("ok") is False or classified.get("class") == "stream_stalled":
            rst = restart_provider(provider)
            steps.append({"id": "restart_provider", **rst})
            restarted = bool(rst.get("ok"))
            time.sleep(delay_ms / 1000.0)
            ping = ping_provider(provider, force_probe=True)
            steps.append({"id": "ping_after_restart", "ok": bool(ping.get("alive")), "detail": ping.get("state")})

    # Retry stream is a client action — mark readiness
    can_retry = bool(ping.get("alive"))
    steps.append({"id": "retry_stream", "ok": can_retry, "detail": "Client should retry the same prompt" if can_retry else "Provider still down"})

    model_offer = []
    if not can_retry or classified.get("class") in ("oom", "context_too_large", "model_crashed", "stream_stalled"):
        models = list_models(provider)
        current = models.get("current") or model
        for m in models.get("models") or []:
            if m != current:
                model_offer.append(m)
            if len(model_offer) >= 5:
                break

    success = can_retry and (restarted or any(s.get("id") == "reconnect" and s.get("ok") for s in steps) or ping.get("alive"))
    # Success means recovery made provider usable for retry — not that generation finished
    usable = bool(ping.get("alive"))
    note_recovery(success=usable)
    append_event(
        {
            "kind": "recovery",
            "code": code,
            "class": classified.get("class"),
            "provider": provider,
            "model": model or (ping.get("probe") or {}).get("model"),
            "steps": steps,
            "usable": usable,
            "auto": auto,
        }
    )

    try:
        from jarvis.provider_health.notify import notify_recovery

        notify_recovery(classified=classified, usable=usable, provider=provider, model=model)
    except Exception:
        pass

    return {
        "ok": True,
        "usable": usable,
        "auto_retry_recommended": usable and auto,
        "attempts_budget": attempts,
        "classified": classified,
        "operator_message": operator_copy(
            classified,
            provider=provider,
            model=model or str((ping.get("probe") or {}).get("model") or ""),
        ),
        "steps": steps,
        "ping": ping,
        "alternate_models": model_offer,
        "recommended_actions": classified.get("recommended_actions") or [],
    }


def _reconnect(provider: str) -> dict[str, Any]:
    provider = (provider or "ollama").lower()
    if provider in ("ollama", "local", ""):
        try:
            from jarvis.services import ensure_ollama

            ok = ensure_ollama(timeout=45)
            return {"ok": ok, "message": "Ollama ensure_ollama" + (" ok" if ok else " failed")}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
    return {"ok": False, "message": f"No reconnect adapter for {provider}"}


def restart_provider(provider: str = "ollama") -> dict[str, Any]:
    """Best-effort provider restart (safe local Ollama path)."""
    provider = (provider or "ollama").lower()
    append_event({"kind": "restart_attempt", "provider": provider})
    if provider not in ("ollama", "local", ""):
        return {"ok": False, "message": f"Restart not supported for {provider}"}
    try:
        # Soft path: ensure running; hard kill is left to Mission Control confirmed actions
        from jarvis.services import ensure_ollama

        ok = ensure_ollama(timeout=60)
        # Warm generate path
        ping = ping_provider("ollama", force_probe=True)
        append_event({"kind": "restart_result", "provider": "ollama", "ok": ok and bool(ping.get("alive"))})
        return {
            "ok": bool(ok and ping.get("alive")),
            "message": "Provider restarted / ensured" if ok else "Provider restart failed",
            "ping": ping,
        }
    except Exception as exc:
        append_event({"kind": "restart_result", "provider": "ollama", "ok": False, "error": str(exc)})
        return {"ok": False, "message": str(exc)}
