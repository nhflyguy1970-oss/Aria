# Source Generated with Decompyle++
# File: journal_brain_feed.cpython-312.pyc (Python 3.12)

'''Debounced auto-feed from bullet journal into brain memory.'''
from __future__ import annotations
import logging
import threading
import time
from typing import Any
log = logging.getLogger('jarvis.journal_brain_feed')
_LOCK = threading.Lock()
_LAST_FEED: 'dict[str, float]' = { }
_DEBOUNCE_SEC = float(__import__('os').getenv('JARVIS_JOURNAL_FEED_DEBOUNCE', '45'))

def _enabled():
    auto_journal_learn_enabled = auto_journal_learn_enabled
    import jarvis.brain_memory
    return auto_journal_learn_enabled()


def _substantive_bullet(bullet = None):
    if not bullet:
        return False
    if not bullet.get('content'):
        bullet.get('content')
    content = ''.strip()
    if len(content) < 12:
        return False
    if bullet.get('type') == 'note' and bullet.get('status') == 'open':
        return True
    if bullet.get('type') == 'task':
        return True
    return bullet.get('type') == 'event'


def maybe_feed_journal_event(memory = None, journal = None, *, event, bullet, day, migrated):
    '''Schedule debounced journal → brain learning (non-blocking).'''
    pass
# WARNING: Decompyle incomplete


def _feed_worker(memory, journal, event = None, bullet = None, day = None, migrated = ('event', 'str', 'bullet', 'dict | None', 'day', 'str | None', 'migrated', 'int', 'return', 'None')):
    pass
# WARNING: Decompyle incomplete


def run_journal_day_consolidation(memory = None, journal = None, *, day):
    '''Nightly summary of journal tasks, completions, and habits into memory.'''
    pass
# WARNING: Decompyle incomplete

