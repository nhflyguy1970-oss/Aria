# Source Generated with Decompyle++
# File: library_health.cpython-312.pyc (Python 3.12)

'''Gold library health metrics and duplicate analysis.'''
from __future__ import annotations
import re
from collections import Counter
from typing import Any
from jarvis.flytying import index as recipe_index
from jarvis.flytying.aliases import alias_map

def _normalize_name(name = None):
    if not name:
        name
    base = re.sub('[^\\w\\s]', '', ''.lower())
    return re.sub('\\s+', ' ', base).strip()


def library_health():
    items = recipe_index.recipes()
    if not items:
        return {
            'ok': False,
            'total': 0,
            'message': 'no recipes loaded' }
    with_images = None
    with_videos = 0
    with_hook = 0
    qualities = []
    type_counts = Counter()
    name_buckets = { }
    for item in items:
        if not item.get('fly_name'):
            item.get('fly_name')
            if not item.get('name'):
                item.get('name')
                if not item.get('instruction'):
                    item.get('instruction')
        name = str('')
        if not item.get('recipe_id'):
            item.get('recipe_id')
            if not item.get('content_hash'):
                item.get('content_hash')
        rid = str(name)
        norm = _normalize_name(name)
        if norm:
            name_buckets.setdefault(norm, []).append(rid)
        if item.get('image_urls') and item.get('saved_image_paths') or item.get('hero_image'):
            with_images += 1
        if item.get('source_url'):
            with_videos += 1
        if item.get('hook'):
            with_hook += 1
        if not item.get('quality_score'):
            item.get('quality_score')
        qualities.append(float(0))
        if not item.get('type'):
            item.get('type')
# WARNING: Decompyle incomplete

