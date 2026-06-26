# Source Generated with Decompyle++
# File: ws_hub.cpython-312.pyc (Python 3.12)

'''WebSocket event hub for job/status push.'''
from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
log = logging.getLogger('jarvis.ws')
_subscribers: 'set[Any]' = set()
_loop: 'asyncio.AbstractEventLoop | None' = None

def set_loop(loop = None):
    global _loop
    _loop = loop


def subscribe(ws = None):
    _subscribers.add(ws)


def unsubscribe(ws = None):
    _subscribers.discard(ws)


async def _broadcast_async(payload = None):
    pass
# WARNING: Decompyle incomplete


def publish(event = None, **fields):
    pass
# WARNING: Decompyle incomplete

