# Source Generated with Decompyle++
# File: build123d_runner.cpython-312.pyc (Python 3.12)

'''build123d parametric CAD runner.'''
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
HELLO_CUBE_SCRIPT = '\nfrom build123d import BuildPart, Box, export_stl\nwith BuildPart() as p:\n    Box(10, 10, 10)\nexport_stl(p.part, r"__OUT__")\n'

def build123d_available():
    
    try:
        import build123d
        return True
    except ImportError:
        return False



def hello_cube(dest = None):
    if not build123d_available():
        return {
            'ok': False,
            'error': 'build123d not installed (pip install build123d)' }
    dest = None(dest)
    dest.parent.mkdir(parents = True, exist_ok = True)
    script = HELLO_CUBE_SCRIPT.replace('__OUT__', str(dest).replace('\\', '\\\\'))
    return _run_script_text(script, dest)


def run_script_file(script_path = None, stl_out = None):
    if not build123d_available():
        return {
            'ok': False,
            'error': 'build123d not installed' }
    script_path = None(script_path)
    stl_out = Path(stl_out)
    stl_out.parent.mkdir(parents = True, exist_ok = True)
    patched = script_path.read_text(encoding = 'utf-8')
    if 'export_stl' not in patched:
        patched += f'''\nfrom build123d import export_stl\nexport_stl(part, r"{stl_out}")\n'''
    return _run_script_text(patched, stl_out)


def _run_script_text(script = None, stl_out = None):
    tmp = tempfile.NamedTemporaryFile('w', suffix = '.py', delete = False, encoding = 'utf-8')
    tmp.write(script)
    tmp_path = tmp.name
    None(None, None)
# WARNING: Decompyle incomplete

