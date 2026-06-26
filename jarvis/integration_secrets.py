# Source Generated with Decompyle++
# File: integration_secrets.cpython-312.pyc (Python 3.12)

'''Integration API keys — saved from the GUI into data/jarvis.env (same as HA token).'''
from __future__ import annotations
import os
import re
from typing import Any
_SECRET_FIELDS: 'dict[str, str]' = {
    'gemini_api_key': 'GEMINI_API_KEY',
    'google_api_key': 'GOOGLE_API_KEY',
    'openai_api_key': 'OPENAI_API_KEY',
    'hf_token': 'HF_TOKEN',
    'meshy_api_key': 'JARVIS_MESHY_API_KEY' }

def _mask(value = None):
    if not value:
        value
    v = ''.strip()
    if not v:
        return ''
    if len(v) <= 8:
        return '••••'
    return f'''{v[:4]}…{v[-4:]}'''


def _env_value(name = None):
    if not os.getenv(name):
        os.getenv(name)
    return ''.strip()


def secrets_status():
    '''Which integration keys are set (masked previews only).'''
    if not _env_value('GEMINI_API_KEY'):
        _env_value('GEMINI_API_KEY')
    gemini = _env_value('GOOGLE_API_KEY')
    openai = _env_value('OPENAI_API_KEY')
    if not _env_value('HF_TOKEN'):
        _env_value('HF_TOKEN')
    hf = _env_value('HUGGING_FACE_HUB_TOKEN')
    meshy = _env_value('JARVIS_MESHY_API_KEY')
    return {
        'gemini_api_key_set': bool(gemini),
        'gemini_api_key_preview': _mask(gemini),
        'openai_api_key_set': bool(openai),
        'openai_api_key_preview': _mask(openai),
        'hf_token_set': bool(hf),
        'hf_token_preview': _mask(hf),
        'meshy_api_key_set': bool(meshy),
        'meshy_api_key_preview': _mask(meshy),
        'storage': 'data/jarvis.env',
        'hint': 'Keys are saved on this PC only (not synced to git). Restart not required.' }


def save_secrets(patch = None):
    '''Persist non-empty keys from the settings UI.'''
    load_jarvis_env = load_jarvis_env
    upsert_env_vars = upsert_env_vars
    import jarvis.env_loader
    updates = { }
# WARNING: Decompyle incomplete


def clear_secret(field = None):
    '''Remove a key from jarvis.env (empty string in UI).'''
    env_name = _SECRET_FIELDS.get(field)
    if not env_name:
        return {
            'ok': False,
            'message': f'''Unknown field: {field}''' }
    ENV_FILE = ENV_FILE
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
# WARNING: Decompyle incomplete

