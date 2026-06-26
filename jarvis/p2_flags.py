# Source Generated with Decompyle++
# File: p2_flags.cpython-312.pyc (Python 3.12)

'''P2 feature flags — projects, Kasa, browser agent.'''
from __future__ import annotations
import os

def _env(name = None, default = None):
    return os.getenv(name, default).strip().lower() not in ('0', 'false', 'no', 'off')


def projects_enabled():
    return _env('JARVIS_PROJECTS', '1')


def kasa_enabled():
    return _env('JARVIS_KASA', '0')


def device_router_enabled():
    return _env('JARVIS_DEVICE_ROUTER', '1')


def browser_agent_enabled():
    return _env('JARVIS_BROWSER_AGENT', '1')


def scene_presets_enabled():
    return _env('JARVIS_SCENE_PRESETS', '1')


def p2_flags():
    p1_flags = p1_flags
    import jarvis.p1_flags
    base = p1_flags()
    base.update({
        'projects': projects_enabled(),
        'kasa': kasa_enabled(),
        'device_router': device_router_enabled(),
        'browser_agent': browser_agent_enabled(),
        'scene_presets': scene_presets_enabled() })
    return base

