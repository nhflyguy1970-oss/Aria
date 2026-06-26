# Source Generated with Decompyle++
# File: restart_audit.cpython-312.pyc (Python 3.12)

'''Append-only audit log for server restart requests (who/why).'''
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
logger = logging.getLogger('jarvis.restart_audit')
AUDIT_FILE = DATA_DIR / 'logs' / 'restart_audit.jsonl'

def log_restart_event(source = None, **extra):
    '''Record a restart trigger. source: api | cli | tray | watchdog | flag | unknown.'''
    pass
# WARNING: Decompyle incomplete

