# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Voice P1 extension.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class VoiceExtension(Extension):
    meta = ExtensionMeta(name = 'voice', version = '1.0.0', description = 'Voice routing, smoke test, sessions, duplex settings', module_label = 'audio')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.voice

    
    def routes(self):
        voice_routes = voice_routes
        import jarvis.extensions.voice.routes
        return voice_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.voice.api
        register_routes(app, assistant)


EXTENSION = VoiceExtension()
