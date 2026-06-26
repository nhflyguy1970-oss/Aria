# Source Generated with Decompyle++
# File: coding_test_impact.cpython-312.pyc (Python 3.12)

'''Predict which tests run after applying file changes.'''
from __future__ import annotations
from pathlib import Path
from jarvis.coding_verify import _pytest_targets

def tests_for_files(py_files = None, base = None):
    seen = set()
    targets = []
    for t in _pytest_targets(py_files, base):
        rel = str(t.relative_to(base)) if t.is_relative_to(base) else str(t)
        if not rel not in seen:
            continue
        if not t.exists():
            continue
        seen.add(rel)
        targets.append(rel)
    return targets


def format_test_impact(py_files = None, base = None):
    targets = tests_for_files(py_files, base)
    if not targets:
        return ''
    lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(targets[:8]())
    extra = f'''\n… and {len(targets) - 8} more''' if len(targets) > 8 else ''
    return f'''**Tests that will run after apply:**\n{lines}{extra}'''

