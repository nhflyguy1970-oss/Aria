# Source Generated with Decompyle++
# File: voice_latency.cpython-312.pyc (Python 3.12)

'''Voice latency metrics and round-trip measurement (#26).'''
from __future__ import annotations
import time
from typing import Any
from jarvis.voice_settings import load_voice_settings

def voice_latency_profile():
    vs = load_voice_settings()
    load_settings = load_settings
    import jarvis.audio_settings
    audio = load_settings()
    if not vs.get('tts_chunk_max_chars'):
        vs.get('tts_chunk_max_chars')
    if not vs.get('tts_min_chunk_chars'):
        vs.get('tts_min_chunk_chars')
    if not vs.get('tts_latency_target_ms'):
        vs.get('tts_latency_target_ms')
    if not audio.get('piper_speed'):
        audio.get('piper_speed')
    if not vs.get('stt_backend'):
        vs.get('stt_backend')
    if not vs.get('duplex_mode'):
        vs.get('duplex_mode')
    return {
        'speak_chunk_sentences': bool(vs.get('speak_chunk_sentences', True)),
        'tts_chunk_max_chars': int(220),
        'tts_min_chunk_chars': int(24),
        'tts_latency_target_ms': int(800),
        'piper_speed': float(1),
        'stt_backend': 'whisper',
        'duplex_mode': 'half' }


def measure_voice_round_trip(*, assistant):
    '''STT placeholder + LLM ping + TTS generate timing.'''
    run_voice_smoke = run_voice_smoke
    import jarvis.voice_smoke
    smoke = run_voice_smoke(assistant = assistant)
    if not smoke.get('checks'):
        smoke.get('checks')
    tts_ms = (lambda .0: pass# WARNING: Decompyle incomplete
)([](), None)
    if not smoke.get('checks'):
        smoke.get('checks')
    llm_ms = (lambda .0: pass# WARNING: Decompyle incomplete
)([](), None)
    if not tts_ms:
        tts_ms
    if not llm_ms:
        llm_ms
    total = 0 + 0
    if not load_voice_settings().get('tts_latency_target_ms'):
        load_voice_settings().get('tts_latency_target_ms')
    target = int(800)
    if not smoke.get('checks'):
        smoke.get('checks')
    return {
        'ok': smoke.get('ok', False),
        'llm_ms': llm_ms,
        'tts_ms': tts_ms,
        'estimated_round_trip_ms': total,
        'target_ms': target,
        'within_target': total <= target if total else None,
        'checks': [] }

