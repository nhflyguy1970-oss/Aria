# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Memory extension — facts, profile, cheatsheets, checkpoints.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class MemoryExtension(Extension):
    meta = ExtensionMeta(name = 'memory', version = '1.0.0', description = 'Long-term memory, cheatsheets, profile, and project checkpoints', module_label = 'memory')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.memory
        document_learning_handlers = document_learning_handlers
        import jarvis.extensions.memory
        observation_learning_handlers = observation_learning_handlers
        import jarvis.extensions.memory
        correction_learning_handlers = correction_learning_handlers
        import jarvis.extensions.memory

    
    def routes(self):
        memory_routes = memory_routes
        import jarvis.extensions.memory.routes
        return memory_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.memory.api
        register_routes(app, assistant)


EXTENSION = MemoryExtension()
