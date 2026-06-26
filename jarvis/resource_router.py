# Source Generated with Decompyle++
# File: resource_router.cpython-312.pyc (Python 3.12)

'''Resource-aware routing — VRAM/RAM, queues, and safe defaults before heavy work.'''
from __future__ import annotations
import json
import logging
import os
import time
import urllib.request as urllib
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.gpu import detect_gpu, is_low_vram
from jarvis.ml_memory import system_ram_gb, unload_ollama_models
log = logging.getLogger('jarvis')
_SETTINGS_FILE = DATA_DIR / 'resource_settings.json'
_HEAVY_ACTIONS = frozenset({
    'edit_image',
    'generate_meme',
    'inpaint_image',
    'upscale_image',
    'generate_image',
    'generate_video'})
_VRAM_ACTIONS = _HEAVY_ACTIONS
_DEFER_VRAM_PREP = frozenset({
    'generate_image',
    'generate_meme'})

def routing_enabled():
    return os.getenv('JARVIS_RESOURCE_ROUTING', '1').lower() not in ('0', 'false', 'no', 'off')


def strict_queue():
    return os.getenv('JARVIS_RESOURCE_STRICT', '0').lower() in ('1', 'true', 'yes')


def max_media_queue():
    
    try:
        return max(1, int(os.getenv('JARVIS_MEDIA_MAX_QUEUE', '6')))
    except ValueError:
        return 6



def _load_settings():
    if _SETTINGS_FILE.exists():
        
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding = 'utf-8'))
            return {
                'last_success': { } }
        except (json.JSONDecodeError, OSError):
            return {
                'last_success': { } }



