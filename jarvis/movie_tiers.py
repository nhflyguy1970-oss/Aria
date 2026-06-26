# Source Generated with Decompyle++
# File: movie_tiers.cpython-312.pyc (Python 3.12)

'''Movie Jarvis tier helpers — trust health, task nudge, export, ICS, profile hints.'''
from __future__ import annotations
import os
import re
import time
from datetime import datetime
from typing import Any
from jarvis.config import DATA_DIR

def trust_health():
    TRUST_MEMORY_TYPES = TRUST_MEMORY_TYPES
    is_test_artifact = is_test_artifact
    import jarvis.trust_memory
    disk_gb = 0
    
    try:
        import shutil
        disk_gb = round(shutil.disk_usage(str(DATA_DIR)).free / 1073741824, 1)
        last_scrub = ''
        scrub_file = DATA_DIR / 'memory_scrub.json'
        if scrub_file.is_file():
            
            try:
                import json
                last_scrub = json.loads(scrub_file.read_text()).get('last_run', '')[:19]
                strategy_count = 0
                failure_count = 0
                
                try:
                    MemoryStore = MemoryStore
                    import jarvis.memory_store
                    store = MemoryStore()
                    strategy_count = len(store.list_entries(entry_type = 'strategy'))
                    failure_count = len(store.list_entries(entry_type = 'failure'))
                    if not last_scrub:
                        last_scrub
                    return {
                        'disk_free_gb': disk_gb,
                        'last_scrub': 'never',
                        'test_filter': 'active',
                        'test_sample_blocked': is_test_artifact('pytest journal scratch buy milk'),
                        'strategy_entries': strategy_count,
                        'failure_entries': failure_count,
                        'trust_types': list(TRUST_MEMORY_TYPES) }
                    except OSError:
                        continue
                    except Exception:
                        continue
                except Exception:
                    continue





def profile_banner(profile = None):
    active_profile_name = active_profile_name
    import jarvis.environment
    if not profile:
        profile
        if not active_profile_name():
            active_profile_name()
    name = 'default'.lower()
    offline = name in ('offline', 'gaming')
    if not offline:
        offline
    web_off = os.getenv('JARVIS_WEB_SEARCH', '1') == '0'
    if not offline:
        offline
    return {
        'profile': name,
        'show': web_off,
        'message': f'''Profile **{name}** — web search {'off' if web_off else 'on'}''',
        'web_search_off': web_off }


def task_nudge_check(*, hour, threshold):
    '''Return whether to nudge user about open journal tasks.'''
    if os.getenv('JARVIS_TASK_NUDGE', '1') != '1':
        return {
            'nudge': False,
            'reason': 'disabled' }
    now = None.now()
# WARNING: Decompyle incomplete


def mark_task_nudge_shown():
    import json
    state_file = DATA_DIR / 'task_nudge_state.json'
    state_file.write_text(json.dumps({
        'date': datetime.now().date().isoformat(),
        'ts': time.time() }), encoding = 'utf-8')


def validate_ics_url(url = None):
    if not url:
        url
    u = ''.strip()
    if not u:
        return {
            'ok': False,
            'message': 'URL required' }
    if not None.startswith('http'):
        return {
            'ok': False,
            'message': 'URL must start with http(s)' }
# WARNING: Decompyle incomplete


def save_ics_url(url = None):
    load_jarvis_env = load_jarvis_env
    upsert_env_vars = upsert_env_vars
    import jarvis.env_loader
    if not url:
        url
    u = ''.strip()
    check = validate_ics_url(u) if u else {
        'ok': True,
        'message': 'cleared' }
    if not u and check.get('ok'):
        return check
    load_jarvis_env()
    upsert_env_vars({
        'JARVIS_ICS_URL': u })
# WARNING: Decompyle incomplete


def export_chat_with_memory(messages = None, *, branch_name, memory_hits):
    lines = [
        f'''# Jarvis Chat — {branch_name}\n''']
    if memory_hits:
        lines.append('## Memories referenced\n')
        for h in memory_hits[:12]:
            if not h.get('date'):
                h.get('date')
            lines.append(f'''- **{h.get('type', 'fact')}** ({''[:10]}): {h.get('content', '')[:200]}''')
        lines.append('')
    for m in messages:
        role = m.get('role', '?')
        if role == 'system':
            continue
        content = m.get('content', '')
        lines.append(f'''## {role.capitalize()}\n\n{content}\n''')
    return '\n'.join(lines)


def memory_citations_from_context(context_block = None):
    '''Parse injected memory lines into citation objects.'''
    cites = []
    if not context_block:
        context_block
    for line in ''.splitlines():
        line = line.strip()
        if not line.startswith('- '):
            continue
        m = re.match('-\\s*\\*\\*(\\w+)\\*\\*\\s*(?:\\(([^)]+)\\))?\\s*:\\s*(.+)', line)
        if not m:
            continue
        if not m.group(2):
            m.group(2)
        cites.append({
            'type': m.group(1),
            'date': '',
            'content': m.group(3).strip() })
    return cites[:8]


def service_restart(name = None):
    if not name:
        name
    svc = ''.strip().lower()
    if svc == 'jarvis':
        request_restart = request_restart
        import jarvis.server_restart
        return request_restart()
    if None == 'ollama':
        ensure_ollama = ensure_ollama
        import jarvis.services
        ok = ensure_ollama(timeout = 45)
        if ok:
            return {
                'ok': ok,
                'service': svc,
                'message': 'Ollama restarted' }
        return {
            'ok': None,
            'service': ok,
            'message': svc }
    if None == 'comfyui':
        ensure_comfyui = ensure_comfyui
        import jarvis.services
        ok = ensure_comfyui(block = True, timeout = 120, on_demand = True)
        if ok:
            return {
                'ok': ok,
                'service': svc,
                'message': 'ComfyUI restarted' }
        return {
            'ok': None,
            'service': ok,
            'message': svc }
    if None in ('homeassistant', 'ha'):
        ensure_homeassistant = ensure_homeassistant
        import jarvis.ha_docker
        ok = ensure_homeassistant(block = True, timeout = 90, on_demand = True)
        if ok:
            return {
                'ok': ok,
                'service': 'homeassistant',
                'message': 'Home Assistant restarted' }
        return {
            'ok': None,
            'service': ok,
            'message': 'homeassistant' }
    return {
        'ok': None,
        'message': f'''Unknown service: {name}''' }


def last_good_media_settings():
    suggested_for_action = suggested_for_action
    import jarvis.resource_router
    return {
        'image': suggested_for_action('generate_image'),
        'video': suggested_for_action('generate_video'),
        'meme': suggested_for_action('generate_meme') }

