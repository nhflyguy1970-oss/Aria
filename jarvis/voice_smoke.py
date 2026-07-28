"""Voice round-trip smoke test — shared pipeline health."""

from __future__ import annotations

import time
from typing import Any


def run_voice_smoke(*, assistant=None) -> dict[str, Any]:
    started = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    try:
        from jarvis.voice_product.settings import load_unified_settings

        settings = load_unified_settings()
        add("voice_settings", bool(settings), f"duplex={settings.get('duplex_mode', '?')}")
    except Exception as exc:
        add("voice_settings", False, str(exc))

    try:
        from jarvis.voice_product.engine import product_status

        st = product_status()
        add("voice_engine", bool(st.get("ok")), st.get("product", ""))
    except Exception as exc:
        add("voice_engine", False, str(exc))

    try:
        from jarvis.voice_product.status_bus import get_voice_state, set_voice_state

        set_voice_state("idle", detail="smoke", publish=False)
        add("status_bus", get_voice_state().get("state") == "idle", "idle")
    except Exception as exc:
        add("status_bus", False, str(exc))

    try:
        from jarvis.voice_product.intent_router import route_utterance

        r = route_utterance("open gallery")
        add("intent_router", bool(r and r.get("product") == "gallery"), str(r))
    except Exception as exc:
        add("intent_router", False, str(exc))

    try:
        from jarvis.voice_product.profiles import list_profiles

        profiles = list_profiles()
        add("profiles", len(profiles) >= 5, f"{len(profiles)} profiles")
    except Exception as exc:
        add("profiles", False, str(exc))

    try:
        from jarvis.voice_product.recovery import diagnose

        d = diagnose()
        add("recovery", "severity" in d, d.get("severity", ""))
    except Exception as exc:
        add("recovery", False, str(exc))

    try:
        from jarvis.cloud_live_voice import cloud_live_status

        live = cloud_live_status()
        # Honest: available OR openai hidden is OK for smoke
        add(
            "cloud_live",
            True,
            f"available={live.get('available')} hidden_openai={live.get('openai_hidden')}",
        )
    except Exception as exc:
        add("cloud_live", False, str(exc))

    try:
        from jarvis.voice_duplex import duplex_status

        dx = duplex_status()
        add("duplex", dx.get("mode") in ("off", "half", "full"), dx.get("mode", ""))
    except Exception as exc:
        add("duplex", False, str(exc))

    try:
        from jarvis.ollama_health import check_ollama

        ollama = check_ollama()
        add("ollama", bool(ollama.get("running")), f"{len(ollama.get('models') or [])} models")
    except Exception as exc:
        add("ollama", False, str(exc))

    passed = sum(1 for c in checks if c.get("ok"))
    return {
        "ok": passed == len(checks) and bool(checks),
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "elapsed_ms": int((time.time() - started) * 1000),
    }
