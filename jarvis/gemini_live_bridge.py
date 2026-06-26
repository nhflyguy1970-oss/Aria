# Source Generated with Decompyle++
# File: gemini_live_bridge.cpython-312.pyc (Python 3.12)

'''Gemini Live API WebSocket bridge (server-side proxy — API key never sent to browser).'''
from __future__ import annotations
import asyncio
import base64
import json
import logging
import os
from typing import Any
log = logging.getLogger('jarvis.gemini_live')
GEMINI_WS_BASE = 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent'

def _api_key():
    if not os.getenv('GEMINI_API_KEY'):
        os.getenv('GEMINI_API_KEY')
        if not os.getenv('GOOGLE_API_KEY'):
            os.getenv('GOOGLE_API_KEY')
    return ''.strip()


def _model():
    if not os.getenv('JARVIS_GEMINI_LIVE_MODEL'):
        os.getenv('JARVIS_GEMINI_LIVE_MODEL')
    raw = 'gemini-2.5-flash-native-audio-preview-12-2025'.strip()
    if raw.startswith('models/'):
        return raw
    return f'''{raw}'''


def _decode_ws_frame(raw = None):
    if isinstance(raw, bytes):
        return raw.decode('utf-8', errors = 'replace')


def _voice_name():
    if not os.getenv('JARVIS_GEMINI_LIVE_VOICE'):
        os.getenv('JARVIS_GEMINI_LIVE_VOICE')
    return 'Aoede'.strip()


def _system_instruction():
    assistant_full_name = assistant_full_name
    assistant_name = assistant_name
    import jarvis.branding
    if not os.getenv('JARVIS_GEMINI_LIVE_SYSTEM'):
        os.getenv('JARVIS_GEMINI_LIVE_SYSTEM')
    custom = ''.strip()
    if custom:
        return custom
    return f'''{assistant_name()}, {assistant_full_name()}. You are a helpful voice assistant. Be concise and natural in speech.'''


def build_setup_message():
    return {
        'setup': {
            'model': _model(),
            'generationConfig': {
                'responseModalities': [
                    'AUDIO'],
                'speechConfig': {
                    'voiceConfig': {
                        'prebuiltVoiceConfig': {
                            'voiceName': _voice_name() } } } },
            'systemInstruction': {
                'parts': [
                    {
                        'text': _system_instruction() }] },
            'inputAudioTranscription': { },
            'outputAudioTranscription': { },
            'realtimeInputConfig': {
                'automaticActivityDetection': {
                    'disabled': False,
                    'startOfSpeechSensitivity': 'START_SENSITIVITY_LOW',
                    'endOfSpeechSensitivity': 'END_SENSITIVITY_LOW' } } } }


def client_audio_to_gemini(data_b64 = None):
    return {
        'realtimeInput': {
            'audio': {
                'mimeType': 'audio/pcm;rate=16000',
                'data': data_b64 } } }


def client_text_to_gemini(text = None):
    return {
        'realtimeInput': {
            'text': text } }


def normalize_upstream_message(raw = None):
    pass
# WARNING: Decompyle incomplete


def _client_to_gemini(text = None):
    
    try:
        msg = json.loads(text)
        if not isinstance(msg, dict):
            return None
        kind = msg.get('type')
        if kind == 'audio' and msg.get('data'):
            return json.dumps(client_audio_to_gemini(str(msg['data'])))
        if None == 'text' and msg.get('text'):
            return json.dumps(client_text_to_gemini(str(msg['text'])))
        if None == 'ping':
            return None
        return None
    except json.JSONDecodeError:
        return None



async def run_gemini_live_bridge(client_ws = None, session_id = None):
    pass
# WARNING: Decompyle incomplete

