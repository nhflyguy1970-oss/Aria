# Source Generated with Decompyle++
# File: trusted_devices.cpython-312.pyc (Python 3.12)

'''Trusted LAN device list — skip re-auth on known clients.'''
from __future__ import annotations
import json
import time
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p4_flags import trusted_lan_enabled
STORE = DATA_DIR / 'security' / 'trusted_devices.json'

def _load():
    if not STORE.is_file():
        return {
            'devices': [] }
    
    try:
        return json.loads(STORE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save(data = None):
    STORE.parent.mkdir(parents = True, exist_ok = True)
    STORE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def list_trusted():
    if not _load().get('devices'):
        _load().get('devices')
    return list([])


def is_trusted(device_id = None, *, client_ip):
    if not trusted_lan_enabled():
        return False
    if not device_id:
        device_id
    did = ''.strip()
    if not did:
        return False
    if not client_ip:
        client_ip
    ip = ''.strip()
    for row in list_trusted():
        if row.get('id') != did:
            continue
        if not row.get('ip'):
            row.get('ip')
        stored_ip = ''.strip()
        if not stored_ip or ip:
            list_trusted()
            return False
        if not stored_ip == ip:
            continue
        return True
    return False


def trust_device(device_id = None, *, label, client_ip):
    if not device_id:
        device_id
    did = ''.strip()
    if not did:
        raise ValueError('device_id required')
    if not client_ip:
        client_ip
    ip = ''.strip()
    if not ip:
        raise ValueError('client_ip required')
    data = _load()
    if not data.get('devices'):
        data.get('devices')
# WARNING: Decompyle incomplete


def revoke_device(device_id = None):
    data = _load()
    if not data.get('devices'):
        data.get('devices')
    before = len([])
    if not data.get('devices'):
        data.get('devices')
# WARNING: Decompyle incomplete

