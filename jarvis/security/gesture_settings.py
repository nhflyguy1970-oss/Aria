# Source Generated with Decompyle++
# File: gesture_settings.cpython-312.pyc (Python 3.12)

'''Persisted browser gesture mode + calibration thresholds.'''
from __future__ import annotations
import json
from pathlib import Path
from jarvis.config import DATA_DIR
GESTURES_FILE = DATA_DIR / 'security' / 'gestures.json'

def load_gesture_settings(path = None):
    if not path:
        path
    p = GESTURES_FILE
    if not p.is_file():
        return {
            'mode': 'off',
            'calibration': { } }
    
    try:
        data = json.loads(p.read_text(encoding = 'utf-8'))
        if not data.get('mode'):
            data.get('mode')
        if not data.get('calibration'):
            data.get('calibration')
        return {
            'mode': 'off',
            'calibration': { } }
    except Exception:
        return 



def merge_gesture_settings(body = None, existing = None):
    if not existing:
        existing
    base = {
        'mode': 'off',
        'calibration': { } }
    if not base.get('mode'):
        base.get('mode')
    mode = body.get('mode', 'off')
    if not base.get('calibration'):
        base.get('calibration')
    calibration = dict({ })
    incoming = body.get('calibration')
    if isinstance(incoming, dict) and incoming:
        calibration.update(incoming)
    return {
        'mode': mode,
        'calibration': calibration }


def save_gesture_settings(body = None, path = None):
    if not path:
        path
    p = GESTURES_FILE
    p.parent.mkdir(parents = True, exist_ok = True)
    merged = merge_gesture_settings(body, load_gesture_settings(p))
    p.write_text(json.dumps(merged, indent = 2), encoding = 'utf-8')
    return merged

