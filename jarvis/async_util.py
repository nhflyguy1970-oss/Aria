# Source Generated with Decompyle++
# File: async_util.cpython-312.pyc (Python 3.12)

'''Helpers to keep blocking work off the asyncio event loop.'''
from __future__ import annotations
import asyncio
import threading
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, TypeVar
T = TypeVar('T')
_SENTINEL = object()

async def run_sync(fn = None, *args, **kwargs):
    '''Run a blocking callable in the default thread pool.'''
    pass
# WARNING: Decompyle incomplete


def stream_sync_iter(iterator_factory = None, *, thread_name):
    '''Bridge a blocking sync generator into async iteration via a queue.'''
    pass
# WARNING: Decompyle incomplete

