# Source Generated with Decompyle++
# File: active_project.cpython-312.pyc (Python 3.12)

'''Persist active project workspace slug.'''
from __future__ import annotations
import json
from pathlib import Path
from jarvis.config import DATA_DIR
ACTIVE_FILE = DATA_DIR / 'active_project.json'

def coding_root_for_slug(slug = None):
    '''Coding/search root: git_path when set, else workspace root.'''
    get_project = get_project
    import jarvis.project_registry
    meta = get_project(slug)
    if not meta:
        return None
    if not meta.get('git_path'):
        meta.get('git_path')
    git_path = ''.strip()
    if git_path:
        p = Path(git_path).expanduser()
        if p.is_dir():
            return p.resolve()
        if not None.get('paths'):
            None.get('paths')
    if not { }.get('root'):
        { }.get('root')
    root = ''
    if root:
        p = Path(root)
        if p.is_dir():
            return p.resolve()


def apply_active_project_effects(assistant = None, slug = None):
    '''Wire memory namespace, coding root, and code index for active project.'''
    if not slug:
        slug
    assistant.session.note_memory_namespace('default')
    if not slug:
        return None
    root = coding_root_for_slug(slug)
# WARNING: Decompyle incomplete


def get_active_slug():
    if not ACTIVE_FILE.is_file():
        return ''
    
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding = 'utf-8'))
        if not data.get('slug'):
            data.get('slug')
        return ''.strip()
    except (json.JSONDecodeError, OSError):
        return ''



def set_active_slug(slug = None):
    get_project = get_project
    import jarvis.project_registry
    if not slug:
        slug
    slug = ''.strip()
    if slug:
        meta = get_project(slug)
        if not meta:
            raise ValueError(f'''Unknown project: {slug}''')
        if meta.get('archived'):
            raise ValueError(f'''Project is archived: {slug}''')
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    payload = {
        'slug': slug }
    ACTIVE_FILE.write_text(json.dumps(payload, indent = 2), encoding = 'utf-8')
    
    try:
        get_assistant = get_assistant
        import jarvis.assistant_instance
        apply_active_project_effects(get_assistant(), slug)
        import threading
        threading.Thread(target = _warm_project_background, args = (slug,), daemon = True, name = 'project-warm').start()
        return payload
    except Exception:
        continue



def _warm_project_background(slug = None):
    '''Warm code index and FunctionGemma after project switch.'''
    if not slug:
        return None
# WARNING: Decompyle incomplete


def get_active_project():
    slug = get_active_slug()
    if not slug:
        return None
    get_project = get_project
    import jarvis.project_registry
    return get_project(slug)


def browser_session_dir():
    '''Per-project browser profile path for Playwright.'''
    slug = get_active_slug()
    if not slug:
        PROJECTS_ROOT = PROJECTS_ROOT
        import jarvis.project_registry
        return str(PROJECTS_ROOT / '_default' / 'browser')
    project_dir = project_dir
    import jarvis.project_registry
    path = project_dir(slug) / 'browser'
    path.mkdir(parents = True, exist_ok = True)
    return str(path)


def cad_dir(slug = None):
    '''Per-project CAD output directory.'''
    pass
# WARNING: Decompyle incomplete

