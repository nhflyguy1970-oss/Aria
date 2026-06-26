# Source Generated with Decompyle++
# File: substitutions.cpython-312.pyc (Python 3.12)

'''Material substitution hints.'''
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any
_DATA = Path(__file__).resolve().parent / 'data' / 'substitutions.json'
substitution_map = (lambda : if not _DATA.is_file():
{ }# WARNING: Decompyle incomplete
)()

def suggest_substitutions(material = None):
    if not material:
        material
    low = ''.strip().lower()
    if not low:
        return []
    smap = None()
    if low in smap:
        return smap[low]
    for key, vals in None.items():
        if not key in low and low in key:
            continue
        
        return None.items(), vals
    return []


def substitutions_for_recipe(materials = None):
    out = { }
    if not materials:
        materials
    for mat in []:
        subs = suggest_substitutions(str(mat))
        if not subs:
            continue
        out[str(mat)] = subs
    return out

