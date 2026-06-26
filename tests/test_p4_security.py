# Source Generated with Decompyle++
# File: test_p4_security.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''P4 security, presence, and shell tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import base64 = import _pytest.assertion.rewrite, assertion
import os

def test_p4_flags_includes_p3():
    p4_flags = p4_flags
    import jarvis.p4_flags
    flags = p4_flags()
    @py_assert1 = []
    @py_assert2 = 'cad'
    @py_assert4 = @py_assert2 in flags
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'projects'
        @py_assert11 = @py_assert9 in flags
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_pin_set_and_verify(tmp_path, monkeypatch):
    pin_file = tmp_path / 'pin.json'
    monkeypatch.setattr('jarvis.security.pin_lock.PIN_FILE', pin_file)
    pin_configured = pin_configured
    set_pin = set_pin
    verify_pin = verify_pin
    import jarvis.security.pin_lock
    @py_assert1 = pin_configured()
    @py_assert3 = not @py_assert1
    if not @py_assert3:
        @py_format4 = 'assert not %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(pin_configured) if 'pin_configured' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pin_configured) else 'pin_configured',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert1 = None
    @py_assert3 = None
    set_pin('1234')
    @py_assert1 = pin_configured()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(pin_configured) if 'pin_configured' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pin_configured) else 'pin_configured',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    @py_assert1 = '1234'
    @py_assert3 = verify_pin(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(verify_pin) if 'verify_pin' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(verify_pin) else 'verify_pin',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = '9999'
    @py_assert3 = verify_pin(@py_assert1)
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(verify_pin) if 'verify_pin' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(verify_pin) else 'verify_pin',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_pin_rejects_invalid():
    set_pin = set_pin
    import jarvis.security.pin_lock
    
    try:
        set_pin('12')
        @py_assert0 = False
        if not @py_assert0:
            @py_format2 = (@pytest_ar._format_assertmsg('expected ValueError') + '\n>assert %(py1)s') % {
                'py1': @pytest_ar._saferepr(@py_assert0) }
            raise AssertionError(@pytest_ar._format_explanation(@py_format2))
        @py_assert0 = None
        return None
    except ValueError:
        return None



def test_session_lifecycle(tmp_path, monkeypatch):
    sess_file = tmp_path / 'sessions.json'
    monkeypatch.setattr('jarvis.security.pin_lock.SESSIONS_FILE', sess_file)
    monkeypatch.setenv('JARVIS_PIN_LOCK', '1')
    monkeypatch.setattr('jarvis.security.pin_lock.PIN_FILE', tmp_path / 'pin.json')
    create_session = create_session
    revoke_session = revoke_session
    session_valid = session_valid
    set_pin = set_pin
    touch_session = touch_session
    import jarvis.security.pin_lock
    set_pin('4321')
    token = create_session(device_id = 'test-dev')
    @py_assert2 = session_valid(token)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    @py_assert2 = touch_session(token)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(touch_session) if 'touch_session' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(touch_session) else 'touch_session',
            'py1': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    revoke_session(token)
    @py_assert2 = session_valid(token)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None


def test_trusted_device(tmp_path, monkeypatch):
    store = tmp_path / 'trusted.json'
    monkeypatch.setattr('jarvis.security.trusted_devices.STORE', store)
    monkeypatch.setenv('JARVIS_TRUSTED_LAN', '1')
    is_trusted = is_trusted
    list_trusted = list_trusted
    revoke_device = revoke_device
    trust_device = trust_device
    import jarvis.security.trusted_devices
    trust_device('dev-abc', label = 'Test', client_ip = '10.0.0.5')
    @py_assert1 = 'dev-abc'
    @py_assert3 = '10.0.0.5'
    @py_assert5 = is_trusted(@py_assert1, client_ip = @py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py2)s, client_ip=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_trusted) if 'is_trusted' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_trusted) else 'is_trusted',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = 'dev-other'
    @py_assert3 = '10.0.0.5'
    @py_assert5 = is_trusted(@py_assert1, client_ip = @py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py0)s(%(py2)s, client_ip=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_trusted) if 'is_trusted' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_trusted) else 'is_trusted',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    devices = list_trusted()
    @py_assert0 = devices[0]['id']
    @py_assert3 = 'dev-abc'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert1 = devices[0]['id']
    @py_assert3 = revoke_device(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(revoke_device) if 'revoke_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(revoke_device) else 'revoke_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_trusted_device_empty_ip_not_trusted(tmp_path, monkeypatch):
    import json
    store = tmp_path / 'trusted.json'
    monkeypatch.setattr('jarvis.security.trusted_devices.STORE', store)
    monkeypatch.setenv('JARVIS_TRUSTED_LAN', '1')
    is_trusted = is_trusted
    trust_device = trust_device
    import jarvis.security.trusted_devices
    trust_device('dev-abc', label = 'Test', client_ip = '10.0.0.5')
    @py_assert1 = 'dev-abc'
    @py_assert3 = ''
    @py_assert5 = is_trusted(@py_assert1, client_ip = @py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py0)s(%(py2)s, client_ip=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_trusted) if 'is_trusted' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_trusted) else 'is_trusted',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert1 = 'dev-abc'
    @py_assert3 = '10.0.0.99'
    @py_assert5 = is_trusted(@py_assert1, client_ip = @py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py0)s(%(py2)s, client_ip=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_trusted) if 'is_trusted' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_trusted) else 'is_trusted',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    store.write_text(json.dumps({
        'devices': [
            {
                'id': 'dev-legacy',
                'ip': '',
                'label': 'legacy' }] }), encoding = 'utf-8')
    @py_assert1 = 'dev-legacy'
    @py_assert3 = '10.0.0.5'
    @py_assert5 = is_trusted(@py_assert1, client_ip = @py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py0)s(%(py2)s, client_ip=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_trusted) if 'is_trusted' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_trusted) else 'is_trusted',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_trust_device_requires_ip(tmp_path, monkeypatch):
    store = tmp_path / 'trusted.json'
    monkeypatch.setattr('jarvis.security.trusted_devices.STORE', store)
    trust_device = trust_device
    import jarvis.security.trusted_devices
    
    try:
        trust_device('dev-x')
        @py_assert0 = False
        if not @py_assert0:
            @py_format2 = (@pytest_ar._format_assertmsg('expected ValueError') + '\n>assert %(py1)s') % {
                'py1': @pytest_ar._saferepr(@py_assert0) }
            raise AssertionError(@pytest_ar._format_explanation(@py_format2))
        @py_assert0 = None
        return None
    except ValueError:
        return None



