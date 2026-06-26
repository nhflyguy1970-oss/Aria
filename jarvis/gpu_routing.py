# Source Generated with Decompyle++
# File: gpu_routing.cpython-312.pyc (Python 3.12)

'''GPU vendor preference — NVIDIA CUDA vs AMD ROCm vs hybrid.'''
from __future__ import annotations
import os
import re
import subprocess

def gpu_preference():
    '''nvidia | amd | both | auto'''
    if not os.getenv('JARVIS_GPU_PREFER'):
        os.getenv('JARVIS_GPU_PREFER')
    raw = 'auto'.strip().lower()
    if raw in ('nvidia', 'amd', 'both', 'hybrid', 'auto'):
        if raw in ('both', 'hybrid'):
            return 'both'
        return None


def _run(cmd = None, timeout = None):
    
    try:
        r = subprocess.run(cmd, capture_output = True, text = True, timeout = timeout)
        if not r.stdout:
            r.stdout
        if not r.stderr:
            r.stderr
        return '' + ''
    except Exception:
        return ''



def parse_nvidia_smi():
    '''Return NVIDIA GPU info from nvidia-smi, or empty dict.'''
    out = _run([
        'nvidia-smi',
        '--query-gpu=name,memory.total,memory.used,driver_version,utilization.gpu',
        '--format=csv,noheader,nounits'])
    if out.strip() or 'failed' in out.lower():
        return { }
    line = None.strip().splitlines()[0]
# WARNING: Decompyle incomplete


def nvidia_available():
    if os.getenv('JARVIS_NVIDIA_AVAILABLE', '').strip().lower() in ('0', 'false', 'no'):
        return False
    return bool(parse_nvidia_smi())


def ctranslate2_cuda_count():
    
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0



def torch_backend():
    '''cuda_nvidia | cuda_rocm | cpu'''
    
    try:
        import torch
        if not torch.cuda.is_available():
            return 'cpu'
            
            try:
                if getattr(torch.version, 'hip', None):
                    return 'cuda_rocm'
                    
                    try:
                        if not torch.cuda.get_device_name(0):
                            torch.cuda.get_device_name(0)
                        name = ''.lower()
                        if 'nvidia' in name and 'geforce' in name and 'rtx' in name or 'quadro' in name:
                            return 'cuda_nvidia'
                            
                            try:
                                if 'radeon' in name or 'amd' in name:
                                    return 'cuda_rocm'
                                    
                                    try:
                                        if nvidia_available():
                                            return 'cuda_nvidia'
                                        return None
                                    except ImportError:
                                        return 'cpu'







def resolve_torch_device():
    if not os.getenv('JARVIS_TORCH_DEVICE'):
        os.getenv('JARVIS_TORCH_DEVICE')
    forced = ''.strip().lower()
    if forced in ('cuda', 'cpu', 'mps'):
        if forced == 'cuda' and torch_backend() == 'cuda_rocm' and gpu_preference() == 'nvidia':
            return 'cpu'
        return forced
    pref = None()
    backend = torch_backend()
    if pref == 'amd':
        if backend == 'cuda_rocm':
            return 'cuda'
        return None
    if None in ('nvidia', 'both', 'auto'):
        if backend == 'cuda_nvidia':
            return 'cuda'
        if not backend == 'cuda_rocm' and pref == 'auto' and nvidia_available():
            return 'cuda'
        return 'cpu'
    return 'cpu'


def resolve_whisper_device():
    if not os.getenv('JARVIS_WHISPER_DEVICE'):
        os.getenv('JARVIS_WHISPER_DEVICE')
    forced = ''.strip().lower()
    if forced in ('cuda', 'cpu'):
        return forced
    pref = None()
    if ctranslate2_cuda_count() > 0 and pref in ('nvidia', 'both', 'auto'):
        if pref == 'both':
            if os.getenv('JARVIS_WHISPER_ON_GPU', '1') == '1':
                return 'cuda'
            return None
    return 'cpu'


def resolve_functiongemma_device():
    if not os.getenv('JARVIS_FUNCTIONGEMMA_DEVICE'):
        os.getenv('JARVIS_FUNCTIONGEMMA_DEVICE')
    forced = 'auto'.strip().lower()
    if forced in ('cuda', 'cpu'):
        if forced == 'cuda' and torch_backend() != 'cuda_nvidia':
            return 'cpu'
        return forced
    backend = None()
    if backend == 'cuda_rocm' and nvidia_available():
        return 'cpu'
    if gpu_preference() in ('nvidia', 'both', 'auto') and backend == 'cuda_nvidia':
        return 'cuda'
    if gpu_preference() == 'amd' and backend == 'cuda_rocm':
        return 'cuda'
    if gpu_preference() == 'auto' and backend == 'cuda_rocm':
        return 'cpu'
    return 'cpu'


def gpu_env_for_subprocess():
    '''Env overrides for child processes (ComfyUI, etc.).'''
    env = { }
    pref = gpu_preference()
    if pref in ('nvidia', 'both', 'auto') and nvidia_available():
        if not os.getenv('JARVIS_CUDA_DEVICE'):
            os.getenv('JARVIS_CUDA_DEVICE')
        idx = '0'.strip()
        env['CUDA_VISIBLE_DEVICES'] = idx
        env.setdefault('HIP_VISIBLE_DEVICES', '-1')
        return env
    if None == 'amd':
        env.pop('CUDA_VISIBLE_DEVICES', None)
    return env


def routing_status():
    nvidia = parse_nvidia_smi()
    return {
        'preference': gpu_preference(),
        'nvidia': nvidia,
        'nvidia_available': bool(nvidia),
        'ctranslate2_cuda_devices': ctranslate2_cuda_count(),
        'torch_backend': torch_backend(),
        'resolved_torch_device': resolve_torch_device(),
        'resolved_whisper_device': resolve_whisper_device(),
        'resolved_functiongemma_device': resolve_functiongemma_device() }

