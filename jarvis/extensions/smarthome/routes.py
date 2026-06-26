# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Smart home fast routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def smarthome_routes():
    return [
        RouteRule('scene_recall', 13, 'scene preset', (lambda m, lower, _s: bool(re.search('\\b(movie mode|work mode)\\b', lower))), (lambda m: if 'movie' in m.lower():
{
'preset': 'movie mode' }{
None: 'preset' })),
        RouteRule('kasa_discover', 14, 'discover kasa', (lambda m, lower, _s: bool(re.search('\\b(discover|find|scan)\\s+kasa\\b', lower))))]

