# Source Generated with Decompyle++
# File: cad_deps.cpython-312.pyc (Python 3.12)

'''CAD toolchain dependency status.'''
from __future__ import annotations
import importlib.util as importlib
import shutil
from typing import Any

def _has_module(name = None):
    return importlib.util.find_spec(name) is not None


def cad_status():
    openscad = shutil.which('openscad')
    build123d = _has_module('build123d')
    meshy = False
    
    try:
        meshy_available = meshy_available
        import jarvis.meshy_client
        meshy = meshy_available()
        cad_enabled = cad_enabled
        meshy_cad_enabled = meshy_cad_enabled
        printer_enabled = printer_enabled
        import jarvis.p3_flags
        if meshy_cad_enabled():
            meshy_cad_enabled()
        if not openscad:
            openscad
        if not openscad:
            openscad
            if not build123d:
                build123d
        return {
            'enabled': cad_enabled(),
            'printer_enabled': printer_enabled(),
            'meshy_cad': meshy,
            'openscad': bool(openscad),
            'openscad_path': '',
            'build123d': build123d,
            'meshy': meshy,
            'ready': bool(meshy) }
    except Exception:
        continue


