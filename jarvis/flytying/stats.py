# Source Generated with Decompyle++
# File: stats.cpython-312.pyc (Python 3.12)

'''Fast filesystem stats for the fly-tying dataset (no Blackfly import).'''
from __future__ import annotations
import json
from pathlib import Path
from jarvis.flytying.config import flytying_root, gold_recipes_path

def read_status():
    root = flytying_root()
    gold = gold_recipes_path()
    out = root / 'output'
    stats_file = out / 'gold_stats.json'
    gold_count = 0
    types = { }
# WARNING: Decompyle incomplete

