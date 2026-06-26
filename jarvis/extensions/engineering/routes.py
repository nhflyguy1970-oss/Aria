# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Engineering voice/chat routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def engineering_routes():
    return [
        RouteRule('cad_status', 8, 'cad status', (lambda m, lower, _s: bool(re.search('\\b(cad status|cad tools|engineering status)\\b', lower)))),
        RouteRule('generate_cad', 12, 'generate cad', (lambda m, lower, _s: if not re.search('\\b(design|generate|create|make)\\b.+\\b(cad|stl|part|adapter|bracket|hose)\\b', lower):
re.search('\\b(design|generate|create|make)\\b.+\\b(cad|stl|part|adapter|bracket|hose)\\b', lower)bool(re.search('\\bengineering design\\b', lower))), (lambda m: {
'prompt': m.strip() })),
        RouteRule('iterate_cad', 13, 'iterate cad', (lambda m, lower, _s: if not re.search('\\b(iterate|edit|modify|change|update)\\b.+\\b(cad|design|model|part|stl)\\b', lower):
re.search('\\b(iterate|edit|modify|change|update)\\b.+\\b(cad|design|model|part|stl)\\b', lower)bool(re.search('\\bmake it (taller|shorter|wider|thinner|thicker|bigger|smaller)\\b', lower))), (lambda m: {
'prompt': m.strip(),
'edit': True })),
        RouteRule('slice_stl', 10, 'slice stl', (lambda m, lower, _s: bool(re.search('\\bslice\\b.+\\b(stl|g-?code)\\b', lower)))),
        RouteRule('printer_status', 8, 'printer status', (lambda m, lower, _s: bool(re.search('\\b(printer|moonraker|klipper)\\b.+\\bstatus\\b', lower)))),
        RouteRule('teach_cad', 14, 'teach cad', (lambda m, lower, _s: bool(re.search('\\bteach\\s+cad\\b', lower))), (lambda m: { }))]

