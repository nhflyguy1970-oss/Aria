# Source Generated with Decompyle++
# File: aliases.cpython-312.pyc (Python 3.12)

'''Pattern name aliases for fly-tying search.'''
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any
_DATA = Path(__file__).resolve().parent / 'data' / 'aliases.json'
alias_map = (lambda : if not _DATA.is_file():
{ }# WARNING: Decompyle incomplete
)()

def expand_query(q = None):
    '''Return (expanded_query_string, alias_terms_used).'''
    if not q:
        q
    needle = ''.strip().lower()
    if not needle:
        return ('', [])
    amap = None()
    terms = [
        needle]
    used = []
    for tok in needle.split():
        low = tok.lower()
        if not low in amap:
            continue
        used.append(low)
        terms.extend(amap[low])
    if needle in amap:
        used.append(needle)
        terms.extend(amap[needle])
    seen = set()
    unique = []
    for t in terms:
        t = t.strip().lower()
        if not t:
            continue
        if not t not in seen:
            continue
        seen.add(t)
        unique.append(t)
    return (' '.join(unique), used)


def aliases_for_name(name = None):
    if not name:
        name
    low = ''.strip().lower()
    if not low:
        return []
    amap = None()
    hits = set(amap.get(low, []))
    for key, vals in amap.items():
        if not low in vals and key in low and low in key:
            continue
        hits.add(key)
        hits.update(vals)
    hits.discard(low)
    return sorted(hits)[:12]

