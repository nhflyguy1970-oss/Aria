# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Smart home P2 — Kasa, scenes, unified devices.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class SmarthomeExtension(Extension):
    meta = ExtensionMeta(name = 'smarthome', version = '1.0.0', description = 'Kasa devices, scene presets, unified device router', module_label = 'automation')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.smarthome

    
    def routes(self):
        smarthome_routes = smarthome_routes
        import jarvis.extensions.smarthome.routes
        return smarthome_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.smarthome.api
        register_routes(app, assistant)


EXTENSION = SmarthomeExtension()
