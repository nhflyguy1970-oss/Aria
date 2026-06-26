# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Security routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def security_routes():
    return [
        RouteRule('security_status', 6, 'security status', (lambda m, lower, _s: bool(re.search('\\b(security|lock) status\\b', lower))))]

