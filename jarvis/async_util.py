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


class _SyncStreamBridge:
    """Bridge a blocking sync generator into async iteration via a queue."""

    __slots__ = ("_queue", "_thread_name", "_iterator_factory", "_started")

    def __init__(
        self,
        iterator_factory: Callable[[], Iterator[Any]],
        *,
        thread_name: str,
    ) -> None:
        self._iterator_factory = iterator_factory
        self._thread_name = thread_name
        self._queue: asyncio.Queue[Any] | None = None
        self._started = False

    def _ensure_started(self) -> asyncio.Queue[Any]:
        if self._queue is not None:
            return self._queue
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._queue = queue

        def producer() -> None:
            try:
                iterator = self._iterator_factory()
                if iterator is None:
                    raise TypeError(
                        f"{self._iterator_factory!r} returned None — expected a sync generator/iterator"
                    )
                for item in iterator:
                    asyncio.run_coroutine_threadsafe(queue.put(item), loop).result(timeout=3600)
            except Exception as exc:
                asyncio.run_coroutine_threadsafe(queue.put(exc), loop).result(timeout=30)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(_SENTINEL), loop).result(timeout=30)

        threading.Thread(target=producer, daemon=True, name=self._thread_name).start()
        self._started = True
        return queue

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
        queue = self._ensure_started()
        item = await queue.get()
        if item is _SENTINEL:
            raise StopAsyncIteration
        if isinstance(item, Exception):
            raise item
        return item


def stream_sync_iter(
    iterator_factory: Callable[[], Iterator[Any]],
    *,
    thread_name: str = "jarvis-stream",
) -> _SyncStreamBridge:
    """Return an async-iterable bridge over a blocking sync generator."""
    return _SyncStreamBridge(iterator_factory, thread_name=thread_name)
