# Source Generated with Decompyle++
# File: proposal_store.cpython-312.pyc (Python 3.12)

'''Persist pending code proposals across restarts.'''
from __future__ import annotations
import json
from jarvis.config import DATA_DIR
PROPOSALS_FILE = DATA_DIR / 'pending_proposals.json'

def load():
    if not PROPOSALS_FILE.exists():
        return { }
    
    try:
        data = json.loads(PROPOSALS_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return 



def save(proposals = None):
    PROPOSALS_FILE.parent.mkdir(parents = True, exist_ok = True)
    clean = { }
# WARNING: Decompyle incomplete


def sync(proposals = None):
    save(proposals)

