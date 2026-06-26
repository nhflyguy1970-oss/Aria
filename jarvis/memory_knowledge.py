# Source Generated with Decompyle++
# File: memory_knowledge.cpython-312.pyc (Python 3.12)

'''Environment and machine facts synced into long-term memory.'''
from __future__ import annotations
import logging
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any
from jarvis.config import DATA_DIR
logger = logging.getLogger('jarvis.memory_knowledge')
ENV_NAMESPACE = 'environment'
TAG_ENV = 'environment-fact'
TAG_ENV_KEY = 'env-key:'
TAG_USER_PREFERENCE = 'user-preference'
TAG_MACHINE = 'machine-fact'
ENVIRONMENT_PREFERENCE_DEFS: 'tuple[dict[str, Any], ...]' = ({
    'key': 'pref-linux-commands',
    'label': 'Linux / shell commands',
    'hint': 'How ARIA should format shell examples and CLI help.',
    'default': 'User prefers Linux shell commands (bash, coreutils) over PowerShell or Windows-style syntax.',
    'type': 'preference',
    'tags': [
        'workflow'] }, {
    'key': 'pref-ollama-local',
    'label': 'Local Ollama',
    'hint': 'Assume on-machine models via Ollama when suggesting inference.',
    'default': 'User uses Ollama for local LLM inference and prefers on-machine models.',
    'type': 'preference',
    'tags': [
        'ollama',
        'workflow'] }, {
    'key': 'pref-privacy-local',
    'label': 'Privacy / local-first',
    'hint': 'Bias toward private, on-device workflows over cloud APIs.',
    'default': 'User dislikes cloud dependence and prefers local, private, on-device AI when possible.',
    'type': 'preference',
    'tags': [
        'privacy'] })

def _env_key(key = None):
    return f'''{TAG_ENV_KEY}{key}'''


def preference_defs():
    pass
# WARNING: Decompyle incomplete


def load_environment_preferences():
    '''User-editable stack preferences (chat_settings); seeds defaults once.'''
    _load_chat_settings = _load_chat_settings
    _write_chat_settings = _write_chat_settings
    import jarvis.config
    data = _load_chat_settings()
    raw = data.get('environment_preferences')
    prefs = dict(raw) if isinstance(raw, dict) else { }
    changed = False
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec['key']
        if not key not in prefs:
            continue
        prefs[key] = spec['default']
        changed = True
    if changed:
        data['environment_preferences'] = prefs
        _write_chat_settings(data)
    return prefs


def save_environment_preferences(prefs = None):
    _load_chat_settings = _load_chat_settings
    _write_chat_settings = _write_chat_settings
    import jarvis.config
# WARNING: Decompyle incomplete


def environment_preferences_payload():
    '''Catalog + current values for the Memory tab API.'''
    prefs = load_environment_preferences()
    items = []
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec['key']
        if not spec.get('tags'):
            spec.get('tags')
        items.append({
            'key': key,
            'label': spec['label'],
            'hint': spec.get('hint', ''),
            'type': spec.get('type', 'preference'),
            'tags': list([]),
            'default': spec['default'],
            'content': prefs.get(key, spec['default']) })
    return {
        'ok': True,
        'preferences': items }


def _docker_container_names():
    if not shutil.which('docker'):
        return []
# WARNING: Decompyle incomplete


def _system_ram_gb():
    
    try:
        f = open('/proc/meminfo', encoding = 'utf-8')
        for line in f:
            if not line.startswith('MemTotal:'):
                continue
            kb = int(line.split()[1])
            
            
            try:
                None(None, None)
                return 
                
                try:
                    None(None, None)
                    
                    try:
                        return round(psutil.virtual_memory().total / 1073741824, 1)
                        with None:
                            if not import psutil:
                                pass
                        
                        try:
                            continue
                        except (OSError, ValueError):
                            continue
                            except Exception:
                                return None







def _cpu_model():
    
    try:
        f = open('/proc/cpuinfo', encoding = 'utf-8')
        for line in f:
            if not line.lower().startswith('model name'):
                continue
            
            
            try:
                None(None, None)
                return 
                
                try:
                    None(None, None)
                    if not platform.processor():
                        platform.processor()
                    return None
                    with None:
                        if not None:
                            pass
                    
                    try:
                        continue
                    except OSError:
                        continue






