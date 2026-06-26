"""Tests for async_util helpers."""

import asyncio

from jarvis.async_util import run_sync, stream_sync_iter


def test_run_sync_runs_in_thread():
    async def _run():
        def add(a, b):
            return a + b

        assert await run_sync(add, 2, 3) == 5

    asyncio.run(_run())


def test_stream_sync_iter_bridges_generator():
    async def _run():
        def gen():
            yield {"a": 1}
            yield {"b": 2}

        out = []
        async for item in stream_sync_iter(gen):
            out.append(item)
        assert out == [{"a": 1}, {"b": 2}]

    asyncio.run(_run())
