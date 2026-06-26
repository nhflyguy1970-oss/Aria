# Source Generated with Decompyle++
# File: voice_settings.cpython-312.pyc (Python 3.12)

'''Voice mode settings — duplex, STT backend, latency prefs.'''
from __future__ import annotations
import json
from jarvis.audio_settings import load_settings, save_settings
from jarvis.config import DATA_DIR
VOICE_FILE = DATA_DIR / 'voice_settings.json'

def load_voice_settings():
    merged = {
        'duplex_mode': 'half',
        'stt_backend': 'whisper',
        'interrupt_on_speak': True,
        'speak_chunk_sentences': True,
        'tts_chunk_max_chars': 220,
        'tts_latency_target_ms': 800,
        'tts_min_chunk_chars': 24 }
    if VOICE_FILE.exists():
        
        try:
            merged.update(json.loads(VOICE_FILE.read_text(encoding = 'utf-8')))
            audio = load_settings()
            if audio.get('duplex_mode'):
                merged['duplex_mode'] = audio['duplex_mode']
            return merged
        except (json.JSONDecodeError, OSError):
            continue



def save_voice_settings(patch = None):
    data = load_voice_settings()
    if not patch.get('stt_backend'):
        patch.get('stt_backend')
# WARNING: Decompyle incomplete


def duplex_mode():
    duplex_voice_enabled = duplex_voice_enabled
    import jarvis.p1_flags
    if not duplex_voice_enabled():
        return 'off'
    if not load_voice_settings().get('duplex_mode'):
        load_voice_settings().get('duplex_mode')
    return 'half'.strip().lower()


def stt_backend():
    realtime_stt_enabled = realtime_stt_enabled
    import jarvis.p1_flags
    if not load_voice_settings().get('stt_backend'):
        load_voice_settings().get('stt_backend')
    saved = 'whisper'.strip().lower()
    if saved == 'realtimestt' and realtime_stt_enabled():
        return 'realtimestt'
    if realtime_stt_enabled() and saved != 'whisper':
        return 'realtimestt'
    return 'whisper'

