# Source Generated with Decompyle++
# File: audio_session.cpython-312.pyc (Python 3.12)

'''Persist Audio tab session (last path, transcript, summary).'''
from __future__ import annotations
import json
from jarvis.config import DATA_DIR
SESSION_FILE = DATA_DIR / 'audio' / 'session.json'

def load_session():
    if not SESSION_FILE.exists():
        return { }
    
    try:
        return json.loads(SESSION_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def save_session(patch = None):
    data = load_session()
# WARNING: Decompyle incomplete

