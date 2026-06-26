# Source Generated with Decompyle++
# File: project_registry.cpython-312.pyc (Python 3.12)

'''Named project workspace registry — data/projects/{slug}/meta.json.'''
from __future__ import annotations
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
PROJECTS_ROOT = DATA_DIR / 'projects'
SUBDIRS = ('cad', 'exports', 'browser')

def _slugify(name = None):
    if not name:
        name
    s = re.sub('[^\\w\\s-]', '', ''.lower())
    s = re.sub('[\\s_]+', '-', s).strip('-')
    if not s[:48]:
        s[:48]
    return 'project'


def _now():
    return datetime.now(timezone.utc).isoformat(timespec = 'seconds')


def project_dir(slug = None):
    return PROJECTS_ROOT / _slugify(slug)


def meta_path(slug = None):
    return project_dir(slug) / 'meta.json'


def _read_meta(path = None):
    if not path.is_file():
        return { }
    
    try:
        data = json.loads(path.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return 



def _write_meta(slug = None, meta = None):
    root = project_dir(slug)
    root.mkdir(parents = True, exist_ok = True)
    for sub in SUBDIRS:
        (root / sub).mkdir(exist_ok = True)
    meta['slug'] = _slugify(slug)
    meta['updated'] = _now()
    meta_path(slug).write_text(json.dumps(meta, indent = 2), encoding = 'utf-8')


def create_project(title = None, *, description, git_path):
    slug = _slugify(title)
    if meta_path(slug).is_file():
        base = slug
        n = 2
        if meta_path(f'''{base}-{n}''').is_file():
            n += 1
            if meta_path(f'''{base}-{n}''').is_file():
                continue
        slug = f'''{base}-{n}'''
    now = _now()
    if not title:
        title
    if not description:
        description
    if not git_path:
        git_path
    if not ''.strip():
        ''.strip()
    meta = {
        'slug': slug,
        'title': slug.strip(),
        'description': ''.strip(),
        'created': now,
        'updated': now,
        'archived': False,
        'git_path': None }
    _write_meta(slug, meta)
    
    try:
        ProjectJournal = ProjectJournal
        import jarvis.project_journal
        ProjectJournal(slug).ensure(title = meta['title'])
        return meta
    except Exception:
        return meta



def get_project(slug = None):
    path = meta_path(slug)
    if not path.is_file():
        return None
    meta = _read_meta(path)
    meta['paths'] = {
        'root': str(project_dir(slug)),
        'cad': str(project_dir(slug) / 'cad'),
        'exports': str(project_dir(slug) / 'exports'),
        'browser': str(project_dir(slug) / 'browser') }
    return meta


def _sync_journal_workspaces():
    '''Ensure journal-only slugs appear in the workspace registry.'''
    
    try:
        list_journal_projects = list_projects
        import jarvis.project_journal
        for jp in list_journal_projects():
            if not jp.get('slug'):
                jp.get('slug')
            slug = ''.strip()
            if slug or meta_path(slug).is_file():
                continue
            if not jp.get('title'):
                jp.get('title')
            meta = create_project(slug, description = 'Synced from journal')
            meta['journal_synced'] = True
            _write_meta(meta['slug'], meta)
        return None
    except Exception:
        return None



def list_projects(*, include_archived):
    PROJECTS_ROOT.mkdir(parents = True, exist_ok = True)
    _sync_journal_workspaces()
    out = []
    for child in sorted(PROJECTS_ROOT.iterdir()):
        if not child.is_dir():
            continue
        meta = get_project(child.name)
        if not meta:
            continue
        if not meta.get('archived') and include_archived:
            continue
        out.append(meta)
    out.sort(key = (lambda m: if not m.get('updated'):
m.get('updated')''), reverse = True)
    return out


def archive_project(slug = None, *, archived):
    meta = get_project(slug)
    if not meta:
        return False
    meta['archived'] = bool(archived)
    _write_meta(slug, meta)
    return True


def update_project(slug = None, patch = None):
    meta = get_project(slug)
    if not meta:
        return None
# WARNING: Decompyle incomplete


def import_git_repo(path = None, *, title):
    is_repo = is_repo
    import jarvis.git_util
    repo = Path(path).expanduser().resolve()
    if not repo.is_dir() or is_repo(repo):
        raise ValueError(f'''Not a git repository: {repo}''')
    if not title.strip():
        title.strip()
    name = repo.name
    meta = create_project(name, git_path = str(repo))
    
    try:
        build_index = build_index
        import jarvis.code_index
        idx_file = project_dir(meta['slug']) / 'code_index.json'
        build_index(repo, index_path = idx_file)
        return meta
    except Exception:
        return meta



def registry_snapshot():
    get_active_slug = get_active_slug
    import jarvis.active_project
    return {
        'enabled': True,
        'root': str(PROJECTS_ROOT),
        'active': get_active_slug(),
        'projects': list_projects(),
        'count': len(list_projects(include_archived = True)) }

