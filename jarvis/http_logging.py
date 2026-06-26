# Source Generated with Decompyle++
# File: http_logging.cpython-312.pyc (Python 3.12)

'''HTTP request logging middleware.'''
from __future__ import annotations
import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jarvis.logging_config import clear_request_id, set_request_id
from jarvis.request_activity import begin_heavy, end_heavy, is_heavy_api_path
logger = logging.getLogger('jarvis.http')
_SKIP_PATHS = frozenset({
    '/api/live',
    '/api/ping',
    '/api/health/lite'})

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self = None, request = None, call_next = None):
        pass
    # WARNING: Decompyle incomplete


