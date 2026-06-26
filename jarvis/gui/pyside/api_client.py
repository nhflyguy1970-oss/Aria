# Source Generated with Decompyle++
# File: api_client.cpython-312.pyc (Python 3.12)

'''HTTP client for native PySide widgets (talks to running ARIA server).'''
from __future__ import annotations
import json
import logging
import urllib.error as urllib
import urllib.parse as urllib
import urllib.request as urllib
from typing import Any
log = logging.getLogger('jarvis.pyside.api')

def _request(base_url = None, path = None, *, method, timeout):
    url = f'''{base_url.rstrip('/')}{path}'''
    req = urllib.request.Request(url, method = method, data = b'' if method == 'POST' else None)
    req.add_header('Accept', 'application/json')
    
    try:
        resp = urllib.request.urlopen(req, timeout = timeout)
        raw = resp.read().decode('utf-8')
        if raw:
            pass
        else:
            
            try:
                None(None, None)
                return 
                with None:
                    if not json.loads(raw), { }:
                        pass
                
                try:
                    return None
                    
                    try:
                        pass
                    except urllib.error.HTTPError:
                        exc.read().decode('utf-8', errors = 'replace') = None
                        log.warning('HTTP %s %s: %s', exc.code, path, body[:200])
                        if not body:
                            body
                        del exc
                        return None
                        None = 
                        del exc
                        except Exception:
                            exc = None
                            log.warning('Request failed %s: %s', path, exc)
                            del exc
                            return None
                            None = 
                            del exc






def fetch_dashboard(base_url = None):
    info = _request(base_url, '/api/system-info')
    news = _request(base_url, '/api/curated-news?use_ai=true')
    presets = _request(base_url, '/api/scenes/presets')
    if presets.get('ok', True):
        return {
            'info': info if info.get('ok', True) else { },
            'news': news if news.get('ok', True) else { },
            'presets': presets }
    return {
        'info': None,
        'news': info if info.get('ok', True) else { },
        'presets': news if news.get('ok', True) else { } }


def activate_scene(base_url = None, preset_id = None):
    enc = urllib.parse.quote(preset_id, safe = '')
    data = _request(base_url, f'''/api/scenes/presets/{enc}/activate''', method = 'POST')
    if not data.get('message'):
        data.get('message')
        if not data.get('error'):
            data.get('error')
    return (bool(data.get('ok')), str('done'))

