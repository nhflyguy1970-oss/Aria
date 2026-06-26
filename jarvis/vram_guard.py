# Source Generated with Decompyle++
# File: vram_guard.cpython-312.pyc (Python 3.12)

'''Coordinate GPU VRAM between Ollama, ComfyUI, and PyTorch on 8GB cards.'''
from __future__ import annotations
import os
import time
from jarvis.gpu import detect_gpu, free_vram_mb, is_low_vram
from jarvis.ml_memory import release_torch_memory, unload_ollama_models
CHECKPOINT_VRAM_REQUIRED_MB: 'dict[str, int]' = {
    'flux': 7800,
    'quality': 5600,
    'fast': 4200 }
CHECKPOINT_VRAM_INCREMENTAL_MB: 'dict[str, int]' = {
    'flux': 1800,
    'quality': 1200,
    'fast': 1000 }

def vram_guard_enabled():
    return os.getenv('JARVIS_VRAM_GUARD', '1').lower() not in ('0', 'false', 'no', 'off')


def _checkpoint_key(checkpoint = None):
    load_settings = load_settings
    import jarvis.comfyui_settings
    if not checkpoint:
        checkpoint
        if not load_settings().get('checkpoint'):
            load_settings().get('checkpoint')
    return 'quality'.strip().lower()


def required_vram_for_checkpoint(checkpoint = None, *, warm):
    ck = _checkpoint_key(checkpoint)
    table = CHECKPOINT_VRAM_INCREMENTAL_MB if warm else CHECKPOINT_VRAM_REQUIRED_MB
    fallback = CHECKPOINT_VRAM_INCREMENTAL_MB['quality'] if warm else CHECKPOINT_VRAM_REQUIRED_MB['quality']
    return table.get(ck, fallback)


def _comfyui_warm():
    '''True when ComfyUI is up — checkpoint weights may already occupy VRAM.'''
    
    try:
        is_available = is_available
        import jarvis.comfyui
        _comfy_healthy = _comfy_healthy
        import jarvis.services
        if is_available():
            is_available()
        return _comfy_healthy()
    except Exception:
        return False



def _wait_for_vram(required_mb = None, *, wait_sec):
    '''Poll until free VRAM meets requirement or timeout.'''
    deadline = time.time() + max(0, wait_sec)
    free = free_vram_mb(force = True)
    if free < required_mb and time.time() < deadline:
        time.sleep(0.4)
        release_torch_memory()
        free = free_vram_mb(force = True)
        if free < required_mb and time.time() < deadline:
            continue
    return free


def prepare_for_comfyui(*, required_mb, wait_sec):
    '''Unload Ollama + PyTorch cache before ComfyUI image work.'''
    if not vram_guard_enabled():
        return {
            'ok': True,
            'skipped': True }
# WARNING: Decompyle incomplete


def ensure_vram_for_comfyui(checkpoint = None):
    '''Prepare GPU and fail fast when VRAM is still too low for the checkpoint.'''
    warm = _comfyui_warm()
    required = required_vram_for_checkpoint(checkpoint, warm = warm)
    prep = prepare_for_comfyui(required_mb = required)
    prep['comfyui_warm'] = warm
    if prep.get('skipped'):
        return prep
    if not prep.get('free_vram_mb'):
        prep.get('free_vram_mb')
    free = None(0)
# WARNING: Decompyle incomplete


def prepare_for_torch_ml():
    '''Free VRAM before MusicGen / diarization / other torch jobs.'''
    if not vram_guard_enabled():
        return {
            'ok': True,
            'skipped': True }
    unloaded = None()
    release_torch_memory()
    return {
        'ok': True,
        'unloaded_ollama': unloaded,
        'released_torch': True }


def free_vram():
    '''Manual / API: drop Ollama models and clear PyTorch cache.'''
    unloaded = unload_ollama_models()
    release_torch_memory()
    gpu = detect_gpu()
    return {
        'ok': True,
        'unloaded_ollama': unloaded,
        'released_torch': True,
        'vram_mb': gpu.get('vram_mb'),
        'ollama_using_gpu': gpu.get('ollama_using_gpu') }


def recommendations():
    '''Actionable tips for the current machine.'''
    gpu = detect_gpu()
    if not gpu.get('vram_mb'):
        gpu.get('vram_mb')
    vram = int(0)
    tips = []
    if is_low_vram(10240):
        tips.append('Use 7B chat/code models (not 14B+) — switch profile to Gaming or run optimize-rx7600-8gb.sh')
        tips.append('Vision: moondream or llama3.2-vision:11b — avoid llava:13b on 8GB')
        tips.append('Whisper: small on CPU (AMD) — set JARVIS_WHISPER_MODEL=small')
        tips.append('Unload Ollama before ComfyUI/Song Studio (JARVIS_VRAM_GUARD=1, default on)')
    if gpu.get('vendor') == 'amd' and gpu.get('rocm_available'):
        tips.append('RX 7600: keep HSA_OVERRIDE_GFX_VERSION=11.0.0 for ComfyUI GPU')
    if gpu.get('ollama_using_gpu') and vram and vram <= 10240:
        tips.append('Ollama is using GPU — click Free VRAM before image gen if you hit OOM')
    if not tips:
        tips.append('VRAM looks comfortable — JARVIS_VRAM_GUARD still helps when mixing Ollama + ComfyUI')
    return tips


def status():
    gpu = detect_gpu()
    return {
        'guard_enabled': vram_guard_enabled(),
        'low_vram': is_low_vram(10240),
        'vram_mb': gpu.get('vram_mb'),
        'ollama_using_gpu': gpu.get('ollama_using_gpu'),
        'ollama_processor': gpu.get('ollama_processor'),
        'recommendations': recommendations() }

