"""Interrupt policy — urgent vs useful notifications with focus/voice respect."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from typing import Any

log = logging.getLogger("jarvis.interrupt")

_voice_state = "idle"
_focus_mode = False
_lock = threading.Lock()
_installed = False


def _on_voice_state(*, state: str = "", **_: Any) -> None:
    global _voice_state
    with _lock:
        _voice_state = (state or "idle").strip().lower()


def _refresh_focus_mode() -> None:
    global _focus_mode
    try:
        from jarvis.config import _load_chat_settings

        preset = ((_load_chat_settings().get("scene_state") or {}).get("active_preset") or "").lower()
        _focus_mode = "focus" in preset
    except Exception:
        _focus_mode = False


def install_hooks() -> None:
    global _installed
    if _installed:
        return
    _installed = True
    from jarvis.events import emit, on

    on("voice_state", _on_voice_state)

    @on("job_done")
    def _job_done(**payload: Any) -> None:
        queue = payload.get("queue") or ""
        ok = payload.get("ok")
        label = payload.get("label") or queue
        if ok:
            evaluate_interrupt(
                "job_complete",
                title="ARIA",
                body=f"{label} finished",
                tier="useful",
            )
        else:
            evaluate_interrupt(
                "job_failed",
                title="ARIA",
                body=f"{label} failed",
                tier="urgent",
            )

    @on("print_job_update")
    def _print_update(**payload: Any) -> None:
        status = (payload.get("status") or "").lower()
        if status == "failed":
            evaluate_interrupt(
                "print_fail",
                title="Print failed",
                body=str(payload.get("message") or "Print job failed")[:200],
                tier="urgent",
            )
        elif status in ("handoff", "printing") and payload.get("notify_complete"):
            evaluate_interrupt(
                "print_complete",
                title="Print ready",
                body=str(payload.get("message") or "Print job update")[:200],
                tier="useful",
            )


def should_interrupt(*, tier: str = "useful") -> bool:
    """Return False when focus mode or voice is active (except urgent)."""
    _refresh_focus_mode()
    with _lock:
        voice_busy = _voice_state in ("listening", "thinking", "speaking")
    if tier == "urgent":
        return True
    if _focus_mode or voice_busy:
        return False
    return True


def _notify(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "-a", "Jarvis", title, body[:240]],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception as exc:
        log.debug("Interrupt notify failed: %s", exc)


def _tts(body: str) -> None:
    if os.getenv("JARVIS_INTERRUPT_TTS", "0") != "1":
        return
    try:
        from jarvis.modules.audio import speak_text

        speak_text(body[:180])
    except Exception:
        pass


def evaluate_interrupt(
    kind: str,
    *,
    title: str,
    body: str,
    tier: str = "useful",
) -> dict[str, Any]:
    """Evaluate and optionally fire desktop notification."""
    if not should_interrupt(tier=tier):
        return {"ok": True, "fired": False, "reason": "suppressed", "kind": kind}
    _notify(title, body)
    if tier == "urgent":
        _tts(body)
    return {"ok": True, "fired": True, "kind": kind, "tier": tier}


def check_services_health(services: dict[str, Any] | None = None) -> None:
    """Urgent interrupt when required services go down."""
    try:
        if services is None:
            from jarvis.services import get_status

            services = get_status()
        down = [
            s.get("label") or s.get("name")
            for s in (services.get("services") or [])
            if s.get("required") and not s.get("running")
        ]
        if down:
            evaluate_interrupt(
                "server_down",
                title="ARIA services",
                body=f"Required service down: {', '.join(down)}",
                tier="urgent",
            )
    except Exception as exc:
        log.debug("Service health interrupt skipped: %s", exc)
