# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Git extension — status, diff, commit, branch, PR, summarize.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class GitExtension(Extension):
    meta = ExtensionMeta(name = 'git', version = '1.0.0', description = 'Git status, diff, commit, branch, and pull requests', module_label = 'coding')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.git

    
    def routes(self):
        git_routes = git_routes
        import jarvis.extensions.git.routes
        return git_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.git.api
        register_routes(app, assistant)


EXTENSION = GitExtension()
