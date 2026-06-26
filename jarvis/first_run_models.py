# Source Generated with Decompyle++
# File: first_run_models.cpython-312.pyc (Python 3.12)

'''First-run model checks and optional Ollama pulls.'''
from __future__ import annotations
import logging
import os
import subprocess
from jarvis.config import DATA_DIR
from jarvis.p1_flags import first_run_models_enabled
log = logging.getLogger('jarvis.first_run')
MARKER = DATA_DIR / '.first_run_models_done'

def _pull(model = None):
    
    try:
        subprocess.run([
            'ollama',
            'pull',
            model], check = False, timeout = 600, capture_output = True)
        return True
    except Exception:
        exc = None
        log.warning('pull %s failed: %s', model, exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def ensure_optional_models(*, force):
    if not first_run_models_enabled():
        return {
            'skipped': True,
            'reason': 'disabled' }
    marker_path = None
    if not marker_path.exists() and force:
        return {
            'skipped': True,
            'reason': 'already ran' }
    check_ollama = check_ollama
    model_available = model_available
    import jarvis.ollama_health
    router_model = router_model
    import jarvis.local_router
    fast_chat_model = fast_chat_model
    reasoning_model = reasoning_model
    import jarvis.brain_routing
    brain_routing_enabled = brain_routing_enabled
    import jarvis.p1_flags
    pulled = []
    if not check_ollama().get('running'):
        return {
            'ok': False,
            'error': 'ollama not running' }
    targets = [
        router_model(),
        fast_chat_model()]
    if brain_routing_enabled():
        targets.append(reasoning_model())
    if not os.getenv('JARVIS_WHISPER_MODEL', 'small').strip():
        os.getenv('JARVIS_WHISPER_MODEL', 'small').strip()
    whisper_model = 'small'
    if whisper_model not in targets:
        targets.append(whisper_model)
    seen = set()
    voice_notes = []
    for m in targets:
        if not m:
            m
        m = ''.strip()
        if m or m in seen:
            continue
        seen.add(m)
        if model_available(m):
            continue
        if not _pull(m):
            continue
        pulled.append(m)
    
    try:
        ensure_voice_assets = ensure_voice_assets
        import jarvis.first_run_downloads
        dl = ensure_voice_assets()
        if not dl.get('voice'):
            dl.get('voice')
        for note in []:
            if not note not in voice_notes:
                continue
                
                try:
                    voice_notes.append(note)
                    continue
                    if not dl.get('pulled'):
                        dl.get('pulled')
                    for item in []:
                        if not item not in pulled:
                            continue
                            
                            try:
                                pulled.append(item)
                                continue
                                
                                try:
                                    piper_ready = piper_ready
                                    piper_voice_label = piper_voice_label
                                    import jarvis.config
                                    if not piper_ready():
                                        voice_notes.append('Piper TTS not ready after auto-download — run scripts/install-dependencies.sh')
                                    else:
                                        voice_notes.append(f'''Piper OK ({piper_voice_label()})''')
                                    
                                    try:
                                        whisper_backend = whisper_backend
                                        import jarvis.audio_whisper
                                        wb = whisper_backend()
                                        if wb == 'none':
                                            voice_notes.append('Whisper not available — pip install faster-whisper')
                                        else:
                                            voice_notes.append(f'''Whisper backend: {wb}''')
                                        if not os.getenv('JARVIS_ROUTER_BACKEND'):
                                            os.getenv('JARVIS_ROUTER_BACKEND')
                                        backend = 'auto'.strip().lower()
                                        if backend in ('auto', 'functiongemma'):
                                            
                                            try:
                                                functiongemma_ready = functiongemma_ready
                                                warm_model = warm_model
                                                import jarvis.functiongemma_router
                                                if functiongemma_ready():
                                                    voice_notes.append('FunctionGemma weights cached')
                                                elif backend == 'functiongemma':
                                                    warm = warm_model()
                                                    if warm.get('ok'):
                                                        voice_notes.append('FunctionGemma loaded')
                                                    else:
                                                        voice_notes.append('FunctionGemma missing — pip install transformers torch; accept license at huggingface.co/google/functiongemma-270m-it')
                                                
                                                try:
                                                    marker_path.parent.mkdir(parents = True, exist_ok = True)
                                                    marker_path.write_text('ok\n', encoding = 'utf-8')
                                                    return {
                                                        'ok': True,
                                                        'pulled': pulled,
                                                        'voice': voice_notes }
                                                    except Exception:
                                                        exc = None
                                                        voice_notes.append(f'''Voice asset download: {exc}''')
                                                        exc = None
                                                        del exc
                                                        continue
                                                        exc = None
                                                        del exc
                                                    except Exception:
                                                        voice_notes.append('Piper check skipped')
                                                        continue
                                                    except Exception:
                                                        continue
                                                    except Exception:
                                                        continue
                                                except OSError:
                                                    continue








