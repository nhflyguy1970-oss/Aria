# Source Generated with Decompyle++
# File: extension.cpython-312.pyc (Python 3.12)

'''Planner extension — tasks, timers, alarms, calendar.'''
from jarvis.extensibility.base import Extension, ExtensionMeta

class PlannerExtension(Extension):
    meta = ExtensionMeta(name = 'planner', version = '1.0.0', description = 'Life planner: tasks, timers, alarms, local calendar', module_label = 'planner')
    
    def load(self = None):
        handlers = handlers
        import jarvis.extensions.planner

    
    def routes(self):
        planner_routes = planner_routes
        import jarvis.extensions.planner.routes
        return planner_routes()

    
    def register_api(self = None, app = None, assistant = None):
        register_routes = register_routes
        import jarvis.extensions.planner.api
        register_routes(app, assistant)


EXTENSION = PlannerExtension()
