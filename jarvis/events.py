"""Lightweight in-process event bus for automation hooks."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger("jarvis.events")

_lock = threading.Lock()
_subscribers: dict[str, list[Callable[..., None]]] = defaultdict(list)


def on(event: str, handler: Callable[..., None] | None = None) -> Callable[..., None]:
    """Subscribe to an event name (e.g. job_done, memory_updated)."""

    def register(fn: Callable[..., None]) -> Callable[..., None]:
        with _lock:
            _subscribers[event].append(fn)
        return fn

    if handler is not None:
        return register(handler)
    return register


def off(event: str, handler: Callable[..., None]) -> None:
    with _lock:
        if handler in _subscribers.get(event, []):
            _subscribers[event].remove(handler)


def emit(event: str, **payload: Any) -> None:
    """Emit an event to all subscribers. Failures in handlers are logged, not raised."""
    with _lock:
        handlers = list(_subscribers.get(event, []))
    for fn in handlers:
        try:
            fn(event=event, **payload)
        except Exception as exc:
            logger.warning("Event handler failed for %s: %s", event, exc)


def emit_job_done(*, queue: str, job_id: str, result: dict | None, label: str = "") -> None:
    emit(
        "job_done",
        queue=queue,
        job_id=job_id,
        result=result or {},
        ok=bool((result or {}).get("ok")),
        label=label,
    )


def emit_memory_updated(*, action: str, entry_id: str | None = None) -> None:
    emit("memory_updated", action=action, entry_id=entry_id)


def emit_ha_state_changed(*, entity_id: str, state: str | None = None) -> None:
    emit("ha_state_changed", entity_id=entity_id, state=state)


def emit_voice_state(state: str, *, detail: str = "", **extra) -> None:
    """Publish voice state on the in-process bus and WebSocket hub."""
    try:
        from jarvis.voice_product.status_bus import set_voice_state

        set_voice_state(
            state,
            detail=detail,
            partial=str(extra.get("partial") or ""),
            cloud_session=str(extra.get("cloud_session") or ""),
            error=str(extra.get("error") or ""),
            publish=True,
        )
        return
    except Exception:
        pass
    emit("voice_state", state=state, detail=detail, **extra)
    try:
        from jarvis.ws_hub import publish as ws_publish

        ws_publish("voice_state", state=state, detail=detail, **extra)
    except Exception:
        pass


def emit_stt_partial(text: str, *, final: bool = False) -> None:
    try:
        from jarvis.voice_product.status_bus import emit_stt_partial as bus_partial

        bus_partial(text, final=final)
        return
    except Exception:
        pass
    emit("stt_partial", text=text, final=final)
    try:
        from jarvis.ws_hub import publish as ws_publish

        ws_publish("stt_partial", text=text, final=final)
    except Exception:
        pass
