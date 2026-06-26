# Source Generated with Decompyle++
# File: audio_settings.cpython-312.pyc (Python 3.12)

'''Persisted audio input/output preferences (override jarvis.env when set from GUI).'''
from __future__ import annotations
import json
import os
from jarvis.config import DATA_DIR
SETTINGS_FILE = DATA_DIR / 'audio_settings.json'

def load_settings():
    if not SETTINGS_FILE.exists():
        return { }
    
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def save_settings(patch = None):
    data = load_settings()
# WARNING: Decompyle incomplete


def saved_input_source():
    if not load_settings().get('input_source'):
        load_settings().get('input_source')
    return ''.strip()


def saved_output_sink():
    if not load_settings().get('output_sink'):
        load_settings().get('output_sink')
    return ''.strip()


def saved_creative_capture_volume():
    if not load_settings().get('creative_capture_volume'):
        load_settings().get('creative_capture_volume')
    return ''.strip()


def saved_capture_volume():
    if not load_settings().get('capture_volume'):
        load_settings().get('capture_volume')
    return ''.strip()

MIC_PROFILES = {
    'rear': {
        'label': 'Rear desk mic (combo jack)',
        'expected_input_source': 'Microphone',
        'default_capture_volume': '100%',
        'mic_boost_hint': '20 dB',
        'hint': 'Plug mic into rear combo jack. alsamixer → Input Source = Microphone.' },
    'front': {
        'label': 'Front gaming headset (combo jack)',
        'expected_input_source': 'Front Microphone',
        'default_capture_volume': '100%',
        'mic_boost_hint': '10–20 dB',
        'hint': 'Plug TRRS headset into front combo jack. alsamixer → Input Source = Front Microphone.' } }

def saved_mic_profile():
    if not load_settings().get('mic_profile'):
        load_settings().get('mic_profile')
    p = 'rear'.strip().lower()
    if p in MIC_PROFILES:
        return p

WHISPER_MODELS = ('tiny', 'base', 'small', 'medium', 'large')

def saved_whisper_model():
    if not load_settings().get('whisper_model'):
        load_settings().get('whisper_model')
    m = ''.strip().lower()
    if m in WHISPER_MODELS:
        return m

WHISPER_LANGUAGES = ('auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar', 'hi')

def saved_whisper_language():
    if not load_settings().get('whisper_language'):
        load_settings().get('whisper_language')
    lang = ''.strip().lower()
    if lang in WHISPER_LANGUAGES:
        return lang
    env = None.getenv('JARVIS_WHISPER_LANGUAGE', 'auto').strip().lower()
    if env in WHISPER_LANGUAGES:
        return env


def saved_piper_speed():
    
    try:
        if not load_settings().get('piper_speed'):
            load_settings().get('piper_speed')
        v = float(1)
        if v > 0:
            return v
        return None
    except (TypeError, ValueError):
        return 1


PIPER_SPEEDS = (0.8, 0.9, 1, 1.1, 1.2)
VST_PLAYBACK_CHAINS = ('flat', 'voice', 'music', 'scout', 'gaming', 'custom')
VST_LIVE_CHAINS = ('off', 'flat', 'voice', 'music', 'scout', 'gaming')

def saved_vst_playback_chain():
    if not load_settings().get('vst_playback_chain'):
        load_settings().get('vst_playback_chain')
    c = ''.strip().lower()
    if c in VST_PLAYBACK_CHAINS:
        return c


def saved_vst_live_chain():
    if not load_settings().get('vst_live_chain'):
        load_settings().get('vst_live_chain')
    c = 'off'.strip().lower()
    if c in VST_LIVE_CHAINS:
        return c


def mic_profile_info(profile = None):
    if not profile:
        profile
    key = saved_mic_profile().strip().lower()
    if key not in MIC_PROFILES:
        key = 'rear'
# WARNING: Decompyle incomplete

