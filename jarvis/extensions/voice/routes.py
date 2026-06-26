# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Voice fast-path routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def voice_routes():
    return [
        RouteRule('voice_smoke_test', 7, 'voice smoke test', (lambda m, lower, _s: bool(re.search('\\b(hello aria|voice smoke|voice test)\\b', lower))))]

