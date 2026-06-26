# Source Generated with Decompyle++
# File: config.cpython-312.pyc (Python 3.12)

'''Fly-tying subsystem configuration.'''
from __future__ import annotations
import os
from pathlib import Path
DEFAULT_FLYTYING_ROOT = Path('/media/jeff/C/fly_fishing_project')

def flytying_root():
    if not os.environ.get('JARVIS_FLYTYING_ROOT'):
        os.environ.get('JARVIS_FLYTYING_ROOT')
    raw = ''.strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if None.is_dir():
        return DEFAULT_FLYTYING_ROOT


def gold_recipes_path():
    out = os.environ.get('FLY_OUTPUT_DIR', '').strip()
    if out:
        return Path(out).expanduser() / 'gold_recipes.jsonl'
    return None() / 'output' / 'gold_recipes.jsonl'


def images_root():
    out = os.environ.get('FLY_OUTPUT_DIR', '').strip()
    if out:
        return Path(out).expanduser() / 'images'
    return None() / 'output' / 'images'

