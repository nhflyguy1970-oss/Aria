"""WebSocket event hub for job/status push."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

log = logging.getLogger("jarvis.ws")
_subscribers: set[Any] = set()
_loop: asyncio.AbstractEventLoop | None = None


def set_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    global _loop
    _loop = loop


def subscribe(ws: Any) -> None:
    _subscribers.add(ws)


def unsubscribe(ws: Any) -> None:
    _subscribers.discard(ws)


async def _broadcast_async(payload: dict[str, Any]) -> None:
    dead: list[Any] = []
    text = json.dumps(payload)
    for ws in list(_subscribers):
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unsubscribe(ws)


def publish(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    loop = _loop
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast_async(payload), loop)
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_broadcast_async(payload))
    except RuntimeError:
        log.debug("ws publish skipped (no loop): %s", event)
