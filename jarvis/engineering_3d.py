# Source Generated with Decompyle++
# File: engineering_3d.cpython-312.pyc (Python 3.12)

'''3D engineering lab — OpenSCAD parametric design, STL library, mesh stats.'''
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
ENGINEERING_DIR = DATA_DIR / 'engineering'
META_FILE = ENGINEERING_DIR / 'models.json'
DEFAULT_CUBE = '// Jarvis parametric cube — edit dimensions\n$fn = 48;\nsize = [40, 40, 20];\ncube(size, center=true);\n'
CAD_SYSTEM_PROMPT = 'You are a mechanical CAD assistant specializing in OpenSCAD for FDM 3D printing. Output ONLY valid OpenSCAD for ONE printable part. Rules: All dimensions in millimeters as parametric variables at the top. Minimum wall thickness 1.2mm (2mm for load-bearing parts). Part must sit flat on the print bed (Z=0); avoid floating geometry. Avoid unsupported overhangs beyond 45°; use chamfers or teardrop holes. Use $fn = 48 for curves (32 for large flat features). Use union, difference, hull, linear_extrude, rotate_extrude. Slip fit clearance +0.2mm; loose fit +0.4mm. No prose, no numbered options. Single ```openscad code fence only.'
CAD_EDIT_SYSTEM_PROMPT = 'You are a mechanical CAD assistant editing OpenSCAD for FDM 3D printing. Return the COMPLETE updated OpenSCAD (not a diff). Keep parametric variables; preserve printability (walls ≥1.2mm, bed contact, clearances). No prose, no options. Single ```openscad fence only.'

def default_engineering_llm():
    '''LLM callable for design/edit (uses engineering_model + custom system prompts).'''
    pass
# WARNING: Decompyle incomplete


def engineering_lab_status():
    '''OpenSCAD + AI model info for the Engineering tab.'''
    engineering_model = engineering_model
    import jarvis.llm
    meshy_available = meshy_available
    import jarvis.meshy_client
    st = openscad_status()
    st['engineering_model'] = engineering_model()
    st['meshy_available'] = meshy_available()
    st['design_engines'] = [
        'openscad',
        'meshy'] if meshy_available() else [
        'openscad']
    return st


def _ensure_dir():
    ENGINEERING_DIR.mkdir(parents = True, exist_ok = True)
    return ENGINEERING_DIR


def _load_meta():
    if not META_FILE.is_file():
        return {
            'models': [] }
    
    try:
        return json.loads(META_FILE.read_text(encoding = 'utf-8'))
    except Exception:
        return 



def _save_meta(data = None):
    _ensure_dir()
    META_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')

FLATPAK_OPENSCAD_REFS = ('org.openscad.OpenSCAD', 'org.openscad.openscad-nightly')

def _flatpak_openscad_ref():
    if not shutil.which('flatpak'):
        return None
    for ref in FLATPAK_OPENSCAD_REFS:
        r = subprocess.run([
            'flatpak',
            'info',
            ref], capture_output = True, timeout = 8, check = False)
        if r.returncode == 0:
            
            return FLATPAK_OPENSCAD_REFS, ref
    return None
    except Exception:
        continue


def _flatpak_export_bin(ref = None):
    for base in (Path('/var/lib/flatpak/exports/bin'), Path.home() / '.local/share/flatpak/exports/bin'):
        for name in (ref, ref.split('.')[-1]):
            candidate = base / name
            if not candidate.is_file():
                continue
            
            
            return (Path('/var/lib/flatpak/exports/bin'), Path.home() / '.local/share/flatpak/exports/bin'), (ref, ref.split('.')[-1]), str(candidate)


def _flatpak_filesystem_grant():
    explicit = os.getenv('JARVIS_OPENSCAD_FLATPAK_FS', '').strip()
    if explicit:
        return explicit
    
    try:
        return str(DATA_DIR.resolve().parent)
    except OSError:
        return 



def _path_under_home(path = None):
    
    try:
        home = Path.home().resolve()
        resolved = path.resolve()
        if not resolved == home:
            resolved == home
        return home in resolved.parents
    except OSError:
        return False



def openscad_path():
    '''Resolve native OpenSCAD binary (apt/snap), not Flatpak.'''
    env_path = os.getenv('JARVIS_OPENSCAD_BIN', '').strip()
    if env_path and Path(env_path).is_file():
        return env_path
    found = None.which('openscad')
    if found:
        return found
    for candidate in None:
        if not Path(candidate).is_file():
            continue
        
        return None, candidate


def openscad_render_cmd(scad_path = None, stl_path = None):
