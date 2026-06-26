# Source Generated with Decompyle++
# File: api.cpython-312.pyc (Python 3.12)

'''Projects HTTP API.'''
from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse

def register_routes(app = None, assistant = None):
    projects_list = (lambda : registry_snapshot = registry_snapshotimport jarvis.project_registry# WARNING: Decompyle incomplete
)()
    projects_create = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    projects_switch = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    projects_import_git = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    projects_archive = (lambda slug = None: archive_project = archive_projectimport jarvis.project_registry{
'ok': archive_project(slug, archived = True) })()
    projects_active = (lambda : get_active_project = get_active_projectimport jarvis.active_project{
'ok': True,
'project': get_active_project() })()

