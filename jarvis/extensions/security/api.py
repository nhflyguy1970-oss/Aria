# Source Generated with Decompyle++
# File: api.cpython-312.pyc (Python 3.12)

'''Security & presence HTTP API.'''
from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse
from jarvis.auth import client_ip

def register_routes(app = None, assistant = None):
    lock_status_route = (lambda request = None: face_status = face_statusimport jarvis.security.face_authlock_status = lock_statusimport jarvis.security.pin_lockif not request.headers.get('X-Jarvis-Session'):
request.headers.get('X-Jarvis-Session')token = ''.strip()# WARNING: Decompyle incomplete
)()
    session_touch = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    pin_setup = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    unlock = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    lock_route = (lambda : lock_status = lock_statusrevoke_all_sessions = revoke_all_sessionsimport jarvis.security.pin_lockrevoked = revoke_all_sessions()# WARNING: Decompyle incomplete
)()
    trusted_list = (lambda : list_trusted = list_trustedimport jarvis.security.trusted_devices{
'ok': True,
'devices': list_trusted() })()
    trusted_revoke = (lambda device_id = app.post('/api/security/lock'): revoke_device = revoke_deviceimport jarvis.security.trusted_devices{
'ok': revoke_device(device_id) })()
    face_enroll = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    face_verify_route = (lambda request = None: pass# WARNING: Decompyle incomplete
)()
    brain_mode_route = (lambda : brain_mode_status = brain_mode_statusimport jarvis.security.brain_mode# WARNING: Decompyle incomplete
)()
    tools_status_route = (lambda : tools_status = tools_statusimport jarvis.security.tools_status{
'ok': True,
'tools': tools_status() })()
    desktop_shells_route = (lambda : electron_status = statusimport jarvis.electron_shellgui_mode = gui_modeimport jarvis.gui_launcherpyside_status = statusimport jarvis.pyside_shell{
'ok': True,
'mode': gui_mode(),
'electron': electron_status(),
'pyside': pyside_status() })()
    cloud_live_route = (lambda : cloud_live_status = cloud_live_statusimport jarvis.cloud_live_voice# WARNING: Decompyle incomplete
)()
    gestures_status_route = (lambda : DATA_DIR = DATA_DIRimport jarvis.configfloating_panels_enabled = floating_panels_enabledgestures_enabled = gestures_enabledimport jarvis.p4_flagscpu_gestures_enabled = cpu_gestures_enabledimport jarvis.p5_flagsimport jsonimport ospath = DATA_DIR / 'security' / 'gestures.json'saved = {
'mode': 'off',
'calibration': { } }if path.is_file():
try:
saved = json.loads(path.read_text(encoding = 'utf-8'))if not saved.get('mode'):
saved.get('mode')if not saved.get('calibration'):
saved.get('calibration')if not os.getenv('JARVIS_GESTURE_SENSITIVITY', '1.35'):
os.getenv('JARVIS_GESTURE_SENSITIVITY', '1.35'){
'ok': True,
'gestures_enabled': gestures_enabled(),
'floating_panels': floating_panels_enabled(),
'cpu_gestures': cpu_gestures_enabled(),
'mode': 'off',
'calibration': { },
'sensitivity': float('1.35'),
'help': 'Detach a panel with ⧉, start camera on Presence, set Control mode. Fist on a floating panel + move wrist to drag; pinch to click.' }except Exception:
continue)()
    gestures_settings_get = (lambda : DATA_DIR = DATA_DIRimport jarvis.configimport jsonpath = DATA_DIR / 'security' / 'gestures.json'if not path.is_file():
{
'ok': True,
'mode': 'off',
'calibration': { } }# WARNING: Decompyle incomplete
)()
    gestures_settings_set = (lambda request = app.get('/api/security/gestures/status'): pass# WARNING: Decompyle incomplete
)()

