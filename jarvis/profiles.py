# Source Generated with Decompyle++
# File: profiles.cpython-312.pyc (Python 3.12)

'''Work / gaming / offline config profiles — snapshots of Jarvis settings.'''
from __future__ import annotations
from typing import Any
from jarvis.config import _load_chat_settings, _write_chat_settings, save_personality_preset, save_vision_quality
from jarvis.model_store import apply_preset
PROFILE_DEFS: 'dict[str, dict[str, Any]]' = {
    'work': {
        'label': 'Work',
        'description': '7B quality models (8GB-safe), professional tone, GPU images',
        'personality': 'professional',
        'model_preset': 'quality',
        'vision_quality': 'fast',
        'comfyui_mode': 'auto',
        'ollama_keep_alive': '15m' },
    'gaming': {
        'label': 'Gaming',
        'description': 'Fast models, short keep-alive to free VRAM',
        'personality': 'brief',
        'model_preset': 'fast',
        'vision_quality': 'fast',
        'comfyui_mode': 'cpu',
        'ollama_keep_alive': '5m' },
    'offline': {
        'label': 'Offline',
        'description': 'Local-only — no web search dependency',
        'personality': 'default',
        'model_preset': 'fast',
        'vision_quality': 'fast',
        'comfyui_mode': 'cpu',
        'ollama_keep_alive': '15m',
        'web_search_disabled': True },
    'uncensored': {
        'label': 'Uncensored',
        'description': 'Max uncensored models, GPU ComfyUI, NSFW checkpoints',
        'personality': 'default',
        'model_preset': 'quality',
        'vision_quality': 'quality',
        'comfyui_mode': 'gpu',
        'ollama_keep_alive': '30m',
        'enable_uncensored': True } }

def list_profiles():
    active = active_profile()
    out = []
    for key, spec in PROFILE_DEFS.items():
        out.append({
            'id': key,
            'label': spec['label'],
            'description': spec['description'],
            'active': key == active })
    return out


def active_profile():
    if not _load_chat_settings().get('active_profile'):
        _load_chat_settings().get('active_profile')
    return ''.strip()


def apply_profile(profile_id = None):
    pid = profile_id.strip().lower()
    if pid not in PROFILE_DEFS:
        raise ValueError(f'''Unknown profile: {profile_id}''')
    spec = PROFILE_DEFS[pid]
    save_personality_preset(spec['personality'])
    save_vision_quality(spec['vision_quality'])
    if spec.get('enable_uncensored'):
        set_uncensored = set_uncensored
        import jarvis.config
        apply_uncensored_profile_tune = apply_uncensored_profile_tune
        import jarvis.hardware_tune
        set_uncensored(True)
        apply_uncensored_profile_tune()
    else:
        apply_preset(spec['model_preset'])
        save_mode = save_mode
        import jarvis.comfyui_settings
        save_mode(spec.get('comfyui_mode', 'auto'))
    data = _load_chat_settings()
    data['active_profile'] = pid
    data['web_search_disabled'] = bool(spec.get('web_search_disabled', False))
    data['ollama_keep_alive_override'] = spec.get('ollama_keep_alive', '')
    _write_chat_settings(data)
    import os
    ka = spec.get('ollama_keep_alive', '')
    if ka:
        os.environ['OLLAMA_KEEP_ALIVE'] = ka
    return {
        'ok': True,
        'profile': pid,
        'label': spec['label'] }


def web_search_disabled():
    return bool(_load_chat_settings().get('web_search_disabled', False))

