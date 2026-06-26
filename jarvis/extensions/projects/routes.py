# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Fast-path routes for projects and scenes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def project_routes():
    return [
        RouteRule('project_switch', 14, 'switch project', (lambda m, lower, _s: bool(re.search('\\b(switch|open|use)\\s+(?:to\\s+)?project\\b', lower))), (lambda m: {
'slug': re.sub('.*project\\s+', '', m, flags = re.I).strip() })),
        RouteRule('project_list', 15, 'list projects', (lambda m, lower, _s: bool(re.search('\\b(list|show)\\s+projects\\b', lower))))]

