"""Voice round-trip smoke test."""

from __future__ import annotations

import time
from typing import Any


def run_voice_smoke(*, assistant=None) -> dict[str, Any]:
    started = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    try:
        from jarvis.voice_settings import load_voice_settings

        settings = load_voice_settings()
        add("voice_settings", bool(settings), f"duplex={settings.get('duplex_mode', '?')}")
    except Exception as exc:
        add("voice_settings", False, str(exc))

    try:
        from jarvis.cloud_live_voice import cloud_live_status

        live = cloud_live_status()
        add("cloud_live", bool(live.get("available")), live.get("message", ""))
    except Exception as exc:
        add("cloud_live", False, str(exc))

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
