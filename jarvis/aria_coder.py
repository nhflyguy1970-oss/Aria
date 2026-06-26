# Source Generated with Decompyle++
# File: aria_coder.cpython-312.pyc (Python 3.12)

'''ARIA coder utilities — filesystem tools, tests, and self-fix/self-upgrade bridges.'''
from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable
from jarvis import fs
from jarvis.config import PROJECT_ROOT
SMOKE_TEST_TARGETS = tuple(os.getenv('JARVIS_DIAGNOSE_TESTS', 'tests/test_coding.py tests/test_aria_coder.py tests/test_cursor_bridge.py tests/test_coding_jobs.py tests/test_coding_jobs_cancel.py').split())
_SELF_FIX_TRIGGER = re.compile('^(?:please\\s+)?(?:(?:self[- ]?)?fix|heal|repair|diagnose and fix)\\s+aria(?:\\s+(?:and\\s+)?apply)?[.!]?\\s*', re.I)

def list_dir(path = None, base = None, *, limit):
    return fs.list_dir(path, base = base, limit = limit)


def write_file_bridge(path = None, content = None, base = None, *, backup):
    
    try:
        resolved = fs.resolve_path(path, base = base)
        backup_path = ''
        if backup and resolved.is_file():
            backup_path = fs.backup_file(path, base = base)
        fs.write_file(path, content, base = base)
        return {
            'ok': True,
            'path': str(resolved),
            'bytes': len(content.encode('utf-8')),
            'backup': backup_path }
    except fs.PathError:
        e = None
        del e
        return None
        None = 
        del e
        except OSError:
            e = None
            del e
            return None
            None = 
            del e



def run_tests_bridge(target = None, base = None, *, timeout, extra_args):
    run_pytest = run_pytest
    import jarvis.project_runner
    if not extra_args:
        extra_args
    args = list([])
    for flag in ('-q', '--tb=short'):
        if not flag not in args:
            continue
        args.append(flag)
    if not target:
        target
    result = run_pytest('tests/', base, timeout = timeout, extra_args = args)
    if not result.stdout:
        result.stdout
    if not result.stderr:
        result.stderr
    stdout = ('' + '').strip()
    if not target:
        target
    return {
        'ok': result.returncode == 0,
        'returncode': result.returncode,
        'output': stdout[-8000:],
        'target': 'tests/' }


def normalize_self_fix_task(task = None):
    """Strip chat trigger phrases so 'fix aria' does not become the LLM task."""
    if not task:
        task
    text = ''.strip()
    text = _SELF_FIX_TRIGGER.sub('', text).strip()
    text = re.sub('^[:—\\-]\\s*', '', text).strip()
    if text.lower() in ('', 'fix aria', 'heal aria', 'repair aria'):
        return ''
    return text


def _run_pytest_targets(targets = None, base = None, *, timeout, extra_args):
