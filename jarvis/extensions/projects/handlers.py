# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Project workspace action handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.p2_flags import projects_enabled
from jarvis.response import err, ok

def _disabled():
    return err('Projects disabled (JARVIS_PROJECTS=0).', module = 'projects')

project_create = (lambda assistant = None, params = None, message = register_action('project_create', module = 'projects', description = 'Create project workspace'): if not projects_enabled():
_disabled()create_project = create_projectimport jarvis.project_registryif not params.get('title'):
params.get('title')title = ''.strip()if not title:
m = re.search('(?:create|new|start)\\s+(?:project\\s+)?(.+)', message, re.I)title = m.group(1) if m else message.strip()if not title:
err('Project title required.', module = 'projects')if not params.get('description'):
params.get('description')meta = create_project(title, description = '')ok(f'''Created project **{meta['title']}** (`{meta['slug']}`).''', module = 'projects', type = 'projects', project = meta))()
project_list = (lambda assistant = None, params = None, message = register_action('project_list', info = True, module = 'projects', description = 'List projects'): if not projects_enabled():
_disabled()get_active_slug = get_active_slugimport jarvis.active_projectlist_projects = list_projectsimport jarvis.project_registryactive = get_active_slug()rows = list_projects()if not rows:
ok('No projects yet. Say *create project My Lab*.', module = 'projects', type = 'projects')lines = Nonefor p in rows:
mark = ' (active)' if p['slug'] == active else ''lines.append(f'''- **{p['title']}** `{p['slug']}`{mark}''')ok('**Projects:**\n' + '\n'.join(lines), module = 'projects', type = 'projects'))()
project_switch = (lambda assistant = None, params = None, message = register_action('project_switch', module = 'projects', description = 'Switch active project'): if not projects_enabled():
_disabled()set_active_slug = set_active_slugimport jarvis.active_projectlist_projects = list_projectsimport jarvis.project_registryif not params.get('slug'):
params.get('slug')if not params.get('project'):
params.get('project')slug = ''.strip()if not slug:
m = re.search('(?:switch|open|use)\\s+(?:to\\s+)?(?:project\\s+)?([\\w-]+)', message, re.I)slug = m.group(1).strip() if m else ''if not slug:
None(', '.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(list_projects()[:6]()), module = 'projects')
    
    try:
        set_active_slug(slug)
        return ok(f'''Switched to project **{slug}**.''', module = 'projects', type = 'projects', project_slug = slug)
    except ValueError:
        exc = None
        del exc
        return None
        None = 
        del exc

)()
project_archive = (lambda assistant = None, params = None, message = register_action('project_archive', module = 'projects', description = 'Archive project'): if not projects_enabled():
_disabled()archive_project = archive_projectimport jarvis.project_registryif not params.get('slug'):
params.get('slug')slug = ''.strip()if not slug:
m = re.search('archive\\s+(?:project\\s+)?([\\w-]+)', message, re.I)slug = m.group(1) if m else ''if not archive_project(slug, archived = True):
err(f'''Project not found: {slug}''', module = 'projects')None(f'''Archived project `{slug}`.''', module = 'projects', type = 'projects'))()
project_import_git = (lambda assistant = None, params = None, message = register_action('project_import_git', module = 'projects', description = 'Import git repo as project'): if not projects_enabled():
_disabled()set_active_slug = set_active_slugimport jarvis.active_projectimport_git_repo = import_git_repoimport jarvis.project_registryif not params.get('path'):
params.get('path')path = ''.strip()if not path:
m = re.search('import\\s+(?:git\\s+)?(?:repo\\s+)?(.+)', message, re.I)path = m.group(1).strip() if m else ''try:
if not params.get('title'):
params.get('title')meta = import_git_repo(path, title = '')set_active_slug(meta['slug'])ok(f'''Imported git repo as **{meta['title']}** (`{meta['slug']}`).''', module = 'projects', type = 'projects', project = meta)except ValueError:
exc = Nonedel excNoneNone = del exc)()
