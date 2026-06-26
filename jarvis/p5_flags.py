# Source Generated with Decompyle++
# File: p5_flags.cpython-312.pyc (Python 3.12)

'''P5 feature flags — integration, learning, ops polish.'''
from __future__ import annotations
import os

def _env(name = None, default = None):
    return os.getenv(name, default).strip().lower() not in ('0', 'false', 'no', 'off')


def cad_teaching_enabled():
    return _env('JARVIS_CAD_TEACHING', '1')


def voice_cheatsheet_enabled():
    return _env('JARVIS_VOICE_CHEATSHEET', '1')


def usb_printer_enabled():
    return _env('JARVIS_USB_PRINTER', '1')


def cpu_gestures_enabled():
    return _env('JARVIS_CPU_GESTURES', '1')


def cad_export_enabled():
    return _env('JARVIS_CAD_EXPORT', '1')


def p5_flags():
    p4_flags = p4_flags
    import jarvis.p4_flags
    base = p4_flags()
    base.update({
        'cad_teaching': cad_teaching_enabled(),
        'voice_cheatsheet': voice_cheatsheet_enabled(),
        'usb_printer': usb_printer_enabled(),
        'cpu_gestures': cpu_gestures_enabled(),
        'cad_export': cad_export_enabled() })
    return base

