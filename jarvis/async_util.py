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
    """Bridge a blocking sync generator into async iteration via a queue.

    The consumer may abandon the stream (first-progress timeout, client
    disconnect, error). Without an explicit stop the producer thread kept
    draining the generator to completion, so ``process_stream``'s ``finally``
    — which releases the global request lock — never ran and every later
    request was refused with "Another request is still finishing".
    ``close()`` signals the producer and closes the underlying generator from
    the producer thread, so that ``finally`` always runs.
    """

    __slots__ = (
        "_queue",
        "_thread_name",
        "_iterator_factory",
        "_started",
        "_stop",
        "_finished",
        "_thread",
    )

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
        self._stop = threading.Event()
        self._finished = threading.Event()
        self._thread: threading.Thread | None = None

    def _ensure_started(self) -> asyncio.Queue[Any]:
        if self._queue is not None:
            return self._queue
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._queue = queue

        def _put(item: Any, timeout: float) -> bool:
            """Hand an item to the loop; False once the loop can no longer take it."""
            try:
                asyncio.run_coroutine_threadsafe(queue.put(item), loop).result(timeout=timeout)
                return True
            except Exception:
                return False

        def producer() -> None:
            iterator: Iterator[Any] | None = None
            try:
                iterator = self._iterator_factory()
                if iterator is None:
                    raise TypeError(
                        f"{self._iterator_factory!r} returned None — expected a sync generator/iterator"
                    )
                for item in iterator:
                    if self._stop.is_set():
                        break
                    if not _put(item, 3600):
                        break
                    if self._stop.is_set():
                        break
            except Exception as exc:
                if not self._stop.is_set():
                    _put(exc, 30)
            finally:
                # Closing here (never from the consumer thread) throws GeneratorExit
                # at the generator's current yield, so its finally — and the request
                # lock release — runs deterministically.
                close = getattr(iterator, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
                _put(_SENTINEL, 30)
                self._finished.set()

        thread = threading.Thread(target=producer, daemon=True, name=self._thread_name)
        self._thread = thread
        self._started = True
        thread.start()
        return queue

    def close(self) -> None:
        """Signal the producer to stop. Idempotent, non-blocking, thread-safe."""
        self._stop.set()

    @property
    def closed(self) -> bool:
        return self._stop.is_set()

    def wait_closed(self, timeout: float | None = None) -> bool:
        """Block until the producer thread has exited. True if it finished."""
        if not self._started:
            return True
        return self._finished.wait(timeout)

    async def aclose(self, timeout: float = 5.0) -> bool:
        """Signal the producer and await its exit without blocking the loop."""
        self.close()
        if not self._started:
            return True
        if self._finished.is_set():
            return True
        return await asyncio.to_thread(self._finished.wait, timeout)

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
        if self._stop.is_set() and self._queue is None:
            raise StopAsyncIteration
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
