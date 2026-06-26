# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Smart home P2 handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.p2_flags import device_router_enabled, kasa_enabled, scene_presets_enabled
from jarvis.response import err, ok
scene_recall = (lambda assistant = None, params = None, message = register_action('scene_recall', module = 'automation', description = 'Activate scene preset'): if not scene_presets_enabled():
err('Scene presets disabled.', module = 'automation')activate_preset = activate_presetimport jarvis.scene_presetsif not params.get('preset'):
params.get('preset')preset = ''.strip()if not preset:
m = re.search('(movie mode|work mode)', message, re.I)preset = m.group(1) if m else message(ok_flag, msg) = activate_preset(preset)if not ok_flag:
err(msg, module = 'automation')None(msg, module = 'automation', type = 'scene_recall'))()
kasa_discover = (lambda assistant = None, params = None, message = register_action('kasa_discover', module = 'automation', description = 'Discover Kasa devices'): if not kasa_enabled():
err('Kasa disabled (JARVIS_KASA=0).', module = 'automation')discover = discoverimport jarvis.kasa_devicesresult = discover()if not result.get('ok'):
err(result.get('error', 'Discover failed'), module = 'automation')n = None.get('count', 0)ok(f'''Found **{n}** Kasa device(s).''', module = 'automation', type = 'kasa', devices = result.get('devices')))()
device_list = (lambda assistant = None, params = None, message = register_action('device_list', info = True, module = 'automation', description = 'List HA + Kasa devices'): if not device_router_enabled():
err('Device router disabled.', module = 'automation')list_unified_devices = list_unified_devicesimport jarvis.device_routerdevices = list_unified_devices()if not devices:
ok('No devices found. Configure HA or run Kasa discover.', module = 'automation')# WARNING: Decompyle incomplete
)()
