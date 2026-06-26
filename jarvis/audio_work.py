# Source Generated with Decompyle++
# File: audio_work.cpython-312.pyc (Python 3.12)

'''Serialize GPU-heavy audio work (Whisper, MusicGen, song studio).'''
from __future__ import annotations
import logging
import os
import threading
import time
from contextlib import contextmanager
log = logging.getLogger('jarvis.audio_work')
_lock = threading.Lock()
_holder: 'str | None' = None
_since = 0
audio_gpu_slot = (lambda label = None: pass# WARNING: Decompyle incomplete
)()

def audio_gpu_status():
    _lock
    if not _holder:
        _holder
    None(None, None)
    return 
    with None:
        if not None, {
            'busy': _holder is not None,
            'label': '',
            'since': _since if _holder else 0 }:
            pass

