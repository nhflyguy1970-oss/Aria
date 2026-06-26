# Source Generated with Decompyle++
# File: brain_routing.cpython-312.pyc (Python 3.12)

'''Fast vs deep chat model selection (thinking / nonthinking).'''
from __future__ import annotations
import os
import re
from jarvis.p1_flags import brain_routing_enabled
_DEEP_RE = re.compile('\\b(why|explain|analyze|debug|fix|implement|refactor|prove|calculate|math|code|algorithm|optimize|design|architect|compare|trade-?off|step by step)\\b', re.I)

def needs_deep_thinking(message = None, *, action):
    if not brain_routing_enabled():
        return False
    if action != 'chat':
        return False
    if not message:
        message
    text = ''.strip()
    if len(text) > 400:
        return True
    if _DEEP_RE.search(text):
        return True
    if text.count('?') >= 2:
        return True
    return False


def fast_chat_model():
    if not os.getenv('JARVIS_FAST_MODEL'):
        os.getenv('JARVIS_FAST_MODEL')
    if not ''.strip():
        ''.strip()
    return _fallback_fast()


def reasoning_model():
    if not os.getenv('JARVIS_REASONING_MODEL'):
        os.getenv('JARVIS_REASONING_MODEL')
    if not ''.strip():
        ''.strip()
    return _fallback_reasoning()


def _fallback_fast():
    model_available = model_available
    import jarvis.ollama_health
    llm = llm
    import jarvis
    for name in ('qwen3:1.7b', 'qwen2.5:3b', 'qwen2.5:7b'):
        if not model_available(name):
            continue
        
        return ('qwen3:1.7b', 'qwen2.5:3b', 'qwen2.5:7b'), name
    return llm.general_model()


def _fallback_reasoning():
    model_available = model_available
    import jarvis.ollama_health
    llm = llm
    import jarvis
    for name in ('deepseek-r1:7b', 'deepseek-r1:1.5b', 'qwen2.5:14b', 'qwen2.5:7b'):
        if not model_available(name):
            continue
        
        return ('deepseek-r1:7b', 'deepseek-r1:1.5b', 'qwen2.5:14b', 'qwen2.5:7b'), name
    return llm.review_model()


def select_chat_model(message = None, params = None, *, action, voice, session_chat_model):
    llm = llm
    import jarvis
    if not params:
        params
    params = { }
    if not params.get('model'):
        params.get('model')
        if not session_chat_model:
            session_chat_model
    explicit = ''.strip()
    if explicit:
        return explicit
    if not None.get('thinking_mode'):
        None.get('thinking_mode')
    mode = ''.strip().lower()
    if mode == 'deep' or needs_deep_thinking(message, action = action):
        return reasoning_model()
    if None == 'fast' or voice:
        return fast_chat_model()
    return None.general_model()

