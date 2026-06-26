"""Helpers to keep blocking work off the asyncio event loop."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, TypeVar

T = TypeVar("T")
_SENTINEL = object()


async def run_sync(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking callable in the default thread pool."""
    return await asyncio.to_thread(fn, *args, **kwargs)


async def stream_sync_iter(
    iterator_factory: Callable[[], Iterator[Any]],
    *,
    thread_name: str = "jarvis-stream",
) -> AsyncIterator[Any]:
    """Bridge a blocking sync generator into async iteration via a queue."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Any] = asyncio.Queue()

    def producer() -> None:
        try:
            for item in iterator_factory():
                asyncio.run_coroutine_threadsafe(queue.put(item), loop).result(timeout=3600)
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(queue.put(exc), loop).result(timeout=30)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(_SENTINEL), loop).result(timeout=30)

    threading.Thread(target=producer, daemon=True, name=thread_name).start()
    while True:
        item = await queue.get()
        if item is _SENTINEL:
            break
        if isinstance(item, Exception):
            raise item
        yield item
