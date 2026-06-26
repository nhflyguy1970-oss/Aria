# Source Generated with Decompyle++
# File: search.cpython-312.pyc (Python 3.12)

'''Unified fly-tying search — single entry for API, handlers, and chat.'''
from __future__ import annotations
from typing import Any
from jarvis.flytying import index as recipe_index
from jarvis.flytying.aliases import expand_query
from jarvis.flytying.user_store import list_favorites

def unified_search(q = None, *, fly_type, limit, min_quality, favorites_only, hook_size, semantic):
    bridge = bridge
    import jarvis.flytying
    (expanded, alias_terms) = expand_query(q)
    if not expanded:
        expanded
    search_q = q
    (rows, mode) = recipe_index.search(search_q, fly_type = fly_type, limit = limit)
    if semantic:
        if not q:
            q
        if ''.strip():
            if not q:
                q
            if len(''.split()) > 1:
                (hybrid_rows, hybrid_mode) = bridge.list_recipes(q = q, fly_type = fly_type, limit = limit)
                if hybrid_mode == 'hybrid':
                    rows = hybrid_rows
                    mode = 'hybrid'
    if alias_terms and mode == 'keyword':
        mode = 'alias'
    fav_set = set(list_favorites()) if favorites_only else set()
    filtered = []
    seen = set()
# WARNING: Decompyle incomplete

