# Source Generated with Decompyle++
# File: request_activity.cpython-312.pyc (Python 3.12)

'''Track in-flight assistant and heavy API requests so restarts/watchdog defer.'''
from __future__ import annotations
import threading
_lock = threading.Lock()
_active = 0
_heavy_active = 0
HEAVY_API_EXACT = frozenset({
    '/api/knowledge',
    '/api/memory/all',
    '/api/memory/conflicts'})
HEAVY_API_PREFIXES = ('/api/knowledge/research', '/api/memory/stats')

def is_heavy_api_path(path = None):
    pass
# WARNING: Decompyle incomplete


def begin():
    global _active
    _lock
    _active += 1
    None(None, None)
    return None
    with None:
        if not None:
            pass


def end():
    global _active
    _lock
    _active = max(0, _active - 1)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def begin_heavy():
    global _heavy_active
    _lock
    _heavy_active += 1
    None(None, None)
    return None
    with None:
        if not None:
            pass


def end_heavy():
    global _heavy_active
    _lock
    _heavy_active = max(0, _heavy_active - 1)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def active():
    _lock
    None(None, None)
    return 
    with None:
        if not None, _active > 0:
            pass


def heavy_active():
    _lock
    None(None, None)
    return 
    with None:
        if not None, _heavy_active > 0:
            pass


def count():
    _lock
    None(None, None)
    return 
    with None:
        if not None, _active:
            pass


def heavy_count():
    _lock
    None(None, None)
    return 
    with None:
        if not None, _heavy_active:
            pass

