# Source Generated with Decompyle++
# File: scene_presets.cpython-312.pyc (Python 3.12)

'''Named scene bundles — movie mode, etc. (HA scene + device overrides).'''
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p2_flags import scene_presets_enabled
PRESETS_FILE = DATA_DIR / 'scene_presets.json'
DEFAULT_PRESETS: 'dict[str, Any]' = {
    'focus mode': {
        'label': 'Focus mode',
        'description': 'Turn off all lights — minimize distractions',
        'kasa_all': 'off',
        'ha_scene': '',
        'devices': [
            {
                'target': 'light.table_lamp',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_2',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_4',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_5',
                'action': 'off' },
            {
                'target': 'light.merkury_bw904_smart_bulb',
                'action': 'off' },
            {
                'target': 'light.merkury_bw904_smart_bulb_2',
                'action': 'off' }] },
    'relax': {
        'label': 'Relax',
        'description': 'Warm dim table lamp',
        'kasa_all': 'dim',
        'kasa_brightness': 40,
        'ha_scene': '',
        'devices': [
            {
                'target': 'light.table_lamp',
                'action': 'on',
                'brightness': 40,
                'color_temp_kelvin': 2700 }] },
    'movie mode': {
        'label': 'Movie mode',
        'description': 'Family room warm dim — optimal for TV',
        'ha_scene': '',
        'devices': [
            {
                'target': 'light.merkury_bw904_smart_bulb',
                'action': 'on',
                'brightness': 12,
                'color_temp_kelvin': 2200 },
            {
                'target': 'light.merkury_bw904_smart_bulb_2',
                'action': 'on',
                'brightness': 12,
                'color_temp_kelvin': 2200 },
            {
                'target': 'light.table_lamp',
                'action': 'off' }] },
    'work mode': {
        'label': 'Work mode',
        'description': 'Bright cool task lighting',
        'ha_scene': '',
        'devices': [
            {
                'target': 'light.table_lamp',
                'action': 'on',
                'brightness': 85,
                'color_temp_kelvin': 4500 },
            {
                'target': 'light.geeni_bw413_smart_bulb_4',
                'action': 'on',
                'brightness': 80,
                'color_temp_kelvin': 4500 },
            {
                'target': 'light.merkury_bw904_smart_bulb',
                'action': 'on',
                'brightness': 70,
                'color_temp_kelvin': 4000 }] },
    'funky': {
        'label': 'Funky UV',
        'description': 'Deep violet / UV-style glow on color bulbs',
        'devices': [
            {
                'target': 'light.geeni_bw413_smart_bulb',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.geeni_bw413_smart_bulb_2',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.geeni_bw413_smart_bulb_4',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.geeni_bw413_smart_bulb_5',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.merkury_bw904_smart_bulb',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.merkury_bw904_smart_bulb_2',
                'action': 'on',
                'brightness': 75,
                'hs': [
                    275,
                    100] },
            {
                'target': 'light.table_lamp',
                'action': 'on',
                'brightness': 60,
                'hs': [
                    275,
                    100] }] },
    'migraine': {
        'label': 'Migraine',
        'description': 'All lights off except table lamp at 30% warm',
        'devices': [
            {
                'target': 'light.geeni_bw413_smart_bulb',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_2',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_4',
                'action': 'off' },
            {
                'target': 'light.geeni_bw413_smart_bulb_5',
                'action': 'off' },
            {
                'target': 'light.merkury_bw904_smart_bulb',
                'action': 'off' },
            {
                'target': 'light.merkury_bw904_smart_bulb_2',
                'action': 'off' },
            {
                'target': 'light.table_lamp',
                'action': 'on',
                'brightness': 30,
                'color_temp_kelvin': 2700 }] },
    'sunlight': {
        'label': 'Sunlight',
        'description': 'Auto daily — wall, wall1, lamp + living lights; excludes bedrooms',
        'mode': 'sunlight',
        'auto': True,
        'all_lights': True,
        'transition': 45,
        'sunrise_transition': 600,
        'include': [
            'light.table_lamp',
            'light.geeni_bw413_smart_bulb_2',
            'light.geeni_bw413_smart_bulb_3',
            'light.merkury_bw904_smart_bulb_2'],
        'include_names': [
            'wall',
            'wall1',
            'lamp',
            'table lamp'],
        'exclude': [
            'light.geeni_bw413_smart_bulb',
            'light.geeni_bw413_smart_bulb_5',
            'light.merkury_bw904_smart_bulb'],
        'devices': [] } }

