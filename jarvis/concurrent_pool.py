"""Background thread pool for parallel long-running jobs."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

_executor: ThreadPoolExecutor | None = None


def max_workers() -> int:
    raw = os.getenv("JARVIS_PARALLEL_WORKERS", "2").strip()
    try:
        return max(1, min(4, int(raw)))
    except ValueError:
        return 2


def background_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=max_workers(),
            thread_name_prefix="jarvis-bg",
        )
    return _executor
