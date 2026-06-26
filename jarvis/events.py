# Source Generated with Decompyle++
# File: events.cpython-312.pyc (Python 3.12)

'''Lightweight in-process event bus for automation hooks.'''
from __future__ import annotations
import logging
import threading
from collections import defaultdict
from typing import Any, Callable
logger = logging.getLogger('jarvis.events')
_lock = threading.Lock()
_subscribers: 'dict[str, list[Callable[..., None]]]' = defaultdict(list)

def on(event = None, handler = None):
    '''Subscribe to an event name (e.g. job_done, memory_updated).'''
    pass
# WARNING: Decompyle incomplete


def off(event = None, handler = None):
    _lock
    if handler in _subscribers.get(event, []):
        _subscribers[event].remove(handler)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def emit(event = None, **payload):
    '''Emit an event to all subscribers. Failures in handlers are logged, not raised.'''
    _lock
    handlers = list(_subscribers.get(event, []))
    None(None, None)
# WARNING: Decompyle incomplete


def emit_job_done(*, queue, job_id, result, label):
    if not result:
        result
    if not result:
        result
    payload = {
        'queue': queue,
        'job_id': job_id,
        'result': { },
        'ok': bool({ }.get('ok')),
        'label': label }
# WARNING: Decompyle incomplete


def emit_job_progress(*, queue, job_id, label, pct, message, done, error):
    payload = {
        'queue': queue,
        'job_id': job_id,
        'label': label,
        'pct': pct,
        'message': message,
        'done': done,
        'error': error }
# WARNING: Decompyle incomplete


def _publish_ws(event = None, **payload):
    pass
# WARNING: Decompyle incomplete


def emit_memory_updated(*, action, entry_id):
    emit('memory_updated', action = action, entry_id = entry_id)


def emit_ha_state_changed(*, entity_id, state):
    emit('ha_state_changed', entity_id = entity_id, state = state)


def emit_voice_state(state = None, *, detail):
    '''Broadcast voice UI state: idle|listening|thinking|speaking.'''
    payload = {
        'state': state,
        'detail': detail }
# WARNING: Decompyle incomplete


def emit_stt_partial(text = None, *, final):
    '''Stream speech-to-text partials to the GUI (Whisper live or RealTimeSTT).'''
    if not text:
        text
    t = ''.strip()
    if not t and final:
        return None
    payload = {
        'text': t,
        'final': final }
# WARNING: Decompyle incomplete

