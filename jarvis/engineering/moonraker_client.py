# Source Generated with Decompyle++
# File: moonraker_client.cpython-312.pyc (Python 3.12)

'''Moonraker / Klipper HTTP client.'''
from __future__ import annotations
import json
import urllib.error as urllib
import urllib.request as urllib
from pathlib import Path
from typing import Any

def _request(url = None, method = None, data = None, headers = ('GET', None, None)):
    if not headers:
        headers
    req = urllib.request.Request(url, data = data, method = method, headers = { })
    resp = urllib.request.urlopen(req, timeout = 15)
    raw = resp.read().decode('utf-8', errors = 'replace')
    None(None, None)
    return 
    with None:
        if not None, json.loads(raw) if raw.strip() else { }:
            pass


def printer_status(host = None, *, api_key):
    base = host.rstrip('/')
    headers = { }
    if api_key:
        headers['X-Api-Key'] = api_key
    
    try:
        data = _request(f'''{base}/printer/objects/query?print_stats&heater_bed&extruder''', headers = headers)
        result = data.get('result', { }).get('status', { })
        ps = result.get('print_stats', { })
        bed = result.get('heater_bed', { })
        ext = result.get('extruder', { })
        return {
            'ok': True,
            'state': ps.get('state', 'unknown'),
            'filename': ps.get('filename', ''),
            'progress': ps.get('progress', 0),
            'bed_c': bed.get('temperature'),
            'nozzle_c': ext.get('temperature') }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def upload_gcode(host = None, gcode_path = None, *, api_key):
    path = Path(gcode_path)
    if not path.is_file():
        return {
            'ok': False,
            'error': f'''G-code missing: {path}''' }
    base = None.rstrip('/')
    boundary = '----aria-boundary'
    body = f'''--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'''.encode() + path.read_bytes() + f'''\r\n--{boundary}--\r\n'''.encode()
    headers = {
        'Content-Type': f'''multipart/form-data; boundary={boundary}''' }
    if api_key:
        headers['X-Api-Key'] = api_key
    
    try:
        _request(f'''{base}/server/files/upload''', method = 'POST', data = body, headers = headers)
        return {
            'ok': True,
            'filename': path.name }
    except urllib.error.HTTPError:
        exc = None
        err = exc.read().decode('utf-8', errors = 'replace')
        del exc
        return None
        None = 
        del exc
        except Exception:
            exc = None
            del exc
            return None
            None = 
            del exc



def start_print(host = None, filename = None, *, api_key):
    base = host.rstrip('/')
    headers = {
        'Content-Type': 'application/json' }
    if api_key:
        headers['X-Api-Key'] = api_key
    payload = json.dumps({
        'filename': filename }).encode()
    
    try:
        _request(f'''{base}/printer/print/start''', method = 'POST', data = payload, headers = headers)
        return {
            'ok': True,
            'filename': filename }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc


