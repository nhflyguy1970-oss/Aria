# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''P4 security & presence extension.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class SecurityExtension(Extension):
    meta = ExtensionMeta(name = 'security', version = '1.0.0', description = 'PIN lock, face auth, trusted LAN, presence, tools status', module_label = 'security')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.security

    
    def routes(self):
        security_routes = security_routes
        import jarvis.extensions.security.routes
        return security_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.security.api
        register_routes(app, assistant)


EXTENSION = SecurityExtension()
