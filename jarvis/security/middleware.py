# Source Generated with Decompyle++
# File: middleware.cpython-312.pyc (Python 3.12)

'''PIN lock middleware — require valid session for API when enabled.'''
from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jarvis.auth import client_ip
from jarvis.p4_flags import pin_lock_enabled
from jarvis.security.pin_lock import pin_configured, session_valid, touch_session
from jarvis.security.trusted_devices import is_trusted

class PinLockMiddleware(BaseHTTPMiddleware):
    EXEMPT_PREFIXES = ('/static', '/favicon', '/api/health', '/api/health/lite', '/api/live', '/api/ping', '/api/lan', '/api/automation/inbound')
    EXEMPT_PATHS = frozenset({
        '/api/security/unlock',
        '/api/security/lock/status',
        '/api/homeassistant/daylight',
        '/api/security/session/touch'})
    
    async def dispatch(self = None, request = None, call_next = None):
        pass
    # WARNING: Decompyle incomplete


