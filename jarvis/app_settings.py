# Source Generated with Decompyle++
# File: app_settings.cpython-312.pyc (Python 3.12)

'''Persisted GUI preferences (survives server restart).'''
from __future__ import annotations
import json
import logging
from pathlib import Path
from jarvis.config import DATA_DIR
log = logging.getLogger('jarvis')
SETTINGS_FILE = DATA_DIR / 'app_settings.json'

def load():
    if not SETTINGS_FILE.exists():
        return { }
    
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError, TypeError):
        exc = None
        log.warning('Could not read %s: %s', SETTINGS_FILE, exc)
        del exc
        return None
        None = 
        del exc



def save(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    SETTINGS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')
    
    try:
        SETTINGS_FILE.chmod(384)
        return None
    except OSError:
        return None



def get_uncensored():
    return bool(load().get('uncensored'))


def set_uncensored_pref(enabled = None):
    data = load()
    data['uncensored'] = bool(enabled)
    save(data)

