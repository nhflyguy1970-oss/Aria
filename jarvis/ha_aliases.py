# Source Generated with Decompyle++
# File: ha_aliases.cpython-312.pyc (Python 3.12)

'''Room aliases for Home Assistant voice control.'''
from __future__ import annotations
import json
import re
from typing import Any
from jarvis.config import DATA_DIR
ALIASES_FILE = DATA_DIR / 'ha_aliases.json'

def _load():
    if not ALIASES_FILE.exists():
        return { }
# WARNING: Decompyle incomplete


def save_aliases(aliases = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    ALIASES_FILE.write_text(json.dumps({
        'aliases': aliases }, indent = 2), encoding = 'utf-8')
    return aliases


def get_aliases():
    return _load()


def set_alias(name = None, entity_ids = None):
    aliases = _load()
    if not name:
        name
    key = ''.lower().strip()
    if not key:
        raise ValueError('alias name required')
# WARNING: Decompyle incomplete


def resolve_alias(query = None):
    if not query:
        query
    q = re.sub('[\\s_]+', ' ', ''.lower()).strip()
    if not q:
        return []
    aliases = None()
    if q in aliases:
        return list(aliases[q])
    for key, ids in None.items():
        if not key in q and q in key:
            continue
        
        return None.items(), list(ids)
    return []

