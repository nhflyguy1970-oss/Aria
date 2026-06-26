# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Projects extension — P2 workspace.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class ProjectsExtension(Extension):
    meta = ExtensionMeta(name = 'projects', version = '1.0.0', description = 'Named project workspaces, git import, active project', module_label = 'projects')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.projects

    
    def routes(self):
        project_routes = project_routes
        import jarvis.extensions.projects.routes
        return project_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.projects.api
        register_routes(app, assistant)


EXTENSION = ProjectsExtension()
