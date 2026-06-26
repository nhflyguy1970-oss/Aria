# Source Generated with Decompyle++
# File: reflection_loop.cpython-312.pyc (Python 3.12)

"""Nightly reflection — distill today's activity into strategy updates."""
from __future__ import annotations
import logging
import os
from datetime import date, datetime
from typing import Any
log = logging.getLogger('jarvis.reflection')
STRATEGIES_NAMESPACE = 'strategies'
REFLECTION_TAG = 'reflection'

def reflection_enabled():
    if os.getenv('JARVIS_REFLECTION_DAILY', '1') == '0':
        return False
    jarvis_preset_enabled = jarvis_preset_enabled
    import jarvis.world_state
    if jarvis_preset_enabled():
        return True
    return os.getenv('JARVIS_BRAIN_MODE', '').strip().lower() in ('1', 'true', 'yes')


def reflection_hour():
    
    try:
        return int(os.getenv('JARVIS_REFLECTION_HOUR', '22'))
    except ValueError:
        return 22



def reflection_status():
    _load_chat_settings = _load_chat_settings
    import jarvis.config
    if not _load_chat_settings().get('reflection_loop'):
        _load_chat_settings().get('reflection_loop')
    state = { }
    if not state.get('last_run_day'):
        state.get('last_run_day')
    if not state.get('last_strategies'):
        state.get('last_strategies')
    return {
        'enabled': reflection_enabled(),
        'hour': reflection_hour(),
        'last_run_day': '',
        'last_strategies': int(0) }


def _mark_run(day = None, count = None):
    _load_chat_settings = _load_chat_settings
    _write_chat_settings = _write_chat_settings
    import jarvis.config
    data = _load_chat_settings()
    data.setdefault('reflection_loop', { })['last_run_day'] = day
    data['reflection_loop']['last_strategies'] = count
    _write_chat_settings(data)


def _gather_context(*, memory_store, journal, day):
    lines = [
        f'''Date: {day}''']
# WARNING: Decompyle incomplete


def _generate_strategies(context = None):
    if not context.strip():
        return []
    prompt = f'''{context}\n\nReply with one rule per line, no numbering.'''
# WARNING: Decompyle incomplete


def _store_strategies(memory_store = None, rules = None):
    pass
# WARNING: Decompyle incomplete


def run_reflection(*, memory_store, journal, day, force):
    '''Run reflection for a day; skip if already done unless force.'''
    if not reflection_enabled() and force:
        return {
            'ok': False,
            'skipped': True,
            'reason': 'disabled' }
# WARNING: Decompyle incomplete


def run_scheduled(now = None):
    '''Called from proactive scheduler at configured hour.'''
    if not reflection_enabled():
        return None
    if not now:
        now
    now = datetime.now()
    if now.hour != reflection_hour() or now.minute > 10:
        return None
    return run_reflection()

