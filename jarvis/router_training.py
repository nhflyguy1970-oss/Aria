# Source Generated with Decompyle++
# File: router_training.cpython-312.pyc (Python 3.12)

'''Export router training JSONL from registered actions.'''
from __future__ import annotations
import json
import logging
import os
import subprocess
from pathlib import Path
from jarvis.config import DATA_DIR
log = logging.getLogger('jarvis.router_training')
OUT = DATA_DIR / 'router_training.jsonl'
FG_OUT = DATA_DIR / 'functiongemma_training.jsonl'
MODELFILE = DATA_DIR / 'router.Modelfile'

def export_training_jsonl():
    ensure_handlers_loaded = ensure_handlers_loaded
    import jarvis.handlers
    all_actions = all_actions
    import jarvis.handlers.registry
    ensure_handlers_loaded()
    OUT.parent.mkdir(parents = True, exist_ok = True)
    lines = []
    for row in all_actions():
        if not row.get('action'):
            row.get('action')
        name = ''
        if not row.get('info') or row.get('registered'):
            continue
        if not row.get('description'):
            row.get('description')
        user = f'''Please {name.replace('_', ' ').strip()}'''
        if not row.get('module'):
            row.get('module')
        assistant = json.dumps({
            'action': name,
            'params': { },
            'thinking': 'tool' })
        row = {
            'messages': [
                {
                    'role': 'user',
                    'content': user },
                {
                    'role': 'assistant',
                    'content': assistant }] }
        lines.append(json.dumps(row, ensure_ascii = False))
    OUT.write_text('\n'.join(lines) + '\n' if lines else '', encoding = 'utf-8')
    return OUT


def _functiongemma_training_samples():
    '''Core router actions → (user utterance, call body) for fine-tune.'''
    pass
# WARNING: Decompyle incomplete


def _functiongemma_example(action = None, description = None):
    '''Return (user utterance, function_call target) for a single training row.'''
    samples = _functiongemma_training_samples()
    if action in samples:
        return samples[action][0]
    if not None:
        pass
    desc = action.replace('_', ' ').strip()
    return (f'''please {desc}''', f'''call:{action}{{}}''')

_ADA_SKIP_ACTIONS = frozenset({
    'create_calendar_event'})

def _ada_training_paths():
    if not os.getenv('JARVIS_FG_ADA_PATHS'):
        os.getenv('JARVIS_FG_ADA_PATHS')
    raw = ''.strip()
# WARNING: Decompyle incomplete


def _format_fg_call(action = None, params = None):
    parts = []
# WARNING: Decompyle incomplete


def _map_ada_tool_call(name = None, arguments = None):
    if not arguments:
        arguments
    args = dict({ })
# WARNING: Decompyle incomplete


def _parse_ada_row(row = None):
    if not row.get('messages'):
        row.get('messages')
    messages = []
    user = ''
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if not msg.get('role') == 'user':
            continue
        if not msg.get('content'):
            msg.get('content')
        user = str('').strip()
        messages
    if not user:
        return None
    for msg in messages:
        if isinstance(msg, dict) or msg.get('role') != 'assistant':
            continue
        if not msg.get('tool_calls'):
            msg.get('tool_calls')
        tool_calls = []
        if not tool_calls:
            continue
        tc = tool_calls[0] if isinstance(tool_calls[0], dict) else { }
        fn = tc.get('function') if isinstance(tc.get('function'), dict) else { }
        if not fn.get('name'):
            fn.get('name')
        ada_name = str('').strip()
        if ada_name or ada_name in _ADA_SKIP_ACTIONS:
            messages
            return None
        if not fn.get('arguments'):
            fn.get('arguments')
        mapped = _map_ada_tool_call(ada_name, { })
        if not mapped:
            return None
        (action, params) = mapped
        if action == 'planner_add_task':
            if not params.get('text'):
                params.get('text')
            if not str('').strip():
                return None
        if action == 'planner_set_timer':
            if not params.get('duration'):
                params.get('duration')
            if not str('').strip():
                return None
        if action == 'planner_set_alarm':
            if not params.get('time'):
                params.get('time')
            if not str('').strip():
                return None
        if action == 'web_search':
            if not params.get('query'):
                params.get('query')
            if not str('').strip():
                return None
        
        return None, (user, _format_fg_call(action, params))


def load_ada_training_rows():
    '''Load Ada FunctionGemma rows from USB paths, mapped to ARIA router actions.'''
    if os.getenv('JARVIS_FG_IMPORT_ADA', '1').strip().lower() in ('0', 'false', 'no'):
        return []
    rows = None
    seen = set()
    for path in _ada_training_paths():
        text = path.read_text(encoding = 'utf-8')
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            parsed = _parse_ada_row(row)
            if not parsed:
                continue
            key = (parsed[0].lower(), parsed[1])
            if key in seen:
                continue
            seen.add(key)
            rows.append(parsed)
    return rows
    except OSError:
        exc = None
        log.warning('Ada training path unreadable %s: %s', path, exc)
        exc = None
        del exc
        continue
        exc = None
        del exc
    except json.JSONDecodeError:
        continue


def export_functiongemma_jsonl(*, core_only):
    '''Export FunctionGemma fine-tuning JSONL (tool-call targets).'''
    pass
# WARNING: Decompyle incomplete


def train_functiongemma_router(*, output_dir):
    '''Export FG dataset and fine-tune when unsloth/transformers training is available.'''
    pass
# WARNING: Decompyle incomplete


def train_router_model(*, name):
    '''Build Ollama Modelfile from exported JSONL and run `ollama create`.'''
    router_model = router_model
    import jarvis.local_router
    path = export_training_jsonl()
    if path.is_file() or path.stat().st_size == 0:
        return {
            'ok': False,
            'error': 'No training rows exported' }
    examples = None
    for line in path.read_text(encoding = 'utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not row.get('messages'):
            row.get('messages')
        msgs = []
        if len(msgs) >= 2:
            examples.append(f'''User: {msgs[0].get('content', '')}\nAssistant: {msgs[1].get('content', '')}''')
        if not len(examples) >= 24:
            continue
        path.read_text(encoding = 'utf-8').splitlines()
    base = router_model()
    body = [
        f'''FROM {base}''',
        'PARAMETER temperature 0',
        'PARAMETER num_predict 120',
        'SYSTEM You are a fast intent router. Reply with ONLY one JSON object.',
        '']
    for ex in examples:
        body.append(f'''MESSAGE user {ex.split(chr(10))[0].replace('User: ', '')}''')
        if not '\n' in ex:
            continue
        body.append(f'''MESSAGE assistant {ex.split(chr(10), 1)[1].replace('Assistant: ', '')}''')
    MODELFILE.write_text('\n'.join(body) + '\n', encoding = 'utf-8')
    
    try:
        proc = subprocess.run([
            'ollama',
            'create',
            name,
            '-f',
            str(MODELFILE)], capture_output = True, text = True, timeout = 600, check = False)
        if proc.returncode != 0:
            if not proc.stderr:
                proc.stderr
                if not proc.stdout:
                    proc.stdout
            return {
                'ok': False,
                'error': 'ollama create failed'[:400],
                'modelfile': str(MODELFILE) }
        return {
            'ok': None,
            'model': name,
            'modelfile': str(MODELFILE),
            'examples': len(examples) }
        except json.JSONDecodeError:
            continue
    except Exception:
        exc = None
        log.warning('router train failed: %s', exc)
        del exc
        return None
        None = 
        del exc


