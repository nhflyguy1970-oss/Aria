# Source Generated with Decompyle++
# File: chat_cancel.cpython-312.pyc (Python 3.12)

'''Cooperative cancellation for in-flight chat streams.'''
from __future__ import annotations
import threading
_lock = threading.Lock()
_cancelled: 'set[str]' = set()

def begin(request_id = None):
    if not request_id:
        return None
    _lock
    _cancelled.discard(request_id)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def cancel(request_id = None):
    if not request_id:
        return False
    _lock
    _cancelled.add(request_id)
    None(None, None)
    return True
    with None:
        if not None:
            pass
    return True


def is_cancelled(request_id = None):
    if not request_id:
        return False
    _lock
    None(None, None)
    return 
    with None:
        if not None, request_id in _cancelled:
            pass


def finish(request_id = None):
    if not request_id:
        return None
    _lock
    _cancelled.discard(request_id)
    None(None, None)
    return None
    with None:
        if not None:
            pass

