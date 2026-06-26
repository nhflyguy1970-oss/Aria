# Source Generated with Decompyle++
# File: workflow_learning.cpython-312.pyc (Python 3.12)

'''Workflow learning — detect and store repeated action sequences.'''
from __future__ import annotations
import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
log = logging.getLogger('jarvis.workflow_learning')
WORKFLOWS_DIR = DATA_DIR / 'workflows'
INDEX_FILE = WORKFLOWS_DIR / 'index.json'
WATCH_FILE = WORKFLOWS_DIR / '_watch_state.json'
WORKFLOW_TAG = 'workflow-learn'
WORKFLOW_NAMESPACE = 'workflows'
IGNORE_ACTIONS = frozenset({
    'chat',
    'clear',
    'recall',
    'greeting',
    'skill_list',
    'models_info',
    'capabilities',
    'teach_recall',
    'memory_search',
    'workflow_list',
    'workflow_scan',
    'workflow_show',
    'workflow_learn',
    'morning_briefing',
    'correction_recall',
    'observation_recall',
    'journal_learn_recall',
    'document_learn_recall',
    'knowledge_research_list'})
_MIN_REPEATS_DEFAULT = 3
_MAX_SEQ_LEN_DEFAULT = 5
_GAP_SECONDS_DEFAULT = 1800

def min_repeats():
    
    try:
        return int(os.getenv('JARVIS_WORKFLOW_MIN_REPEATS', str(_MIN_REPEATS_DEFAULT)))
    except ValueError:
        return 



def max_seq_len():
    
    try:
        return int(os.getenv('JARVIS_WORKFLOW_MAX_STEPS', str(_MAX_SEQ_LEN_DEFAULT)))
    except ValueError:
        return 



def gap_seconds():
    
    try:
        return int(os.getenv('JARVIS_WORKFLOW_GAP_SEC', str(_GAP_SECONDS_DEFAULT)))
    except ValueError:
        return 



def _utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def slugify(text = None):
    if not text:
        text
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:72]:
        s[:72]
    return 'workflow'


def workflow_enabled():
    return os.getenv('JARVIS_WORKFLOW_LEARN', '1').lower() not in ('0', 'false', 'off', 'no')


def auto_watch():
    mode = os.getenv('JARVIS_AUTO_WORKFLOW_LEARN', 'smart').lower()
    if mode in ('0', 'false', 'off', 'no'):
        return False
    return mode in ('1', 'true', 'yes', 'smart')


def auto_remember():
    auto_workflow_remember_enabled = auto_workflow_remember_enabled
    import jarvis.brain_memory
    return auto_workflow_remember_enabled()


def _ensure_dir():
    WORKFLOWS_DIR.mkdir(parents = True, exist_ok = True)


def _load_index():
    if not INDEX_FILE.is_file():
        return {
            'workflows': { } }
    
    try:
        data = json.loads(INDEX_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('workflows', { })
            return data
        return {
            'workflows': { } }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt workflow index: %s', exc)
        exc = None
        del exc
        return {
            'workflows': { } }
        exc = None
        del exc



def _save_index(data = None):
    _ensure_dir()
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(INDEX_FILE)
    INDEX_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _workflow_path(slug = None):
    return WORKFLOWS_DIR / f'''{slugify(slug)}.json'''


def _load_watch():
    if not WATCH_FILE.is_file():
        return {
            'recent': [],
            'patterns': { } }
    
    try:
        data = json.loads(WATCH_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('recent', [])
            data.setdefault('patterns', { })
            return data
        return {
            'recent': [],
            'patterns': { } }
    except (json.JSONDecodeError, OSError):
        continue



def _save_watch(data = None):
    _ensure_dir()
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(WATCH_FILE)
    WATCH_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _normalize_detail(action = None, detail = None):
