# Source Generated with Decompyle++
# File: pin_lock.cpython-312.pyc (Python 3.12)

'''GUI security — PIN lock, sessions, idle re-lock.'''
from __future__ import annotations
import hashlib
import json
import secrets
import time
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p4_flags import face_auth_enabled, lock_idle_seconds, pin_lock_enabled
PIN_FILE = DATA_DIR / 'security' / 'pin.json'
SESSIONS_FILE = DATA_DIR / 'security' / 'sessions.json'

def _ensure_dir():
    PIN_FILE.parent.mkdir(parents = True, exist_ok = True)


def pin_configured():
    return PIN_FILE.is_file()


def _hash_pin(pin = None, salt = None):
    return hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 120000).hex()


def set_pin(pin = None):
    if not pin:
        pin
    pin = ''.strip()
    if pin.isdigit():
        if not  <= 4, len(pin) or 4, len(pin) <= 6:
            raise ValueError('PIN must be 4–6 digits')
    raise ValueError('PIN must be 4–6 digits')
    _ensure_dir()
    PIN_FILE.write_text(json.dumps({
        'salt': salt,
        'hash': _hash_pin(pin, salt) }, indent = 2), encoding = 'utf-8')
    return {
        'ok': True,
        'configured': True }


def verify_pin(pin = None):
    if not PIN_FILE.is_file():
        return False
    
    try:
        data = json.loads(PIN_FILE.read_text(encoding = 'utf-8'))
        if not pin:
            pin
        return _hash_pin(''.strip(), data['salt']) == data['hash']
    except (json.JSONDecodeError, OSError, KeyError):
        return False



def _load_sessions():
    if not SESSIONS_FILE.is_file():
        return {
            'sessions': { } }
    
    try:
        return json.loads(SESSIONS_FILE.read_text(encoding = 'utf-8'))
    except (json.JSONDecodeError, OSError):
        return 



def _save_sessions(data = None):
    _ensure_dir()
    SESSIONS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def create_session(*, device_id):
    token = secrets.token_urlsafe(32)
    data = _load_sessions()
    data.setdefault('sessions', { })[token] = {
        'created': time.time(),
        'last_active': time.time(),
        'device_id': device_id }
    _save_sessions(data)
    return token


def touch_session(token = None):
    data = _load_sessions()
    row = data.get('sessions', { }).get(token)
    if not row:
        return False
    row['last_active'] = time.time()
    _save_sessions(data)
    return True


def session_valid(token = None):
    if not token:
        return False
    if not pin_lock_enabled():
        return True
    if not pin_configured():
        return True
    data = _load_sessions()
    row = data.get('sessions', { }).get(token)
    if not row:
        return False
    idle = lock_idle_seconds()
    if not row.get('last_active'):
        row.get('last_active')
    if time.time() - float(0) > idle:
        revoke_session(token)
        return False
    return True


def revoke_session(token = None):
    data = _load_sessions()
    data.get('sessions', { }).pop(token, None)
    _save_sessions(data)


def revoke_all_sessions():
    data = _load_sessions()
    if not data.get('sessions'):
        data.get('sessions')
    count = len({ })
    data['sessions'] = { }
    _save_sessions(data)
    return count


def lock_status(*, session_token):
    if pin_lock_enabled():
        pin_lock_enabled()
    if session_token:
        return {
            'pin_lock_enabled': pin_lock_enabled(),
            'pin_configured': pin_configured(),
            'face_auth_enabled': face_auth_enabled(),
            'idle_seconds': lock_idle_seconds(),
            'lock_capable': pin_configured(),
            'session_valid': session_valid(session_token) }
    return {
        'pin_lock_enabled': None,
        'pin_configured': pin_lock_enabled(),
        'face_auth_enabled': pin_configured(),
        'idle_seconds': face_auth_enabled(),
        'lock_capable': lock_idle_seconds(),
        'session_valid': pin_configured() }