def _load():
    if not PRESETS_FILE.is_file():
        return dict(DEFAULT_PRESETS)
    
    try:
        data = json.loads(PRESETS_FILE.read_text(encoding = 'utf-8'))
        merged = dict(DEFAULT_PRESETS)
        if isinstance(data, dict):
            merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return 



def list_presets():
    presets = _load()
    out = []
# WARNING: Decompyle incomplete


def activate_preset(name = None):
    if not scene_presets_enabled():
        return (False, 'Scene presets disabled (JARVIS_SCENE_PRESETS=0)')
    if not name:
        name
    key = ''.strip().lower()
    presets = _load()
    spec = presets.get(key)
    if not spec:
        for k, v in presets.items():
            if not key in k.lower() and k.lower() in key:
                continue
            spec = v
            key = k
            presets.items()
    if not spec or isinstance(spec, dict):
        return (False, f'''Unknown scene preset: {name}''')
    if not None.get('mode'):
        None.get('mode')
    if ''.strip().lower() == 'sunlight':
        activate_sunlight = activate_sunlight
        import jarvis.sunlight_scene
        return activate_sunlight(spec)
    deactivate_sunlight_if_other_preset = deactivate_sunlight_if_other_preset
    import jarvis.sunlight_scene
    deactivate_sunlight_if_other_preset(key)
    messages = []
    failures = []
    had_steps = False
    if not spec.get('ha_scene'):
        spec.get('ha_scene')
    scene = ''.strip()
    if scene:
        had_steps = True
        activate_scene = activate_scene
        ha_enabled = ha_enabled
        import jarvis.home_assistant
        if ha_enabled():
            (ok, msg) = activate_scene(scene)
            if ok:
                messages.append(msg)
            else:
                failures.append(f'''Scene: {msg}''')
        else:
            failures.append('Scene: Home Assistant not configured')
    control_device = control_device
    import jarvis.device_router
    if not spec.get('devices'):
        spec.get('devices')
    for step in []:
        if not isinstance(step, dict):
            continue
        if not step.get('target'):
            step.get('target')
        target = ''.strip()
        if not step.get('action'):
            step.get('action')
        action = 'on'.strip()
        if not target:
            continue
        had_steps = True
        (ok, msg, backend) = control_device(target, action, brightness = step.get('brightness'), rgb = step.get('rgb'), hs = step.get('hs'), color_temp_kelvin = step.get('color_temp_kelvin'), color_name = step.get('color_name'), transition = step.get('transition'))
        if ok:
            messages.append(f'''[{backend}] {msg}''')
            continue
        if not backend:
            backend
        failures.append(f'''[{'none'}] {target}: {msg}''')
    if not spec.get('label'):
        spec.get('label')
    label = key
    if not spec.get('kasa_all'):
        spec.get('kasa_all')
    kasa_all = ''.strip().lower()
    if kasa_all:
        had_steps = True
        control_all = control_all
        import jarvis.kasa_devices
        if kasa_all == 'off':
            (ok, msg) = control_all('off')
            if ok:
                messages.append(msg)
            else:
                failures.append(f'''Kasa: {msg}''')
        elif kasa_all in ('dim', 'on'):
            if not spec.get('kasa_brightness'):
                spec.get('kasa_brightness')
            bright = int(40)
            (ok, msg) = control_all('on', brightness = bright)
            if ok:
                messages.append(msg)
            else:
                failures.append(f'''Kasa: {msg}''')
    if not had_steps:
        return (True, f'''Activated **{label}** (no device steps configured yet).''')
    if not None:
        detail = '; '.join(failures) if failures else 'All steps failed'
        return (False, f'''**{label}** failed: {detail}''')
    result = f'''{label}:** ''' + ' '.join(messages)
    if failures:
        result += f''' Failed: {'; '.join(failures)}'''
    
    try:
        _load_chat_settings = _load_chat_settings
        _write_chat_settings = _write_chat_settings
        import jarvis.config
        data = _load_chat_settings()
        data.setdefault('scene_state', { })['active_preset'] = key
        _write_chat_settings(data)
        return (True, result)
    except Exception:
        return (True, result)


