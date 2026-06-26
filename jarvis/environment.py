# Source Generated with Decompyle++
# File: environment.cpython-312.pyc (Python 3.12)

'''Unified environment snapshot — time, profile, services, disk, resources.'''
from __future__ import annotations
import os
import shutil
import time
from datetime import datetime
from typing import Any
from jarvis.config import DATA_DIR

def disk_free_gb(path = None):
    if not path:
        path
    target = str(DATA_DIR)
    
    try:
        usage = shutil.disk_usage(target)
        return round(usage.free / 1073741824, 1)
    except OSError:
        return 0



def active_profile_name():
    
    try:
        active_profile = active_profile
        import jarvis.profiles
        if not active_profile().get('name'):
            active_profile().get('name')
            if not active_profile().get('id'):
                active_profile().get('id')
        return 'default'
    except Exception:
        return 



def snapshot(*, include_resources):
    '''Machine + Jarvis context for briefing, routing, and /api/environment.'''
    get_status = get_status
    import jarvis.services
    now = datetime.now()
    services = get_status(force = False)
    if not services.get('services'):
        services.get('services')
    if not services.get('ollama'):
        services.get('ollama')
    payload = {
        'timestamp': now.isoformat(timespec = 'seconds'),
        'date': now.date().isoformat(),
        'time': now.strftime('%H:%M'),
        'profile': active_profile_name(),
        'disk_free_gb': disk_free_gb(),
        'data_dir': str(DATA_DIR),
        'services_ready': bool(services.get('ready')),
        'services': [],
        'ollama_running': bool({ }.get('running')) }
    if include_resources:
        
        try:
            resource_snapshot = snapshot
            import jarvis.resource_router
            payload['resources'] = resource_snapshot()
            
            try:
                detect_gpu = detect_gpu
                free_vram_mb = free_vram_mb
                import jarvis.gpu
                gpu = detect_gpu()
                if gpu.get('vram_mb', 0):
                    gpu.get('vram_mb', 0)
                payload['gpu'] = {
                    'name': gpu.get('name'),
                    'vram_mb': gpu.get('vram_mb'),
                    'free_vram_mb': free_vram_mb(),
                    'low_vram': gpu.get('vram_mb', 0) <= 10240 }
                return payload
                except Exception:
                    payload['resources'] = { }
                    continue
            except Exception:
                payload['gpu'] = { }
                return payload




def briefing_line():
    '''One-line environment hint for morning briefing.'''
    snap = snapshot(include_resources = False)
    parts = [
        f'''Profile: **{snap['profile']}**''']
    if snap.get('disk_free_gb'):
        parts.append(f'''{snap['disk_free_gb']}GB free on data disk''')
    if not snap.get('gpu'):
        snap.get('gpu')
    gpu = { }
    if gpu.get('free_vram_mb'):
        parts.append(f'''{gpu['free_vram_mb']}MB VRAM free''')
    elif gpu.get('vram_mb'):
        parts.append(f'''{gpu['vram_mb']}MB GPU''')
    if not snap.get('services'):
        snap.get('services')
# WARNING: Decompyle incomplete

