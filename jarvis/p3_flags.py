# Source Generated with Decompyle++
# File: p3_flags.cpython-312.pyc (Python 3.12)

'''P3 feature flags — CAD lab and 3D printing.'''
from __future__ import annotations
import os

def _env(name = None, default = None):
    return os.getenv(name, default).strip().lower() not in ('0', 'false', 'no', 'off')


def cad_enabled():
    return _env('JARVIS_CAD', '1')


def printer_enabled():
    return _env('JARVIS_PRINTER', '1')


def meshy_cad_enabled():
    return _env('JARVIS_MESHY_CAD', '1')


def p3_flags():
    p2_flags = p2_flags
    import jarvis.p2_flags
    base = p2_flags()
    base.update({
        'cad': cad_enabled(),
        'printer': printer_enabled(),
        'meshy_cad': meshy_cad_enabled() })
    return base