def test_revoke_all_sessions(tmp_path, monkeypatch):
    sess_file = tmp_path / 'sessions.json'
    monkeypatch.setattr('jarvis.security.pin_lock.SESSIONS_FILE', sess_file)
    monkeypatch.setenv('JARVIS_PIN_LOCK', '1')
    monkeypatch.setattr('jarvis.security.pin_lock.PIN_FILE', tmp_path / 'pin.json')
    create_session = create_session
    revoke_all_sessions = revoke_all_sessions
    session_valid = session_valid
    set_pin = set_pin
    import jarvis.security.pin_lock
    set_pin('4321')
    t1 = create_session(device_id = 'a')
    t2 = create_session(device_id = 'b')
    @py_assert2 = session_valid(t1)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(t1) if 't1' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t1) else 't1',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    @py_assert1 = revoke_all_sessions()
    @py_assert4 = 2
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(revoke_all_sessions) if 'revoke_all_sessions' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(revoke_all_sessions) else 'revoke_all_sessions',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert2 = session_valid(t1)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(t1) if 't1' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t1) else 't1',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert2 = session_valid(t2)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(t2) if 't2' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t2) else 't2',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None


def test_security_lock_handler_revokes_sessions(tmp_path, monkeypatch):
    sess_file = tmp_path / 'sessions.json'
    monkeypatch.setattr('jarvis.security.pin_lock.SESSIONS_FILE', sess_file)
    monkeypatch.setenv('JARVIS_PIN_LOCK', '1')
    monkeypatch.setattr('jarvis.security.pin_lock.PIN_FILE', tmp_path / 'pin.json')
    security_lock = security_lock
    import jarvis.extensions.security.handlers
    create_session = create_session
    session_valid = session_valid
    set_pin = set_pin
    import jarvis.security.pin_lock
    set_pin('4321')
    token = create_session(device_id = 'voice')
    @py_assert2 = session_valid(token)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    result = security_lock(None, { }, '')
    @py_assert1 = result.get
    @py_assert3 = 'lock'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert1 = result.get
    @py_assert3 = 'type'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'lock'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert2 = session_valid(token)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(session_valid) if 'session_valid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session_valid) else 'session_valid',
            'py1': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None


