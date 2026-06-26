# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Browser automation P2 extension.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class BrowserExtension(Extension):
    meta = ExtensionMeta(name = 'browser', version = '1.0.0', description = 'Web browse agent, search bridge, safety limits', module_label = 'web')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.browser

    
    def routes(self):
        browser_routes = browser_routes
        import jarvis.extensions.browser.routes
        return browser_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.browser.api
        register_routes(app, assistant)


EXTENSION = BrowserExtension()
