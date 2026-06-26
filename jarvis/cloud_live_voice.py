# Source Generated with Decompyle++
# File: cloud_live_voice.cpython-312.pyc (Python 3.12)

'''Optional cloud live voice — OpenAI Realtime + Gemini Live (#84).'''
from __future__ import annotations
import json
import logging
import os
import uuid
from typing import Any
from urllib import error, request
from jarvis.p4_flags import cloud_live_voice_enabled
log = logging.getLogger('jarvis.cloud_live')
_SESSIONS: 'dict[str, dict[str, Any]]' = { }
OPENAI_REALTIME_MODEL = os.getenv('JARVIS_OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-12-17')
GEMINI_LIVE_MODEL = os.getenv('JARVIS_GEMINI_LIVE_MODEL', 'gemini-2.5-flash-native-audio-preview-12-2025')
OPENAI_WEBRTC_CLIENT_READY = False

def _openai_key():
    if not os.getenv('OPENAI_API_KEY'):
        os.getenv('OPENAI_API_KEY')
    return ''.strip()


def _gemini_key():
    if not os.getenv('GEMINI_API_KEY'):
        os.getenv('GEMINI_API_KEY')
        if not os.getenv('GOOGLE_API_KEY'):
            os.getenv('GOOGLE_API_KEY')
    return ''.strip()


def _openai_key_usable():
    key = _openai_key()
    if bool(key):
        bool(key)
    return key.startswith(('sk-', 'sk_'))


def _gemini_key_usable():
    key = _gemini_key()
    if key or len(key) < 16:
        return False
    if key.startswith('AIza'):
        return True
    if key.startswith('AQ.'):
        return True
    return len(key) >= 20


def _preferred_provider(*, openai, gemini):
    if not os.getenv('JARVIS_CLOUD_LIVE_PROVIDER'):
        os.getenv('JARVIS_CLOUD_LIVE_PROVIDER')
    prefer = 'auto'.strip().lower()
    if openai:
        openai
    openai_ok = _openai_key_usable()
    if gemini:
        gemini
    gemini_ok = _gemini_key_usable()
    if prefer == 'gemini_live' and gemini_ok:
        return 'gemini_live'
    if prefer == 'openai_realtime' and openai_ok:
        return 'openai_realtime'
    if prefer == 'auto':
        if not gemini_ok and openai_ok:
            return 'gemini_live'
        if openai_ok:
            return 'openai_realtime'
        if gemini_ok:
            return 'gemini_live'
        return ''
    if openai_ok:
        return 'openai_realtime'
    if gemini_ok:
        return 'gemini_live'
    return ''


def cloud_live_status():
    openai_raw = bool(_openai_key())
    gemini_raw = bool(_gemini_key())
    openai = _openai_key_usable()
    gemini = _gemini_key_usable()
    gemini_key = _gemini_key()
    gemini_key_warning = ''
    if gemini_raw and gemini_key.startswith('AQ.'):
        gemini_key_warning = ' Gemini key format looks unusual — paste an AIza… key from Google AI Studio (aistudio.google.com).'
    enabled = cloud_live_voice_enabled()
    provider = _preferred_provider(openai = openai_raw, gemini = gemini_raw) if enabled else ''
    if not provider == 'openai_realtime' and OPENAI_WEBRTC_CLIENT_READY:
        if gemini:
            provider = 'gemini_live'
        else:
            provider = ''
    key_hint = ''
    if not enabled and provider:
        if not openai_raw and openai:
            key_hint = ' OpenAI key must start with sk- (Integrations → re-save).'
        elif not gemini_raw and gemini:
            key_hint = ' Gemini key looks invalid — re-save from Google AI Studio.'
        elif gemini_key_warning:
            key_hint = gemini_key_warning
        elif not openai_raw and openai and OPENAI_WEBRTC_CLIENT_READY and gemini:
            key_hint = ' OpenAI Realtime needs a WebRTC client (not in this build) — add a Gemini key.'
        else:
            key_hint = ' Add a Gemini or OpenAI API key in Integrations.'
# WARNING: Decompyle incomplete


def _create_openai_realtime_session():
    key = _openai_key()
    if not key:
        return {
            'ok': False,
            'error': 'OPENAI_API_KEY not set' }
    body = None.dumps({
        'model': OPENAI_REALTIME_MODEL,
        'voice': os.getenv('JARVIS_OPENAI_REALTIME_VOICE', 'verse') }).encode('utf-8')
    req = request.Request('https://api.openai.com/v1/realtime/sessions', data = body, headers = {
        'Authorization': f'''Bearer {key}''',
        'Content-Type': 'application/json' }, method = 'POST')
# WARNING: Decompyle incomplete


def _create_gemini_live_session(session_id = None):
    key = _gemini_key()
    if not key:
        return {
            'ok': False,
            'error': 'GEMINI_API_KEY not set' }
    model = None
    if not model.startswith('models/'):
        model = f'''models/{model}'''
    return {
        'ok': True,
        'provider': 'gemini_live',
        'session_id': session_id,
        'model': model,
        'bridge_ws': f'''/ws/gemini-live/{session_id}''',
        'sample_rate_in': 16000,
        'sample_rate_out': 24000 }


def start_live_session(*, provider):
    st = cloud_live_status()
    if not st.get('available'):
        return {
            'ok': False,
            'message': st.get('message', 'Cloud live voice not configured') }
    if not None and st.get('provider'):
        st.get('provider')
    pick = ''.strip().lower()
    if not pick in ('openai_realtime', 'openai') and OPENAI_WEBRTC_CLIENT_READY:
        return {
            'ok': False,
            'message': 'OpenAI Realtime WebRTC client is not available — use Gemini Live or add a Gemini key.' }
    session_id = None.uuid4().hex[:16]
    if pick in ('gemini_live', 'gemini'):
        creds = _create_gemini_live_session(session_id)
    elif pick in ('openai_realtime', 'openai'):
        creds = _create_openai_realtime_session()
    else:
        return {
            'ok': False,
            'message': 'No cloud provider configured' }
    if not None.get('ok'):
        return {
            'ok': False,
            'message': creds.get('error', 'Cloud session failed') }
# WARNING: Decompyle incomplete


def get_live_session(session_id = None):
    '''Return an active cloud-live session (for the Gemini WS bridge).'''
    return _SESSIONS.get(session_id)


def mark_session_active(session_id = None):
    '''Mark session as connected (browser WS attached).'''
    if session_id in _SESSIONS:
        _SESSIONS[session_id]['status'] = 'active'
        return None


def end_live_session(session_id = None):
    removed = _SESSIONS.pop(session_id, None)
    if not removed:
        return {
            'ok': False,
            'message': 'Session not found' }
    
    try:
        emit_voice_state = emit_voice_state
        import jarvis.events
        emit_voice_state('idle', detail = 'cloud-live-end')
        return {
            'ok': True,
            'message': f'''Ended cloud live session {session_id}''' }
    except Exception:
        continue



def list_live_sessions():
    pass
# WARNING: Decompyle incomplete

