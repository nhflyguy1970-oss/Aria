# Source Generated with Decompyle++
# File: brain_mode.cpython-312.pyc (Python 3.12)

'''Local vs cloud brain / voice mode indicator.'''
from __future__ import annotations
import os
from typing import Any

def brain_mode_status():
    check_ollama = check_ollama
    import jarvis.ollama_health
    cloud_live_voice_enabled = cloud_live_voice_enabled
    import jarvis.p4_flags
    ollama = check_ollama()
    local_ok = bool(ollama.get('running'))
    cloud_bits = []
    if os.getenv('OPENAI_API_KEY', '').strip():
        cloud_bits.append('OpenAI')
    if os.getenv('GEMINI_API_KEY', '').strip() or os.getenv('GOOGLE_API_KEY', '').strip():
        cloud_bits.append('Gemini')
    if os.getenv('JARVIS_MESHY_API_KEY', '').strip() or os.getenv('MESHY_API_KEY', '').strip():
        cloud_bits.append('Meshy')
    if cloud_live_voice_enabled():
        cloud_live_voice_enabled()
    live = bool(cloud_bits)
    if local_ok and cloud_bits:
        pass
    elif not cloud_bits and local_ok:
        pass
    
    mode = 'local'
    if not local_ok and cloud_bits:
        mode = 'offline'
    if not ollama.get('models'):
        ollama.get('models')
    return {
        'mode': mode,
        'local': local_ok,
        'ollama_models': len([]),
        'cloud_providers': cloud_bits,
        'cloud_live_voice': live,
        'label': {
            'local': 'Local brain (Ollama)',
            'cloud': 'Cloud APIs',
            'hybrid': 'Local + cloud',
            'offline': 'Offline — check Ollama' }.get(mode, mode) }

