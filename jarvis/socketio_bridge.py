# Source Generated with Decompyle++
# File: socketio_bridge.cpython-312.pyc (Python 3.12)

'''Optional Socket.IO bridge alongside WebSocket hub.'''
from __future__ import annotations
import logging
log = logging.getLogger('jarvis.socketio')

def socketio_available():
    
    try:
        import socketio
        return True
    except ImportError:
        return False



def wrap_asgi_app(app):
    '''Wrap FastAPI with Socket.IO when JARVIS_SOCKETIO=1.'''
    pass
# WARNING: Decompyle incomplete


def mount_socketio(app = None):
    '''Deprecated — use wrap_asgi_app at uvicorn startup.'''
    return wrap_asgi_app(app) is not app

