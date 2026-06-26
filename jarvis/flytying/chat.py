# Source Generated with Decompyle++
# File: chat.cpython-312.pyc (Python 3.12)

'''Dedicated fly-tying chat — RAG-backed, separate from main ARIA chat.'''
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any, Iterator
from jarvis.config import DATA_DIR
SETTINGS_FILE = DATA_DIR / 'flytying_settings.json'
_CREATIVE_RE = re.compile('\\b(design|create a new|invent|custom pattern|new fly|original pattern|from scratch|dream up|come up with)\\b', re.I)
_SYSTEM_BASE = "You are ARIA's fly-tying expert — a patient, precise instructor for trout and warm-water patterns.\n\nUse the REFERENCE RECIPES below when they are relevant. Prefer cited patterns from the library over invention.\nWhen designing a new fly, say clearly that it is a custom design, list materials and numbered steps, and note hatch/water context.\nWhen suggesting from the user's materials list, rank practical patterns and explain why each fits.\n\nRules:\n- Give hook size, thread, and materials in tying order when teaching a pattern.\n- Number tying steps clearly.\n- Mention variations only when useful.\n- If the library lacks a match, say so and offer your best custom recipe.\n- Keep answers focused; avoid filler."

def _settings():
    if not SETTINGS_FILE.is_file():
        return { }
    
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            return data
        return None
    except (OSError, json.JSONDecodeError):
        return 



def _save_settings(data = None):
    SETTINGS_FILE.parent.mkdir(parents = True, exist_ok = True)
    SETTINGS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def flytying_model(message = None, *, override):
    '''Best local model for fly tying: 7b for recipes, 14b when designing.'''
    if not override:
        override
    if ''.strip():
        return override.strip()
    if not None().get('model'):
        None().get('model')
    saved = ''.strip()
    if saved:
        return saved
    if not None.environ.get('JARVIS_FLYTYING_MODEL'):
        None.environ.get('JARVIS_FLYTYING_MODEL')
    env = ''.strip()
    if env:
        return env
    model_available = model_available
    import jarvis.ollama_health
    llm = llm
    import jarvis
    if not message:
        message
    creative = bool(_CREATIVE_RE.search(''))
    if creative:
        for name in ('qwen2.5:14b', 'qwen2.5:7b', 'qwen2.5:3b'):
            if not model_available(name):
                continue
            
            return ('qwen2.5:14b', 'qwen2.5:7b', 'qwen2.5:3b'), name
    for None in ('qwen2.5:7b', 'qwen2.5:14b', 'qwen2.5:3b'):
        if not model_available(name):
            continue
        return None, name
    return llm.general_model()


def get_model_setting():
    if not _settings().get('model'):
        _settings().get('model')
    if not os.environ.get('JARVIS_FLYTYING_MODEL'):
        os.environ.get('JARVIS_FLYTYING_MODEL')
    return {
        'model': flytying_model(),
        'saved': ''.strip(),
        'env_default': ''.strip(),
        'recommended': 'qwen2.5:7b',
        'recommended_design': 'qwen2.5:14b' }


def set_model_setting(model = None):
    if not model:
        model
    model = ''.strip()
    data = _settings()
    if model:
        data['model'] = model
    else:
        data.pop('model', None)
    _save_settings(data)
    return get_model_setting()


def _format_context(recipes = None):
    if not recipes:
        return 'REFERENCE RECIPES: (none retrieved — answer from general fly-tying knowledge and note the gap.)'
    blocks = []
    for i, r in enumerate(recipes, 1):
        if not r.get('name'):
            r.get('name')
            if not r.get('fly_name'):
                r.get('fly_name')
        name = 'Unknown'
        if not r.get('type'):
            r.get('type')
        lines = [
            f'''### {i}. {name} ({'?'})''']
        if r.get('hook'):
            lines.append(f'''Hook: {r['hook']}''')
        if not r.get('materials'):
            r.get('materials')
        mats = []
        if mats:
            None('; '.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(mats[:20]()))
        if not r.get('steps'):
            r.get('steps')
        steps = []
        if steps:
            None(' | '.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(steps[:12]()))
        if r.get('source_url'):
            lines.append(f'''Source: {r['source_url']}''')
        blocks.append('\n'.join(lines))
    return 'REFERENCE RECIPES:\n\n' + '\n\n'.join(blocks)


def _prepare_turn(messages = None, *, fly_type, model):
    if not messages:
        return {
            'ok': False,
            'message': 'messages required',
            'hits': [],
            'llm_messages': [] }
    last_user = None
    for m in reversed(messages):
        if not m.get('role'):
            m.get('role')
        if not ''.lower() == 'user':
            continue
        if not m.get('content'):
            m.get('content')
        last_user = ''.strip()
        reversed(messages)
    if not last_user:
        return {
            'ok': False,
            'message': 'no user message',
            'hits': [],
            'llm_messages': [] }
    bridge = bridge
    import jarvis.flytying
    hatch_context_text = hatch_context_text
    import jarvis.flytying.hatch
    if not bridge.gold_available():
        return {
            'ok': False,
            'message': 'Gold recipe library missing',
            'hits': [],
            'llm_messages': [] }
    hits = None.search_recipes(last_user, fly_type = fly_type, limit = 5)
    full_recipes = []
    for h in hits:
        if not h.get('name'):
            h.get('name')
            if not h.get('recipe_id'):
                h.get('recipe_id')
        detail = bridge.get_recipe('')
        if detail and detail.get('recipe'):
            full_recipes.append(detail['recipe'])
            continue
        if not detail:
            continue
        full_recipes.append(detail)
    context = _format_context(full_recipes)
    hatch = hatch_context_text()
    model_name = flytying_model(last_user, override = model)
    system = f'''{_SYSTEM_BASE}\n\n{hatch}\n\n{context}'''
    llm_messages = [
        {
            'role': 'system',
            'content': system }]
    for m in messages[-12:]:
        if not m.get('role'):
            m.get('role')
        role = 'user'.lower()
        if role not in ('user', 'assistant'):
            continue
        if not m.get('content'):
            m.get('content')
        content = ''.strip()
        if not content:
            continue
        llm_messages.append({
            'role': role,
            'content': content })
    return {
        'ok': True,
        'message': 'ok',
        'hits': hits,
        'model': model_name,
        'llm_messages': llm_messages,
        'last_user': last_user }


def chat_turn(messages = None, *, fly_type, model):
    '''Multi-turn fly-tying chat with RAG context from gold recipes.'''
    ctx = _prepare_turn(messages, fly_type = fly_type, model = model)
    if not ctx.get('ok'):
        if not ctx.get('message'):
            ctx.get('message')
        if not ctx.get('hits'):
            ctx.get('hits')
        return {
            'ok': False,
            'message': 'error',
            'answer': '',
            'recipes': [] }
    llm = llm
    import jarvis
    model_name = ctx['model']
    
    try:
        answer = llm.ask(model_name, ctx['llm_messages'], temperature = 0.25)
        if not answer:
            answer
        return {
            'ok': True,
            'message': 'ok',
            'answer': ''.strip(),
            'model': model_name,
            'recipes': ctx['hits'] }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def chat_turn_stream(messages = None, *, fly_type, model):
    '''Stream tokens for fly-tying chat (SSE-friendly event dicts).'''
    pass
# WARNING: Decompyle incomplete

