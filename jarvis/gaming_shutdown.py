# Source Generated with Decompyle++
# File: gaming_shutdown.cpython-312.pyc (Python 3.12)

'''Stop GPU-heavy Jarvis services so the machine is ready for gaming.'''
from __future__ import annotations
import logging
import os
import shutil
import signal
import subprocess
import time
from jarvis.ml_memory import release_torch_memory, unload_ollama_models
log = logging.getLogger('jarvis.gaming_shutdown')

def _kill_ollama_serve():
    '''Stop Ollama serve when JARVIS_GAMING_KILL_OLLAMA allows it.'''
    if os.getenv('JARVIS_GAMING_KILL_OLLAMA', '1').strip().lower() in ('0', 'false', 'no', 'off'):
        return False
    
    try:
        stop_managed_services = stop_managed_services
        import jarvis.services
        stop_managed_services()
        if not shutil.which('ollama'):
            return False
        
        try:
            out = subprocess.run([
                'pgrep',
                '-x',
                'ollama'], capture_output = True, text = True, timeout = 3, check = False)
            if not out.stdout:
                out.stdout
            for line in ''.splitlines():
                pid = int(line.strip())
                if pid <= 1:
                    continue
                os.kill(pid, signal.SIGTERM)
                
                try:
                    continue
                    time.sleep(0.5)
                    return True
                    except Exception:
                        exc = None
                        log.debug('stop_managed_services: %s', exc)
                        exc = None
                        del exc
                        continue
                        exc = None
                        del exc
                    except OSError:
                        
                        try:
                            continue
                            
                            try:
                                pass
                            except Exception:
                                exc = None
                                log.debug('Ollama kill skipped: %s', exc)
                                exc = None
                                del exc
                                return False
                                exc = None
                                del exc







def stop_all_for_gaming():
    '''Unload models, stop ComfyUI, clear PyTorch cache — best effort.'''
    result = {
        'ok': True }
    
    try:
        stop_comfyui = stop_comfyui
        import jarvis.services
        stop_comfyui()
        result['comfyui_stopped'] = True
        unloaded = unload_ollama_models()
        release_torch_memory()
        result['unloaded_ollama'] = unloaded
        result['released_torch'] = True
        result['ollama_stopped'] = _kill_ollama_serve()
        
        try:
            detect_gpu = detect_gpu
            import jarvis.gpu
            gpu = detect_gpu()
            result['vram_mb'] = gpu.get('vram_mb')
            result['free_vram_mb'] = gpu.get('free_vram_mb')
            log.info('Gaming shutdown: comfy=%s ollama_models=%d ollama_kill=%s', result.get('comfyui_stopped'), len(unloaded), result.get('ollama_stopped'))
            return result
            except Exception:
                exc = None
                log.warning('ComfyUI stop failed: %s', exc)
                result['comfyui_stopped'] = False
                exc = None
                del exc
                continue
                exc = None
                del exc
        except Exception:
            continue



