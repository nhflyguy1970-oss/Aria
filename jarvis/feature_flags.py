# Source Generated with Decompyle++
# File: feature_flags.cpython-312.pyc (Python 3.12)

'''Central JARVIS_* feature flags for optional P0+ stacks.'''
from __future__ import annotations
import os

def _env(name = None, default = None):
    return os.getenv(name, default).strip().lower() not in ('0', 'false', 'no', 'off')


def planner_enabled():
    return _env('JARVIS_PLANNER', '1')


def tool_permissions_enabled():
    return _env('JARVIS_TOOL_PERMISSIONS', '1')


def curated_news_enabled():
    return _env('JARVIS_CURATED_NEWS', '1')


def dashboard_enabled():
    return _env('JARVIS_DASHBOARD', '1')


def system_monitor_enabled():
    return _env('JARVIS_SYSTEM_MONITOR', '1')


def ha_fuzzy_enabled():
    return _env('JARVIS_HA_FUZZY', '1')


def voice_overlay_enabled():
    return _env('JARVIS_VOICE_OVERLAY', '1')


def checklist_enabled():
    return _env('JARVIS_CHECKLIST', '1')


def all_flags():
    return {
        'planner': planner_enabled(),
        'tool_permissions': tool_permissions_enabled(),
        'curated_news': curated_news_enabled(),
        'dashboard': dashboard_enabled(),
        'system_monitor': system_monitor_enabled(),
        'ha_fuzzy': ha_fuzzy_enabled(),
        'voice_overlay': voice_overlay_enabled(),
        'checklist': checklist_enabled() }