def test_lock_status_fields(tmp_path, monkeypatch):
    pin_file = tmp_path / 'pin.json'
    monkeypatch.setattr('jarvis.security.pin_lock.PIN_FILE', pin_file)
    monkeypatch.setenv('JARVIS_PIN_LOCK', '1')
    monkeypatch.setenv('JARVIS_FACE_AUTH', '1')
    face_auth_enabled = face_auth_enabled
    import jarvis.p4_flags
    lock_status = lock_status
    set_pin = set_pin
    import jarvis.security.pin_lock
    st = lock_status()
    @py_assert0 = st['lock_capable']
    @py_assert3 = False
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'locked'
    @py_assert2 = @py_assert0 not in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    set_pin('1234')
    st = lock_status()
    @py_assert0 = st['lock_capable']
    @py_assert3 = True
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = st['face_auth_enabled']
    @py_assert4 = face_auth_enabled()
    @py_assert2 = @py_assert0 == @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(face_auth_enabled) if 'face_auth_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(face_auth_enabled) else 'face_auth_enabled',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_security_settings_revoke_uses_id():
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    security = open(os.path.join(root, 'security_settings.js'), encoding = 'utf-8').read()
    @py_assert0 = 'd.id'
    @py_assert2 = @py_assert0 in security
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, security)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(security) if 'security' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(security) else 'security' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'd.device_id'
    @py_assert2 = @py_assert0 not in security
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, security)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(security) if 'security' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(security) else 'security' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_face_mediapipe_fallback_when_unavailable(tmp_path, monkeypatch):
    face_file = tmp_path / 'face_profile.json'
    face_img = tmp_path / 'face_enroll.jpg'
    monkeypatch.setattr('jarvis.security.face_auth.FACE_FILE', face_file)
    monkeypatch.setattr('jarvis.security.face_auth.FACE_IMG', face_img)
    monkeypatch.setenv('JARVIS_FACE_AUTH', '1')
    enroll_face = enroll_face
    verify_face = verify_face
    import jarvis.security.face_auth
    tiny = base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' ,#\x1c\x1c(7),01444\x1f'=9=82<.7\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\x8a(\xa2\x8f\xff\xd9").decode()
    data_url = f'''data:image/jpeg;base64,{tiny}'''
    er = enroll_face(data_url)
    @py_assert1 = er.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(er) if 'er' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(er) else 'er',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    face_file.write_text('{"fingerprint": [0.1, 0.2], "method": "mediapipe"}', encoding = 'utf-8')
    monkeypatch.setattr('jarvis.security.face_auth._mediapipe_available', (lambda : False))
    vr = verify_face(data_url)
    @py_assert1 = vr.get
    @py_assert3 = 'method'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'histogram_fallback'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(vr) if 'vr' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vr) else 'vr',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert0 = 'ok'
    @py_assert2 = @py_assert0 in vr
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, vr)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(vr) if 'vr' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vr) else 'vr' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_brain_mode_status():
    brain_mode_status = brain_mode_status
    import jarvis.security.brain_mode
    st = brain_mode_status()
    @py_assert0 = st['mode']
    @py_assert3 = ('local', 'cloud', 'hybrid', 'offline')
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'label'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_tools_status():
    tools_status = tools_status
    import jarvis.security.tools_status
    rows = tools_status()
    @py_assert3 = isinstance(rows, list)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py1)s, %(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(rows) if 'rows' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rows) else 'rows',
            'py2': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert3 = None
    @py_assert1 = rows()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_face_enroll_verify(tmp_path, monkeypatch):
    face_file = tmp_path / 'face_profile.json'
    face_img = tmp_path / 'face_enroll.jpg'
    monkeypatch.setattr('jarvis.security.face_auth.FACE_FILE', face_file)
    monkeypatch.setattr('jarvis.security.face_auth.FACE_IMG', face_img)
    monkeypatch.setenv('JARVIS_FACE_AUTH', '1')
    enroll_face = enroll_face
    verify_face = verify_face
    import jarvis.security.face_auth
    tiny = base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' ,#\x1c\x1c(7),01444\x1f'=9=82<.7\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\x8a(\xa2\x8f\xff\xd9").decode()
    data_url = f'''data:image/jpeg;base64,{tiny}'''
    er = enroll_face(data_url)
    @py_assert1 = er.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(er) if 'er' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(er) else 'er',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    vr = verify_face(data_url)
    @py_assert1 = vr.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(vr) if 'vr' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vr) else 'vr',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None


