# Source Generated with Decompyle++
# File: __init__.cpython-312.pyc (Python 3.12)

'''Registered action handlers.'''
from jarvis.handlers.media import MediaHandler
_loaded = False

def ensure_handlers_loaded():
    global _loaded
    if _loaded:
        return None
    load_extensions = load_extensions
    import jarvis.extensibility.loader
    meta = meta
    import jarvis.handlers
    knowledge_handlers = knowledge_handlers
    import jarvis.handlers
    skill_handlers = skill_handlers
    import jarvis.handlers
    workflow_handlers = workflow_handlers
    import jarvis.handlers
    self_upgrade_handlers = self_upgrade_handlers
    import jarvis.handlers
    aria_coder_handlers = aria_coder_handlers
    import jarvis.handlers
    register_queue_actions = register_queue_actions
    import jarvis.handlers.queues
    load_extensions()
    register_queue_actions()
    _loaded = True

__all__ = [
    'MediaHandler',
    'ensure_handlers_loaded']
