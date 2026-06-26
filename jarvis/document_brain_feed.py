# Source Generated with Decompyle++
# File: document_brain_feed.cpython-312.pyc (Python 3.12)

'''Debounced auto-learn from ingested documents when brain mode / flag is on.'''
from __future__ import annotations
import logging
import threading
import time
from pathlib import Path
log = logging.getLogger('jarvis.document_brain_feed')
_LOCK = threading.Lock()
_LAST_LEARN: 'dict[str, float]' = { }
_DEBOUNCE_SEC = float(__import__('os').getenv('JARVIS_DOCUMENT_LEARN_DEBOUNCE', '60'))

def auto_document_learn_enabled():
    _enabled = auto_document_learn_enabled
    import jarvis.brain_memory
    return _enabled()


def maybe_auto_learn_document(memory = None, path = None, *, title):
    '''Schedule debounced learn_from_file after ingest/upload (non-blocking).'''
    pass
# WARNING: Decompyle incomplete

