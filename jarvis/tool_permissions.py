# Source Generated with Decompyle++
# File: tool_permissions.cpython-312.pyc (Python 3.12)

'''Per-tool confirmation settings (always | ask | never).'''
from __future__ import annotations
import json
import uuid
from typing import Any, Literal
from jarvis.config import DATA_DIR
from jarvis.feature_flags import tool_permissions_enabled
Permission = Literal[('always', 'ask', 'never')]
PERM_FILE = DATA_DIR / 'tool_permissions.json'
PENDING_FILE = DATA_DIR / 'pending_tool_confirms.json'
DEFAULTS: 'dict[str, Permission]' = {
    'write_file': 'ask',
    'shell': 'ask',
    'web_agent': 'ask',
    'cad': 'ask',
    'ha_control': 'never',
    'upgrade_apply': 'ask' }

def _load_raw():
    if not PERM_FILE.exists():
        return { }
    
    try:
        return json.loads(PERM_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save_raw(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    PERM_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def get_permissions():
    raw = _load_raw()
    out = dict(DEFAULTS)
    if not raw.get('tools'):
        raw.get('tools')
    tools = { }
    for key, val in tools.items():
        if not val in ('always', 'ask', 'never'):
            continue
        out[key] = val
    return out


def set_permission(tool = None, mode = None):
    if not tool:
        tool
    tool = ''.strip()
    if not mode:
        mode
    mode = ''.strip().lower()
    if mode not in ('always', 'ask', 'never'):
        raise ValueError('mode must be always, ask, or never')
    raw = _load_raw()
    if not raw.get('tools'):
        raw.get('tools')
    tools = dict({ })
    tools[tool] = mode
    raw['tools'] = tools
    _save_raw(raw)
    return get_permissions()


def permission_for(tool = None):
    if not tool_permissions_enabled():
        return 'always'
    return get_permissions().get(tool, DEFAULTS.get(tool, 'ask'))


def needs_confirmation(tool = None):
    return permission_for(tool) == 'ask'


def _load_pending():
    if not PENDING_FILE.exists():
        return { }
    
    try:
        return json.loads(PENDING_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save_pending(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    PENDING_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def create_pending(tool = None, action = None, params = None, message = ('tool', 'str', 'action', 'str', 'params', 'dict', 'message', 'str', 'return', 'str')):
    confirm_id = uuid.uuid4().hex[:12]
    pending = _load_pending()
    pending[confirm_id] = {
        'tool': tool,
        'action': action,
        'params': params,
        'message': message[:500] }
    _save_pending(pending)
    return confirm_id


def pop_pending(confirm_id = None):
    pending = _load_pending()
    row = pending.pop(confirm_id, None)
    _save_pending(pending)
    return row


def list_pending():
    pass
# WARNING: Decompyle incomplete

