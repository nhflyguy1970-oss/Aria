# Source Generated with Decompyle++
# File: room_aliases.cpython-312.pyc (Python 3.12)

'''Room alias map — one friendly name controls multiple devices.'''
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
ALIASES_FILE = DATA_DIR / 'room_aliases.json'

def _load():
    if not ALIASES_FILE.is_file():
        return { }
# WARNING: Decompyle incomplete


def list_aliases():
    return dict(_load())


def resolve_targets(target = None):
    '''Return device targets for a room alias, or [target] if not an alias.'''
    if not target:
        target
    t = ''.strip()
    if not t:
        return []
    key = None.lower()
    aliases = _load()
    if key in aliases:
        return list(aliases[key])
    for alias, devices in None.items():
        if not alias in key and key in alias:
            continue
        
        return None.items(), list(devices)
    return [
        t]


def control_alias(target = None, action = None, **kwargs):
    '''Control all devices in a room alias. Returns aggregate result.'''
    control_device = control_device
    import jarvis.device_router
    targets = resolve_targets(target)
# WARNING: Decompyle incomplete

