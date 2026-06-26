# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Engineering P3 extension.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class EngineeringExtension(Extension):
    meta = ExtensionMeta(name = 'engineering', version = '1.0.0', description = 'CAD generation, slicing, and 3D printer control', module_label = 'engineering')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.engineering

    
    def routes(self):
        engineering_routes = engineering_routes
        import jarvis.extensions.engineering.routes
        return engineering_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.engineering.api
        register_routes(app, assistant)


EXTENSION = EngineeringExtension()
