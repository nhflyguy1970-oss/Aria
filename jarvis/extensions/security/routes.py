'''Security routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def security_routes():
    return [
        RouteRule('security_status', 6, 'security status', (lambda m, lower, _s: bool(re.search('\\b(security|lock) status\\b', lower))))]

