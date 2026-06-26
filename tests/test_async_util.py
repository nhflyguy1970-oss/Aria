"""Tests for async_util helpers."""

import asyncio

from jarvis.async_util import run_sync, stream_sync_iter


def test_run_sync_runs_in_thread():
    async def _run():
        result = await run_sync(lambda: 42)
        assert result == 42

    asyncio.run(_run())


def test_stream_sync_iter_bridges_generator():
    async def _run():
        def produce():
            yield {"n": 1}
            yield {"n": 2}

        seen = []
        async for event in stream_sync_iter(produce, thread_name="test-stream"):
            seen.append(event)
        assert seen == [{"n": 1}, {"n": 2}]

    asyncio.run(_run())
