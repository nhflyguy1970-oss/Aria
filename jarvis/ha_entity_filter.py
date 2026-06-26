# Source Generated with Decompyle++
# File: ha_entity_filter.cpython-312.pyc (Python 3.12)

'''Hide removed or unwanted Home Assistant entities from Jarvis.'''
from __future__ import annotations
import json
import re
from functools import lru_cache
from typing import Any
from jarvis.config import DATA_DIR
_HIDDEN_FILE = DATA_DIR / 'ha_hidden_entities.json'

def _norm(text = None):
    if not text:
        text
    return re.sub('[\\s_]+', ' ', ''.lower()).strip()

_hidden_config = (lambda : defaults = {
'entity_ids': [],
'name_keywords': [
'bathroom',
'bath',
'shower'],
'hide_unavailable_lights': True }# WARNING: Decompyle incomplete
)()

def entity_hidden_from_jarvis(st = None):
    '''True when Jarvis should not list or control this HA entity.'''
    pass
# WARNING: Decompyle incomplete


def filter_visible_entities(states = None):
    pass
# WARNING: Decompyle incomplete

