# Source Generated with Decompyle++
# File: local_router.cpython-312.pyc (Python 3.12)

'''Fast local intent router via small Ollama model (FunctionGemma-style JSON).'''
from __future__ import annotations
import json
import logging
import os
import re
import time
from typing import Any
from jarvis.p1_flags import local_router_enabled
from jarvis.session import SessionContext
log = logging.getLogger('jarvis.router')
_CACHE: 'dict[str, tuple[float, dict[str, Any]]]' = { }
_CACHE_TTL = 120
_ROUTER_ACTIONS = ('system_info', 'morning_briefing', 'planner_add_task', 'planner_set_timer', 'planner_set_alarm', 'planner_today', 'curated_briefing', 'audio_stop', 'audio_pause', 'ha_control', 'ha_status', 'web_search', 'weather_forecast', 'generate_cad', 'iterate_cad', 'chat', 'thinking', 'nonthinking')

def router_model():
    if not os.getenv('JARVIS_ROUTER_MODEL'):
        os.getenv('JARVIS_ROUTER_MODEL')
    return 'qwen3:1.7b'.strip()


def _system_prompt():
    actions = ', '.join(_ROUTER_ACTIONS)
    return f'''You are a fast intent router. Reply with ONLY one JSON object, no markdown.\nKeys: "action" (one of: {actions}), "params" (object), "thinking" (short string).\nUse thinking for math/coding/debug/reasoning; nonthinking for greetings/simple facts.\nMap timers/alarms/tasks/planner/status/weather/HA/web/CAD to the matching action.\nUse generate_cad for new parts; iterate_cad to modify the current design.\nIf unsure, use {{"action":"chat","params":{{}},"thinking":"chat"}}.'''


def _parse_json(raw = None):
    if not raw:
        raw
    text = ''.strip()
    if text.startswith('```'):
        text = re.sub('^```\\w*\\n?', '', text)
        text = re.sub('\\n?```$', '', text)
    start = text.find('{')
    end = text.rfind('}') + 1
    if start < 0 or end <= start:
        return None
    
    try:
        data = json.loads(text[start:end])
        if isinstance(data, dict) or 'action' not in data:
            return None
        data.setdefault('params', { })
        data.setdefault('thinking', data.get('action', 'routed'))
        return data
    except json.JSONDecodeError:
        return None



def try_local_route(message = None, session = None):
    '''Return intent dict or None to fall through to full router.'''
    if not local_router_enabled():
        return None
    try_hint_route = try_hint_route
    import jarvis.router_hints
    hint = try_hint_route(message)
    if hint:
        return hint
    if not None.getenv('JARVIS_ROUTER_BACKEND'):
        None.getenv('JARVIS_ROUTER_BACKEND')
    backend = 'auto'.strip().lower()
    if backend in ('auto', 'functiongemma'):
        try_functiongemma_route = try_functiongemma_route
        import jarvis.functiongemma_router
        hit = try_functiongemma_route(message, session)
        if hit:
            return hit
        if None == 'functiongemma':
            return None
    return _try_ollama_route(message, session)


def _try_ollama_route(message = None, session = None):
    if not message:
        message
    text = ''.strip()
    if text and len(text) > 280 or text.count('\n') > 2:
        return None
    cache_key = text.lower()
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return dict(cached[1])
    
    try:
        llm = llm
        import jarvis
        t0 = time.perf_counter()
        raw = llm.ask_with_system(router_model(), _system_prompt(), text, options = {
            'temperature': 0,
            'num_predict': 120 })
        ms = int((time.perf_counter() - t0) * 1000)
        parsed = _parse_json(raw)
        if not parsed:
            return None
            
            try:
                if not parsed.get('action'):
                    parsed.get('action')
                action = str('chat')
                if action == 'thinking':
                    parsed = {
                        'action': 'chat',
                        'params': {
                            'thinking_mode': 'deep' },
                        'thinking': 'deep chat' }
                elif action == 'nonthinking':
                    parsed = {
                        'action': 'chat',
                        'params': {
                            'thinking_mode': 'fast' },
                        'thinking': 'fast chat' }
                elif action == 'iterate_cad':
                    params = parsed.setdefault('params', { })
                    params.setdefault('edit', True)
                elif action not in _ROUTER_ACTIONS and action != 'chat':
                    has_action = has_action
                    import jarvis.handlers.registry
                    if not has_action(action):
                        return None
                        
                        try:
                            if getattr(session, 'voice_mode', False):
                                needs_deep_thinking = needs_deep_thinking
                                import jarvis.brain_routing
                                params = parsed.setdefault('params', { })
                                if not params.get('thinking_mode') != 'deep' and needs_deep_thinking(text):
                                    params['thinking_mode'] = 'fast'
                                    params['voice'] = True
                                    if not parsed.get('thinking'):
                                        parsed.get('thinking')
                                    parsed['thinking'] = 'voice fast'
                            parsed['router_ms'] = ms
                            parsed['router'] = 'local'
                            _CACHE[cache_key] = (time.time(), parsed)
                            return parsed
                        except Exception:
                            exc = None
                            log.debug('local router skipped: %s', exc)
                            exc = None
                            del exc
                            return None
                            exc = None
                            del exc





def router_status():
    fg_status = router_status
    import jarvis.functiongemma_router
    if not os.getenv('JARVIS_ROUTER_BACKEND'):
        os.getenv('JARVIS_ROUTER_BACKEND')
    return {
        'enabled': local_router_enabled(),
        'backend': 'auto'.strip().lower(),
        'model': router_model(),
        'cache_entries': len(_CACHE),
        'functiongemma': fg_status() }

