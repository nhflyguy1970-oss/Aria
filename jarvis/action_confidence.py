# Source Generated with Decompyle++
# File: action_confidence.cpython-312.pyc (Python 3.12)

'''Confidence-weighted autonomy — track action outcomes and gate confirmations.'''
from __future__ import annotations
import json
import os
import threading
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
STORE_FILE = DATA_DIR / 'action_confidence.json'
_lock = threading.Lock()
_stats: 'dict[str, dict[str, int]]' = { }
_loaded = False
MIN_SAMPLES = max(3, int(os.getenv('JARVIS_CONFIDENCE_MIN_SAMPLES', '5')))
HIGH_THRESHOLD = float(os.getenv('JARVIS_CONFIDENCE_HIGH', '0.75'))
LOW_THRESHOLD = float(os.getenv('JARVIS_CONFIDENCE_LOW', '0.45'))
TRACKED_ACTIONS = frozenset({
    'ha_scene',
    'ha_control',
    'scene_preset',
    'scene_recall',
    'workflow_run'})

def _load():
    global _loaded, _stats
    if _loaded:
        return None
    _loaded = True
    if not STORE_FILE.is_file():
        _stats = { }
        return None
# WARNING: Decompyle incomplete


def _save():
    STORE_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(STORE_FILE)
    _lock
    STORE_FILE.write_text(json.dumps(_stats, indent = 2), encoding = 'utf-8')
    None(None, None)
    return None
    with None:
        if not None:
            pass


def record_outcome(action_type = None, *, ok):
    '''Record success/failure for an action type.'''
    if not action_type:
        action_type
    key = ''.strip().lower()
    if not key:
        return None
    _load()
    _lock
    row = _stats.setdefault(key, {
        'success': 0,
        'failure': 0 })
    if ok:
        if not row.get('success'):
            row.get('success')
        row['success'] = int(0) + 1
    elif not row.get('failure'):
        row.get('failure')
    row['failure'] = int(0) + 1
    None(None, None)
    _save()
    return None
    with None:
        if not None:
            pass
    _save()


def confidence_for(action_type = None):
    '''Return 0–1 success rate; 0.5 when insufficient samples.'''
    if not action_type:
        action_type
    key = ''.strip().lower()
    if not key:
        return 0.5
    _load()
    _lock
    if not _stats.get(key):
        _stats.get(key)
    row = { }
    if not row.get('success'):
        row.get('success')
    success = int(0)
    if not row.get('failure'):
        row.get('failure')
    failure = int(0)
    None(None, None)
# WARNING: Decompyle incomplete


def confidence_tier(action_type = None):
    '''high | medium | low based on confidence_for.'''
    c = confidence_for(action_type)
    if c >= HIGH_THRESHOLD:
        return 'high'
    if c <= LOW_THRESHOLD:
        return 'low'
    return 'medium'


def autonomy_decision(action_type = None):
    '''Decision for whether to confirm, explain, or proceed silently.'''
    tier = confidence_tier(action_type)
    c = confidence_for(action_type)
    needs_confirm = tier == 'low'
    explain = tier == 'medium'
    return {
        'action_type': action_type,
        'confidence': round(c, 3),
        'tier': tier,
        'needs_confirm': needs_confirm,
        'explain': explain,
        'brief_note': tier == 'high' }


def snapshot():
    _load()
    _lock
# WARNING: Decompyle incomplete

