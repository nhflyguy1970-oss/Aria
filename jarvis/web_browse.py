# Source Generated with Decompyle++
# File: web_browse.cpython-312.pyc (Python 3.12)

'''Search + browse bridge and shopping templates.'''
from __future__ import annotations
import re
from typing import Any
from urllib.parse import urlparse
from jarvis.p2_flags import browser_agent_enabled

def pick_url_from_search(query = None, *, max_results):
    search = search
    import jarvis.web_search
    results = search(query, limit = max_results)
    if not results:
        results
    for row in []:
        if not row.get('url'):
            row.get('url')
            if not row.get('href'):
                row.get('href')
        url = ''.strip()
        if not url.startswith('http'):
            continue
        
        return [], url
    return ''


def search_and_browse(query = None, *, allow_risky):
    if not browser_agent_enabled():
        return {
            'ok': False,
            'message': 'Browser agent disabled' }
    url = None(query)
    if not url:
        return {
            'ok': False,
            'message': f'''No URL found for: {query}''' }
    navigate = navigate
    import jarvis.browser_agent
    result = navigate(url, allow_risky = allow_risky)
    result['query'] = query
    result['picked_url'] = url
    return result


def parse_shopping_query(message = None):
    '''Find X under $Y on site Z.'''
    if not message:
        message
    text = ''.strip()
    m = re.search('(?:find|search for|look for)\\s+(.+?)\\s+(?:under|below|less than)\\s+\\$?(\\d+(?:\\.\\d+)?)\\s+(?:on|at)\\s+(.+)$', text, re.I)
    if not m:
        return None
    return {
        'item': m.group(1).strip(),
        'max_price': float(m.group(2)),
        'site': m.group(3).strip().rstrip('.'),
        'query': f'''{m.group(1).strip()} site:{m.group(3).strip()}''' }


def shopping_search(message = None):
    spec = parse_shopping_query(message)
    if not spec:
        return {
            'ok': False,
            'message': 'Could not parse shopping query' }
    site = None['site']
    if not site.startswith('http'):
        host = site.replace('www.', '').split('/')[0]
        if '.' not in host:
            host = f'''{host}.com'''
        site = f'''https://{host}'''
    query = f'''{spec['item']} {site}'''
    return search_and_browse(query)


def is_risky_url(url = None):
    _check_url_safe = _check_url_safe
    import jarvis.browser_agent
    (ok, _) = _check_url_safe(url, allow_risky = False)
    return not ok

