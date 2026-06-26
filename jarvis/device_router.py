# Source Generated with Decompyle++
# File: device_router.cpython-312.pyc (Python 3.12)

'''Unified friendly-name routing — Home Assistant entity or Kasa device.'''
from __future__ import annotations
from typing import Any
from jarvis.p2_flags import device_router_enabled, kasa_enabled

def control_device(target = None, action = None, **kwargs):
    '''Returns (ok, message, backend) where backend is ha|kasa|none.'''
    if not target:
        target
    target = ''.strip()
    if not action:
        action
    action = 'on'.strip().lower()
    if not target:
        return (False, 'No device target specified.', 'none')
    resolve_targets = resolve_targets
    import jarvis.room_aliases
    targets = resolve_targets(target)
# WARNING: Decompyle incomplete


def list_unified_devices():
    out = []
    
    try:
        ha_enabled = ha_enabled
        list_states = list_states
        import jarvis.home_assistant
        if ha_enabled():
            for ent in list_states(refresh = False)[:80]:
                if not ent.get('attributes', { }).get('friendly_name'):
                    ent.get('attributes', { }).get('friendly_name')
                out.append({
                    'name': ent.get('entity_id'),
                    'id': ent.get('entity_id'),
                    'backend': 'ha',
                    'state': ent.get('state') })
        if kasa_enabled():
            list_devices = list_devices
            import jarvis.kasa_devices
            for dev in list_devices():
                if not dev.get('alias'):
                    dev.get('alias')
                out.append({
                    'name': dev.get('host'),
                    'id': dev.get('host'),
                    'backend': 'kasa',
                    'state': 'on' if dev.get('is_on') else 'off' })
        return out
    except Exception:
        continue


