# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Fly-tying extension — search patterns, show recipes, RAG Q&A.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class FlyTyingExtension(Extension):
    meta = ExtensionMeta(name = 'flytying', version = '1.0.0', description = 'Fly-tying pattern search, recipes, and RAG assistant', module_label = 'flytying')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.flytying
        
        try:
            maybe_sync_library = maybe_sync_library
            import jarvis.flytying.knowledge
            maybe_sync_library()
            return None
        except Exception:
            return None


    
    def routes(self):
        flytying_routes = flytying_routes
        import jarvis.extensions.flytying.routes
        return flytying_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.flytying.api
        register_routes(app, assistant)


EXTENSION = FlyTyingExtension()
