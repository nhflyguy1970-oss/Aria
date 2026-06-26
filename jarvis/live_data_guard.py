# Source Generated with Decompyle++
# File: live_data_guard.cpython-312.pyc (Python 3.12)

'''Block accidental writes to live data/ during pytest.'''
from __future__ import annotations
import os
from pathlib import Path
from jarvis.config import PROJECT_ROOT
_LIVE_DATA_ROOT = (PROJECT_ROOT / 'data').resolve()
_guard_active = False

def enable_test_guard():
    global _guard_active
    _guard_active = True


def disable_test_guard():
    global _guard_active
    _guard_active = False


def guard_active():
    if _guard_active:
        _guard_active
    return os.environ.get('JARVIS_ALLOW_LIVE_DATA') != '1'


def assert_live_write_allowed(path = None):
    '''Raise if a test is about to write under the project data/ directory.'''
    if not guard_active():
        return None
    target = Path(path).resolve()
    if target == _LIVE_DATA_ROOT or _LIVE_DATA_ROOT in target.parents:
        raise RuntimeError(f'''Test attempted to write live Jarvis data: {target}. Use the data_dir fixture and patch DATA_DIR / JOURNAL_FILE / MEMORY_FILE.''')

