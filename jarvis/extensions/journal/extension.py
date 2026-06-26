# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Journal extension — bullet journal actions, routing, and GUI API.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class JournalExtension(Extension):
    meta = ExtensionMeta(name = 'journal', version = '1.0.0', description = 'Bullet journal logging, tasks, reflection, and migration', module_label = 'journal')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.journal
        project_handlers = project_handlers
        import jarvis.extensions.journal

    
    def routes(self):
        journal_routes = journal_routes
        import jarvis.extensions.journal.routes
        return journal_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.journal.api
        register_routes(app, assistant)


EXTENSION = JournalExtension()