def test_gestures_json_defaults(tmp_path, monkeypatch):
    import json
    sec = tmp_path / 'security'
    sec.mkdir()
    path = sec / 'gestures.json'
    monkeypatch.setattr('jarvis.config.DATA_DIR', tmp_path)
    gestures_enabled = gestures_enabled
    floating_panels_enabled = floating_panels_enabled
    import jarvis.p4_flags
    @py_assert2 = gestures_enabled()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(gestures_enabled) if 'gestures_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gestures_enabled) else 'gestures_enabled',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None
    @py_assert2 = floating_panels_enabled()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(floating_panels_enabled) if 'floating_panels_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(floating_panels_enabled) else 'floating_panels_enabled',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None
    path.write_text(json.dumps({
        'mode': 'control' }), encoding = 'utf-8')
    data = json.loads(path.read_text(encoding = 'utf-8'))
    @py_assert0 = data['mode']
    @py_assert3 = 'control'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_gestures_settings_merge_calibration(tmp_path, monkeypatch):
    import json
    sec = tmp_path / 'security'
    sec.mkdir()
    path = sec / 'gestures.json'
    path.write_text(json.dumps({
        'mode': 'control',
        'calibration': {
            'pinchMax': 0.06,
            'palmMin': 0.11,
            'at': 1 } }), encoding = 'utf-8')
    monkeypatch.setattr('jarvis.security.gesture_settings.GESTURES_FILE', path)
    save_gesture_settings = save_gesture_settings
    import jarvis.security.gesture_settings
    data = save_gesture_settings({
        'mode': 'preview' })
    @py_assert0 = data['mode']
    @py_assert3 = 'preview'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = data['calibration']['pinchMax']
    @py_assert3 = 0.06
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    save_gesture_settings({
        'calibration': {
            'pinchMax': 0.07,
            'captured': {
                'pinch': True } } })
    saved = json.loads(path.read_text(encoding = 'utf-8'))
    @py_assert0 = saved['mode']
    @py_assert3 = 'preview'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = saved['calibration']['pinchMax']
    @py_assert3 = 0.07
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = saved['calibration']['palmMin']
    @py_assert3 = 0.11
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = saved['calibration']['captured']['pinch']
    @py_assert3 = True
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_smarthome_scene_js_handles_pin_lock():
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    sm = open(os.path.join(root, 'smarthome.js'), encoding = 'utf-8').read()
    @py_assert0 = 'jarvis-unlocked'
    @py_assert2 = @py_assert0 in sm
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, sm)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(sm) if 'sm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sm) else 'sm' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'scenePanelStatus'
    @py_assert2 = @py_assert0 in sm
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, sm)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(sm) if 'sm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sm) else 'sm' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'needsUnlock'
    @py_assert2 = @py_assert0 in sm
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, sm)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(sm) if 'sm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sm) else 'sm' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'jarvisLockCapable'
    @py_assert2 = @py_assert0 in sm
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, sm)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(sm) if 'sm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sm) else 'sm' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Session expired'
    @py_assert2 = @py_assert0 in sm
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, sm)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(sm) if 'sm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sm) else 'sm' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert2 = 'throw err'
    @py_assert4 = @py_assert2 in sm
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'throw err;'
        @py_assert11 = @py_assert9 in sm
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_lock_screen_session_restore_js():
    '''PIN unlock session should survive reload; stale 423 must not re-lock.'''
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    lock = open(os.path.join(root, 'lock_screen.js'), encoding = 'utf-8').read()
    patch = open(os.path.join(root, 'api_fetch_patch.js'), encoding = 'utf-8').read()
    app = open(os.path.join(root, 'app.js'), encoding = 'utf-8').read()
    @py_assert0 = 'sessionStillValid'
    @py_assert2 = @py_assert0 in lock
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, lock)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(lock) if 'lock' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(lock) else 'lock' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'jarvisLockCapable'
    @py_assert2 = @py_assert0 in lock
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, lock)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(lock) if 'lock' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(lock) else 'lock' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'jarvis-lock-settled'
    @py_assert2 = @py_assert0 in lock
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, lock)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(lock) if 'lock' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(lock) else 'lock' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'jarvisRequireUnlock'
    @py_assert2 = @py_assert0 in patch
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, patch)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(patch) if 'patch' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(patch) else 'patch' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'location.reload()'
    @py_assert3 = app.split('initApiKeyModal')[1].split('initLanPanel')[0]
    @py_assert2 = @py_assert0 not in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_presence_static_js_calibration_fixes():
    '''Regression guard for gesture calibration wiring.'''
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    presence = open(os.path.join(root, 'presence.js'), encoding = 'utf-8').read()
    @py_assert0 = 'gestureTrackingActive'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'applyCalibration'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'buildCalibrationPayload'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'body: JSON.stringify({ mode: m })'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'calibrating || mode !== "off"'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_presence_static_js_s5_fixes():
    '''Regression guard for Subsystem 5 Presence JS-only fixes (S5-01..S5-06).'''
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    presence = open(os.path.join(root, 'presence.js'), encoding = 'utf-8').read()
    security = open(os.path.join(root, 'security_settings.js'), encoding = 'utf-8').read()
    attachments = open(os.path.join(root, 'modules', 'chat', 'attachments.mjs'), encoding = 'utf-8').read()
    @py_assert0 = 'Start camera first'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'disabled — set JARVIS_GESTURES=1 to enable'
    @py_assert2 = @py_assert0 in security
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, security)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(security) if 'security' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(security) else 'security' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'facingMode: "user"'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 's.onerror'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'MediaPipe failed to load'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Cloud Live'
    @py_assert3 = presence.split('cameraErrorHint')[1].split('}')[0]
    @py_assert2 = @py_assert0 not in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'window.jarvisCameraErrorHint = cameraErrorHint'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'window.jarvisCameraErrorHint'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_attachments_static_js_s11_fixes():
    '''Regression guard for Subsystem 11 Vision JS fixes (S11-01..S11-05).'''
    root = os.path.join(os.path.dirname(__file__), '..', 'jarvis', 'gui', 'static')
    attachments = open(os.path.join(root, 'modules', 'chat', 'attachments.mjs'), encoding = 'utf-8').read()
    presence = open(os.path.join(root, 'presence.js'), encoding = 'utf-8').read()
    init = open(os.path.join(root, 'modules', 'chat', 'init.mjs'), encoding = 'utf-8').read()
    state = open(os.path.join(root, 'modules', 'chat', 'state.mjs'), encoding = 'utf-8').read()
    @py_assert0 = 'from "./format.mjs"'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'isTextEntryElement'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'window.loadModelSettings?.()'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'loadModelSettings();'
    @py_assert4 = attachments.replace
    @py_assert6 = 'window.loadModelSettings?.()'
    @py_assert8 = ''
    @py_assert10 = @py_assert4(@py_assert6, @py_assert8)
    @py_assert2 = @py_assert0 not in @py_assert10
    if not @py_assert2:
        @py_format12 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py11)s\n{%(py11)s = %(py5)s\n{%(py5)s = %(py3)s.replace\n}(%(py7)s, %(py9)s)\n}',), (@py_assert0, @py_assert10)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert0 = 'previewObjectUrl'
    @py_assert2 = @py_assert0 in state
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, state)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(state) if 'state' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(state) else 'state' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'revokePreviewObjectUrl'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'URL.revokeObjectURL'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'window.jarvisReleaseOtherCapture?.()'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'window.jarvisReleaseOtherCapture = releaseOtherCapture'
    @py_assert2 = @py_assert0 in presence
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, presence)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(presence) if 'presence' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presence) else 'presence' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'stopCamera()'
    @py_assert3 = presence.split('releaseOtherCapture')[1].split('window.jarvisReleaseOtherCapture')[0]
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'refs.fileInput?.addEventListener("change"'
    @py_assert2 = @py_assert0 not in init
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, init)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(init) if 'init' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(init) else 'init' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'refs.fileInput?.addEventListener("change"'
    @py_assert2 = @py_assert0 in attachments
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, attachments)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(attachments) if 'attachments' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(attachments) else 'attachments' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

