# Source Generated with Decompyle++
# File: slicer.cpython-312.pyc (Python 3.12)

'''Slicer detection and headless G-code export.'''
from __future__ import annotations
import glob
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.engineering.printer_profiles import get_model
SETTINGS_FILE = DATA_DIR / 'printer_settings.json'

def _load_settings():
    if not SETTINGS_FILE.is_file():
        return { }
    
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def save_settings(data = None):
    SETTINGS_FILE.parent.mkdir(parents = True, exist_ok = True)
# WARNING: Decompyle incomplete


def _orca_search_paths():
    paths = []
    if not os.getenv('JARVIS_ORCASLICER_PATH'):
        os.getenv('JARVIS_ORCASLICER_PATH')
    env = ''.strip()
    if env:
        paths.append(env)
    for name in ('orcaslicer', 'orca-slicer', 'OrcaSlicer'):
        w = shutil.which(name)
        if not w:
            continue
        paths.append(w)
    home = Path.home()
    for pattern in (str(home / 'bin' / 'OrcaSlicer*'), str(home / 'Applications' / 'OrcaSlicer*.AppImage'), str(home / '.local' / 'bin' / 'orcaslicer'), str(home / 'Downloads' / 'OrcaSlicer*.AppImage'), '/opt/OrcaSlicer/orcaslicer', '/usr/bin/orcaslicer'):
        for hit in glob.glob(pattern):
            if not Path(hit).is_file():
                continue
            paths.append(hit)
    
    try:
        proc = subprocess.run([
            'flatpak',
            'which',
            'com.softfever.OrcaSlicer'], capture_output = True, text = True, timeout = 5)
        if proc.returncode == 0 and proc.stdout.strip():
            paths.append('flatpak run com.softfever.OrcaSlicer')
        return list(dict.fromkeys(paths))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        continue



def _orca_system_roots():
    roots = [
        Path.home() / '.config' / 'OrcaSlicer' / 'system',
        Path.home() / '.var' / 'app' / 'com.softfever.OrcaSlicer' / 'config' / 'OrcaSlicer' / 'system']
    if not os.getenv('JARVIS_ORCA_SYSTEM_DIR'):
        os.getenv('JARVIS_ORCA_SYSTEM_DIR')
    custom = ''.strip()
    if custom:
        roots.insert(0, Path(custom))
# WARNING: Decompyle incomplete


def find_orca_profile_settings(printer_model = None):
    '''Return --load-settings paths for a known printer model.'''
    pass
# WARNING: Decompyle incomplete


def detect_slicers():
    pass
# WARNING: Decompyle incomplete


def slicer_status():
    slicers = detect_slicers()
    settings = _load_settings()
    if not settings.get('default_slicer'):
        settings.get('default_slicer')
# WARNING: Decompyle incomplete


def _run_slicer_cmd(cmd = None, *, timeout):
    if cmd[0].startswith('flatpak run'):
        parts = cmd[0].split()
        full = parts + cmd[1:]
    else:
        full = cmd
    return subprocess.run(full, capture_output = True, text = True, timeout = timeout)


def slice_stl(stl_path = None, gcode_path = None, *, slicer_id, printer_model):
    stl_path = Path(stl_path)
    if not stl_path.is_file():
        return {
            'ok': False,
            'error': f'''STL missing: {stl_path}''' }
# WARNING: Decompyle incomplete

