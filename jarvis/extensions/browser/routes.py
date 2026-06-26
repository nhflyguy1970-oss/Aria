# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Browser fast routes.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def _search_browse_query(message = None):
    if not message:
        message
    text = ''.strip()
    text = re.sub('^(please\\s+)?', '', text, flags = re.I)
    text = re.sub('\\bsearch (the )?web for\\s+', '', text, flags = re.I)
    text = re.sub('\\band (open|browse)\\s*$', '', text, flags = re.I)
    text = re.sub('\\bfrom (the )?web\\s*$', '', text, flags = re.I)
    if not text.strip():
        text.strip()
    return message.strip()


def browser_routes():
    return [
        RouteRule('browse_web', 12, 'browse url', (lambda m, lower, _s: bool(re.search('\\b(open|browse|go to)\\s+(https?://|www\\.)', lower))), (lambda m: if re.search('(https?://\\S+|www\\.\\S+)', m, re.I):
{
'url': re.search('(https?://\\S+|www\\.\\S+)', m, re.I).group(1).rstrip('.,)') }{
None: 'url' })),
        RouteRule('search_and_browse', 14, 'search browse open', (lambda m, lower, _s: if not re.search('\\b(search .+ and (open|browse)|find .+ and (open|browse))\\b', lower):
re.search('\\b(search .+ and (open|browse)|find .+ and (open|browse))\\b', lower)if not re.search('\\bsearch (the )?web for .+ and (open|browse)\\b', lower):
re.search('\\bsearch (the )?web for .+ and (open|browse)\\b', lower)if not re.search('\\bopen .+ from (the )?web\\b', lower):
re.search('\\bopen .+ from (the )?web\\b', lower)if not re.search('\\bfind .+ under \\$?\\d+ on \\w', lower):
re.search('\\bfind .+ under \\$?\\d+ on \\w', lower)bool(re.search('\\bshop(ping)? for .+ (on|at) \\w', lower))), (lambda m: {
'query': _search_browse_query(m) })),
        RouteRule('browser_takeover', 8, 'browser takeover', (lambda m, lower, _s: bool(re.search('\\b(take over|takeover) (the )?browser\\b', lower)))),
        RouteRule('browser_run_task', 10, 'browser agent task', (lambda m, lower, _s: if not re.search('\\b(click|find|fill|press|select)\\b.+\\b(on the )?(page|site|browser)\\b', lower):
re.search('\\b(click|find|fill|press|select)\\b.+\\b(on the )?(page|site|browser)\\b', lower)bool(re.search('\\bbrowser agent\\b', lower))), (lambda m: {
'goal': m.strip() }))]

