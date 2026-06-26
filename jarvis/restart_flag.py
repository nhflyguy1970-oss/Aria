# Source Generated with Decompyle++
# File: restart_flag.cpython-312.pyc (Python 3.12)

'''Flag file so watchdog/tray know a server restart was intentional.'''
from __future__ import annotations
import time
from pathlib import Path
from jarvis.config import DATA_DIR
_FLAG = DATA_DIR / 'server_restart.flag'

def mark_restart_started():
    _FLAG.parent.mkdir(parents = True, exist_ok = True)
    _FLAG.write_text(str(time.time()), encoding = 'utf-8')


def clear_restart_flag():
    
    try:
        _FLAG.unlink(missing_ok = True)
        return None
    except OSError:
        return None



def controlled_restart_active(max_age_sec = None):
    if not _FLAG.is_file():
        return False
    
    try:
        started = float(_FLAG.read_text(encoding = 'utf-8').strip())
        return time.time() - started < max_age_sec
    except (OSError, ValueError):
        return True