def collect_machine_facts():
    '''Auto-detected machine/stack facts (overwritten on sync).'''
    pass
# WARNING: Decompyle incomplete


def collect_preference_facts():
    '''User-edited preferences from chat_settings.'''
    prefs = load_environment_preferences()
    facts = []
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec['key']
        if not prefs.get(key):
            prefs.get(key)
        content = ''.strip()
        if not content:
            continue
        if not spec.get('tags'):
            spec.get('tags')
        None({
            'key': facts.append,
            'content': key,
            'type': content,
            'tags': spec.get('type', 'preference') })
    return facts


def collect_environment_facts():
    return collect_machine_facts() + collect_preference_facts()


def _find_env_entry(memory_store = None, key = None):
    if hasattr(memory_store, 'find_by_env_key'):
        return memory_store.find_by_env_key(key)
    tag = None(key)
    for e in memory_store.list_entries(namespace = ENV_NAMESPACE):
        if not e.get('tags'):
            e.get('tags')
        if not tag in []:
            continue
        
        return memory_store.list_entries(namespace = ENV_NAMESPACE), e


def _upsert_env_fact(memory_store = None, fact = None):
    """Return 'added', 'updated', or 'unchanged'."""
    key = fact['key']
    existing = _find_env_entry(memory_store, key)
    content = fact['content']
    if existing:
        if not existing.get('content'):
            existing.get('content')
        if ''.strip() == content:
            return 'unchanged'
        memory_store.update(existing['id'], content = content)
        return 'updated'
    memory_store.add(fact['type'], content, tags = fact['tags'], namespace = ENV_NAMESPACE)
    return 'added'


def _should_sync():
    interval_h = int(os.getenv('JARVIS_ENV_MEMORY_SYNC_HOURS', '24'))
    if interval_h <= 0:
        return False
    _load_chat_settings = _load_chat_settings
    import jarvis.config
    data = _load_chat_settings()
    if not data.get('environment_memory'):
        data.get('environment_memory')
    meta = { }
    last = meta.get('synced_at')
    if not last:
        return True
    
    try:
        prev = datetime.fromisoformat(str(last).replace('Z', '+00:00'))
        age_h = (datetime.now(timezone.utc) - prev).total_seconds() / 3600
        return age_h >= interval_h
    except (TypeError, ValueError):
        return True



def _mark_synced(count = None):
    _load_chat_settings = _load_chat_settings
    _write_chat_settings = _write_chat_settings
    import jarvis.config
    data = _load_chat_settings()
    data['environment_memory'] = {
        'synced_at': datetime.now(timezone.utc).isoformat(),
        'fact_count': count }
    _write_chat_settings(data)


def sync_environment_memory(memory_store = None, *, force, machine_only):
    '''Upsert machine facts (auto) and user preferences (from settings).'''
    if not force and _should_sync():
        return {
            'ok': True,
            'skipped': True,
            'reason': 'recent' }
    added = None
    updated = None
    for fact in collect_machine_facts():
        result = _upsert_env_fact(memory_store, fact)
        if result == 'added':
            added += 1
            continue
        if not result == 'updated':
            continue
        updated += 1
# WARNING: Decompyle incomplete


def save_environment_preferences_to_memory(memory_store = None, prefs = None):
    '''Persist preferences to settings and sync only preference rows to memory.'''
    merged = save_environment_preferences(prefs)
    added = 0
    updated = 0
    removed = 0
    active_keys = set()
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec['key']
        if not merged.get(key):
            merged.get(key)
        content = ''.strip()
        if not content:
            existing = _find_env_entry(memory_store, key)
            if existing and memory_store.delete_id(existing['id']):
                removed += 1
            continue
        active_keys.add(key)
        if not spec.get('tags'):
            spec.get('tags')
        fact = {
            'key': ENVIRONMENT_PREFERENCE_DEFS,
            'content': key,
            'type': content,
            'tags': spec.get('type', 'preference') }
        result = _upsert_env_fact(memory_store, fact)
        if result == 'added':
            added += 1
            continue
        if not result == 'updated':
            continue
        updated += 1
    return {
        'ok': True,
        'added': added,
        'updated': updated,
        'removed': removed,
        'preferences': merged }

