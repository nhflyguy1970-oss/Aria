# Source Generated with Decompyle++
# File: kasa_devices.cpython-312.pyc (Python 3.12)

'''TP-Link Kasa smart plug/bulb control (optional python-kasa).'''
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p2_flags import kasa_enabled
log = logging.getLogger('jarvis.kasa')
STORE = DATA_DIR / 'kasa_devices.json'

def _available():
    if not kasa_enabled():
        return False
    
    try:
        import kasa
        return True
    except ImportError:
        return False



def _load_store():
    if not STORE.is_file():
        return {
            'devices': [] }
    
    try:
        return json.loads(STORE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save_store(data = None):
    STORE.parent.mkdir(parents = True, exist_ok = True)
    STORE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def list_devices():
    if not _load_store().get('devices'):
        _load_store().get('devices')
    return list([])


def _run(coro):
    return asyncio.run(coro)


async def _discover_async(timeout = None):
    pass
# WARNING: Decompyle incomplete


def discover(*, timeout):
    if not _available():
        return {
            'ok': False,
            'error': 'Kasa disabled or python-kasa not installed (pip install python-kasa)' }
    
    try:
        devices = _run(_discover_async(timeout))
        _save_store({
            'devices': devices,
            'discovered': True })
        return {
            'ok': True,
            'devices': devices,
            'count': len(devices) }
    except Exception:
        exc = None
        log.warning('Kasa discover failed: %s', exc)
        del exc
        return None
        None = 
        del exc



def _match_device(target = None):
    if not target:
        target
    needle = ''.strip().lower()
    if not needle:
        return None
    for dev in list_devices():
        if not dev.get('alias'):
            dev.get('alias')
        alias = ''.lower()
        if not dev.get('host'):
            dev.get('host')
        host = ''.lower()
        if not needle in alias and alias in needle and needle == host:
            continue
        
        return list_devices(), dev


async def _control_async(host = None, action = None, *, brightness, hue, saturation):
    pass
# WARNING: Decompyle incomplete


def control_device(target = None, action = None, *, brightness, hue, saturation):
    if not _available():
        return (False, 'Kasa not available')
    dev = _match_device(target)
    if not dev:
        return (False, f'''No Kasa device matches \'{target}\'''')
    
    try:
        return _run(_control_async(dev['host'], action, brightness = brightness, hue = hue, saturation = saturation))
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def set_color(target = None, hue = None, saturation = None, *, brightness):
    '''Set bulb color (HSV). Turns device on.'''
    return control_device(target, 'on', brightness = brightness, hue = hue, saturation = saturation)


async def _control_all_async(hosts = None, action = None, *, brightness):
    pass
# WARNING: Decompyle incomplete


def control_all(action = None, *, brightness):
    '''Turn all stored Kasa devices on/off or dim (Ada Focus/Relax scenes).'''
    if not _available():
        return (False, 'Kasa not available')
    devices = list_devices()
    if not devices:
        return (False, 'No Kasa devices — run Discover first')
# WARNING: Decompyle incomplete


def status():
    group_devices_by_room = group_devices_by_room
    list_rooms = list_rooms
    import jarvis.kasa_rooms
    devices = list_devices()
    groups = group_devices_by_room(devices)
# WARNING: Decompyle incomplete

