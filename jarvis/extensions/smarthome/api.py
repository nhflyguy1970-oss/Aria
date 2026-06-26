# Source Generated with Decompyle++
# File: api.cpython-312.pyc (Python 3.12)

'''Smart home API.'''
from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse

def register_routes(app = None, assistant = None):
    kasa_status = (lambda : status = statusimport jarvis.kasa_devices# WARNING: Decompyle incomplete
)()
    kasa_devices = (lambda : status = statusimport jarvis.kasa_devices# WARNING: Decompyle incomplete
)()
    kasa_install_route = (lambda : ensure_kasa = ensure_kasaimport jarvis.kasa_installensure_kasa(install = True))()
    kasa_discover_route = (lambda : discover = discoverimport jarvis.kasa_devicesdiscover())()
    kasa_control_route = (lambda request = app.post('/api/kasa/install'): pass# WARNING: Decompyle incomplete
)()
    unified_devices = (lambda : list_unified_devices = list_unified_devicesimport jarvis.device_router{
'ok': True,
'devices': list_unified_devices() })()
    scene_presets_list = (lambda : list_presets = list_presetsimport jarvis.scene_presets{
'ok': True,
'presets': list_presets() })()
    scene_presets_activate = (lambda preset_id = app.get('/api/devices'): activate_preset = activate_presetimport jarvis.scene_presets(ok_flag, msg) = activate_preset(preset_id){
'ok': ok_flag,
'message': msg })()

