# Source Generated with Decompyle++
# File: cad_store.cpython-312.pyc (Python 3.12)

'''CAD model registry — global + per-project versioned history.'''
from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
ENGINEERING_DIR = DATA_DIR / 'engineering'
INDEX_FILE = ENGINEERING_DIR / 'models.json'
LAST_SCRIPT_FILE = ENGINEERING_DIR / 'last_script.json'

def _cad_root():
    
    try:
        get_active_slug = get_active_slug
        import jarvis.active_project
        project_dir = project_dir
        import jarvis.project_registry
        slug = get_active_slug()
        if slug:
            root = project_dir(slug) / 'cad'
            root.mkdir(parents = True, exist_ok = True)
            return root
        ENGINEERING_DIR.mkdir(parents = True, exist_ok = True)
        return ENGINEERING_DIR
    except Exception:
        continue



def _load_index():
    path = _cad_root() / 'models.json'
    if path.is_file() and INDEX_FILE.is_file():
        path = INDEX_FILE
    if not path.is_file():
        return {
            'models': [] }
    
    try:
        return json.loads(path.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save_index(data = None):
    path = _cad_root() / 'models.json'
    path.parent.mkdir(parents = True, exist_ok = True)
    path.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')
    if path != INDEX_FILE:
        INDEX_FILE.parent.mkdir(parents = True, exist_ok = True)
        INDEX_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')
        return None


def new_model_id():
    return uuid.uuid4().hex[:10]


def register_model(*, prompt, name, backend, stl_path, scad_path, script_path, notes, verify, model_id):
    data = _load_index()
    if not model_id:
        model_id
    if not ''.strip():
        ''.strip()
    mid = new_model_id()
    now = time.time()
    if not name:
        name
    if not verify:
        verify
    row = {
        'id': mid,
        'name': prompt[:120],
        'prompt': prompt[:2000],
        'tags': [
            'aria'],
        'backend': backend,
        'created': now,
        'updated': now,
        'stl_rendered': bool(stl_path),
        'stl_path': stl_path,
        'scad_path': scad_path,
        'script_path': script_path,
        'notes': notes[:500],
        'verify': { },
        'version': 1 }
    data.setdefault('models', []).append(row)
    _save_index(data)
    return row


def list_models(limit = None):
    if not _load_index().get('models'):
        _load_index().get('models')
    rows = list([])
    rows.sort(key = (lambda r: if not r.get('updated'):
r.get('updated')float(0)), reverse = True)
    return rows[:limit]


def get_model(model_id = None):
    for row in list_models(limit = 500):
        if not row.get('id') == model_id:
            continue
        
        return list_models(limit = 500), row


def update_model(model_id = None, **fields):
    data = _load_index()
    if not data.get('models'):
        data.get('models')
# WARNING: Decompyle incomplete


def paths_for_model(model_id = None):
    root = _cad_root()
    return {
        'stl': root / f'''{model_id}.stl''',
        'scad': root / f'''{model_id}.scad''',
        'script': root / f'''{model_id}.py''',
        'gcode': root / f'''{model_id}.gcode''' }


def save_last_script(backend = None, content = None, *, model_id, prompt):
    ENGINEERING_DIR.mkdir(parents = True, exist_ok = True)
    payload = {
        'backend': backend,
        'content': content[:20000],
        'model_id': model_id,
        'prompt': prompt[:2000],
        'updated': time.time() }
    LAST_SCRIPT_FILE.write_text(json.dumps(payload, indent = 2), encoding = 'utf-8')


def load_last_script():
    if not LAST_SCRIPT_FILE.is_file():
        return { }
    
    try:
        return json.loads(LAST_SCRIPT_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def clear_gallery(*, delete_files):
    '''Remove all models from the registry and delete associated CAD files.'''
    removed_ids = []
    deleted_files = []
    data = _load_index()
    root = _cad_root()
    if not data.get('models'):
        data.get('models')
    for row in list([]):
        if not row.get('id'):
            row.get('id')
        mid = ''.strip()
        if mid:
            removed_ids.append(mid)
        if not delete_files:
            continue
        for key in ('stl_path', 'scad_path', 'script_path'):
            if not row.get(key):
                row.get(key)
            p = ''.strip()
            if not p:
                continue
            path = Path(p)
            if not path.is_file():
                continue
            path.unlink()
            deleted_files.append(str(path))
        if not mid:
            continue
        for path in paths_for_model(mid).values():
            if not path.is_file():
                continue
            path.unlink()
            if not str(path) not in deleted_files:
                continue
            deleted_files.append(str(path))
    empty = {
        'models': [] }
    _save_index(empty)
    if INDEX_FILE != _cad_root() / 'models.json':
        INDEX_FILE.write_text(json.dumps(empty, indent = 2), encoding = 'utf-8')
    if delete_files and LAST_SCRIPT_FILE.is_file():
        LAST_SCRIPT_FILE.unlink()
        deleted_files.append(str(LAST_SCRIPT_FILE))
    return {
        'ok': True,
        'removed': len(removed_ids),
        'ids': removed_ids,
        'deleted_files': len(deleted_files) }

