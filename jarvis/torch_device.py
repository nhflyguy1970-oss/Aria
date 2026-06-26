# Source Generated with Decompyle++
# File: torch_device.cpython-312.pyc (Python 3.12)

'''Pick best torch device (CUDA NVIDIA / ROCm AMD / CPU) for audio ML.'''
from __future__ import annotations
import os

def _rocm_pytorch_gpu():
    '''True when PyTorch ROCm exposes a GPU via the cuda API.'''
    
    try:
        import torch
        if not torch.cuda.is_available():
            return False
            
            try:
                return bool(getattr(torch.version, 'hip', None))
            except ImportError:
                return False




def torch_device():
    """Return 'cuda', 'cpu', or env override for PyTorch (MusicGen, pyannote, etc.)."""
    resolve_torch_device = resolve_torch_device
    import jarvis.gpu_routing
    return resolve_torch_device()


def whisper_device():
    '''Device for faster-whisper (CTranslate2). NVIDIA CUDA when available.'''
    resolve_whisper_device = resolve_whisper_device
    import jarvis.gpu_routing
    return resolve_whisper_device()


def device_info():
    detect_gpu = detect_gpu
    import jarvis.gpu
    routing_status = routing_status
    torch_backend = torch_backend
    import jarvis.gpu_routing
    gpu = detect_gpu()
    routing = routing_status()
    dev = torch_device()
    whisper = whisper_device()
    backend = torch_backend()
    hint = ''
    if backend == 'cuda_nvidia':
        hint = f'''PyTorch on NVIDIA CUDA ({gpu.get('name', 'GPU')}). Whisper: {whisper}.'''
    elif backend == 'cuda_rocm' and gpu.get('nvidia_available'):
        hint = 'PyTorch is ROCm (AMD) but NVIDIA is present. Run ./scripts/install-cuda-pytorch.sh and ./scripts/enable-nvidia-gpu.sh to move AI workloads to the RTX GPU.'
    elif gpu.get('vendor') == 'amd' and gpu.get('rocm_available'):
        if dev == 'cuda' and _rocm_pytorch_gpu():
            hint = "PyTorch ROCm uses device name 'cuda' on AMD — that is normal. Whisper uses NVIDIA CUDA when JARVIS_GPU_PREFER=nvidia."
        elif dev == 'cpu':
            hint = 'Using CPU — install ROCm PyTorch for faster MusicGen/diarization on AMD'
        elif dev == 'cpu':
            hint = 'Using CPU — install CUDA PyTorch for NVIDIA or ROCm PyTorch for AMD'
    return {
        'device': dev,
        'whisper_device': whisper,
        'gpu': gpu,
        'routing': routing,
        'hint': hint }