def _save_settings(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def record_media_outcome(action = None, *, ok, method, detail, width, height, frames):
    if ok or action not in _HEAVY_ACTIONS:
        return None
    data = _load_settings()
    entry = {
        'at': time.time(),
        'method': method,
        'detail': detail[:200],
        'vram_mb': detect_gpu().get('vram_mb'),
        'low_vram': is_low_vram(10240) }
    if width:
        entry['width'] = int(width)
    if height:
        entry['height'] = int(height)
    if frames:
        entry['frames'] = int(frames)
    data.setdefault('last_success', { })[action] = entry
    _save_settings(data)


def suggested_for_action(action = None):
    if not _load_settings().get('last_success', { }).get(action):
        _load_settings().get('last_success', { }).get(action)
    return dict({ })


def ollama_loaded_models():
    host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434').rstrip('/')
# WARNING: Decompyle incomplete


def ram_available_gb():
    
    try:
        mem_total = 0
        mem_avail = 0
        f = open('/proc/meminfo', encoding = 'utf-8')
        for line in f:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
                continue
            if not line.startswith('MemAvailable:'):
                continue
            mem_avail = int(line.split()[1])
        
        try:
            None(None, None)
            if mem_avail:
                return round(mem_avail / 1048576, 1)
            if None:
                return round(mem_total / 1048576, 1)
            return None
            with None:
                if not None:
                    pass
            
            try:
                continue
            except OSError:
                return 0





def snapshot():
    coding_stats = job_stats
    import jarvis.coding_jobs
    busy_state = busy_state
    media_stats = job_stats
    import jarvis.media_jobs
    vram_status = status
    import jarvis.vram_guard
    gpu = detect_gpu()
    vram = vram_status()
    media = busy_state()
    coding = coding_stats()
    loaded = ollama_loaded_models()
    low = bool(vram.get('low_vram'))
    free_vram_mb = free_vram_mb
    import jarvis.gpu
# WARNING: Decompyle incomplete


def _queue_warnings(media = None):
    warnings = []
    if not media.get('pending'):
        media.get('pending')
    pending = int(0)
    if media.get('busy'):
        if not media.get('label'):
            media.get('label')
        label = 'media job'
        warnings.append(f'''GPU media job running: **{label}**. New jobs queue behind it.''')
    if pending > 0:
        warnings.append(f'''{pending} media job(s) already queued — yours will wait in line.''')
    if pending + 1 if media.get('busy') else 0 >= max_media_queue() - 1:
        warnings.append(f'''Media queue is nearly full (max {max_media_queue()}). Cancel stale jobs or wait before starting more renders.''')
    return warnings


def preflight(action = None):
    '''Preflight check for GUI and chat before heavy GPU work.'''
    recommendations = recommendations
    import jarvis.vram_guard
    if not action:
        action
    action = 'video'.strip().lower()
    snap = snapshot()
    media = snap['media_queue']
    warnings = _queue_warnings(media)
    tips = recommendations()[:5]
    adjustments = []
    suggested = { }
    is_video = action in ('video', 'generate_video')
    is_image = action in ('generate_image', 'image')
    if snap['low_vram']:
        if action in _VRAM_ACTIONS or is_video:
            warnings.append('8GB-class GPU detected — Jarvis will unload Ollama before ComfyUI when the job runs.')
        if is_video:
            effective_engine = effective_engine
            effective_animatediff_frames = effective_animatediff_frames
            effective_animatediff_size = effective_animatediff_size
            import jarvis.video_settings
            eng = effective_engine()
            (ad_w, ad_h) = effective_animatediff_size()
            frames = effective_animatediff_frames(4, 8)
            if eng in ('auto', 'animatediff'):
                adjustments.append('AnimateDiff may fall back to Ken Burns if VRAM is tight.')
                tips.insert(0, 'Ken Burns uses less VRAM than AnimateDiff on RX 7600.')
            suggested = {
                'engine': eng,
                'width': ad_w,
                'height': ad_h,
                'frames': min(frames, 16),
                'low_vram_max_frames': 8 }
        if is_image:
            adjustments.append('Prefer SDXL Turbo or 768² — Flux uses more VRAM on 8GB.')
            load_settings = load_settings
            import jarvis.comfyui_settings
            required_vram_for_checkpoint = required_vram_for_checkpoint
            import jarvis.vram_guard
            if not load_settings().get('checkpoint'):
                load_settings().get('checkpoint')
            ck = 'quality'
            need = required_vram_for_checkpoint(ck)
            if not snap.get('free_vram_mb'):
                snap.get('free_vram_mb')
            free = int(0)
            if free and free < need:
                warnings.append(f'''Only **{free}MB** VRAM free — **{ck}** needs ~{need}MB. Jarvis will unload Ollama when the job runs; use **Free VRAM** if generation fails.''')
        if snap['ollama_models_loaded'] > 0:
            warnings.append(f'''Ollama has {snap['ollama_models_loaded']} model(s) loaded — use **Free VRAM** or let Jarvis unload them when the job starts.''')
    if snap['ram_available_gb'] and snap['ram_available_gb'] < 4:
        warnings.append(f'''Low system RAM available ({snap['ram_available_gb']}GB) — close heavy apps if renders fail.''')
    last = suggested_for_action(action if action in _HEAVY_ACTIONS else 'generate_video')
    if last.get('method'):
        tips.insert(0, f'''Last successful {action}: {last['method']} on this machine.''')
    blocked = False
    if not media.get('queue_depth'):
        media.get('queue_depth')
    queue_depth = int(0)
    if strict_queue() and queue_depth >= max_media_queue():
        blocked = True
        warnings.append('Queue full — cancel a job or wait (JARVIS_RESOURCE_STRICT=1).')
    if not blocked:
        not blocked
    return {
        'ok': len(warnings) == 0,
        'allow': not blocked,
        'blocked': blocked,
        'action': action,
        'warnings': warnings,
        'adjustments': adjustments,
        'tips': tips,
        'suggested': suggested,
        'resources': snap }


def check_media_enqueue(action = None):
    '''Gate media job enqueue; returns advisory text and optional block.'''
    pf = preflight(action)
    media = pf['resources']['media_queue']
    if not media.get('pending'):
        media.get('pending')
    pending = int(0)
    position = pending + 1 if media.get('busy') else 0 + 1
    parts = []
    if pf['adjustments']:
        parts.append(' '.join(pf['adjustments'][:2]))
    if routing_enabled() and action in _VRAM_ACTIONS and pf['resources']['low_vram']:
        parts.append('Ollama will be unloaded before this job starts.')
    return {
        'allowed': pf['allow'],
        'blocked': pf['blocked'],
        'message': pf['warnings'][0] if pf['blocked'] else '',
        'warnings': pf['warnings'],
        'adjustments': pf['adjustments'],
        'queue_position': position,
        'advisory': ' '.join(parts).strip() }


def prepare_for_media_job(action = None):
    '''Run right before a queued media job executes.'''
    if not routing_enabled():
        return {
            'skipped': True }
    if None not in _VRAM_ACTIONS:
        return {
            'skipped': True }
    if None in _DEFER_VRAM_PREP:
        return {
            'skipped': True,
            'deferred': True,
            'action': action }
    prepare_for_comfyui = prepare_for_comfyui
    vram_guard_enabled = vram_guard_enabled
    import jarvis.vram_guard
    result = {
        'action': action,
        'prepared': False }
    if vram_guard_enabled():
        prep = prepare_for_comfyui()
        result.update(prep)
        result['prepared'] = True
        return result
    if None(10240):
        unloaded = unload_ollama_models()
        result['unloaded_ollama'] = unloaded
        result['prepared'] = bool(unloaded)
    return result


def should_prefer_ken_burns():
    '''Extra guard beyond video_settings when Ollama still holds GPU.'''
    if not routing_enabled():
        return False
    if not is_low_vram(10240):
        return False
    if ollama_loaded_models() and detect_gpu().get('ollama_using_gpu'):
        return True
    return False


def chat_busy_hint():
    snap = snapshot()
    media = snap['media_queue']
    if not media.get('busy') and media.get('pending'):
        return None
    if not media.get('label'):
        media.get('label')
    label = 'media render'
    return f'''Note: GPU queue busy ({label}) — chat still works; heavy image/video jobs are serialized.'''


def status_line():
    snap = snapshot()
    parts = []
    if snap['vram_mb']:
        parts.append(f'''{round(snap['vram_mb'] / 1024, 1)}GB VRAM''')
    media = snap['media_queue']
    if media.get('busy'):
        if not media.get('label'):
            media.get('label')
        parts.append(f'''busy: {'media'}''')
    elif media.get('pending'):
        parts.append(f'''queue: {media['pending']}''')
    if snap['ollama_models_loaded']:
        parts.append(f'''Ollama×{snap['ollama_models_loaded']}''')
    if parts:
        return ' · '.join(parts)

