# Source Generated with Decompyle++
# File: test_home_assistant.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Home Assistant integration tests.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.home_assistant import activate_scene, check_connection, control_entity, find_entities, ha_enabled, home_summary, parse_control, parse_scene, verify_automation_secret
ha_env = (lambda monkeypatch: pass# WARNING: Decompyle incomplete
)()

def test_ha_enabled_requires_url_and_token(monkeypatch):
    monkeypatch.delenv('JARVIS_HA_URL', raising = False)
    monkeypatch.delenv('JARVIS_HA_TOKEN', raising = False)
    @py_assert1 = ha_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ha_enabled) if 'ha_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ha_enabled) else 'ha_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_parse_control():
    @py_assert1 = 'turn off the porch light'
    @py_assert3 = parse_control(@py_assert1)
    @py_assert6 = {
        'action': 'off',
        'target': 'porch light' }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_control) if 'parse_control' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_control) else 'parse_control',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'switch living room on'
    @py_assert3 = parse_control(@py_assert1)
    @py_assert6 = {
        'action': 'on',
        'target': 'living room' }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_control) if 'parse_control' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_control) else 'parse_control',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_parse_scene_and_leave(ha_env):
    @py_assert1 = 'activate scene movie night'
    @py_assert3 = parse_scene(@py_assert1)
    @py_assert6 = 'movie night'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_scene) if 'parse_scene' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_scene) else 'parse_scene',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = "I'm heading out"
    @py_assert3 = parse_scene(@py_assert1)
    @py_assert6 = 'scene.leaving'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_scene) if 'parse_scene' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_scene) else 'parse_scene',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'good night house'
    @py_assert3 = parse_scene(@py_assert1)
    @py_assert6 = 'scene.leaving'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_scene) if 'parse_scene' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_scene) else 'parse_scene',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_find_entities_fuzzy(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_find_entities_with_mock_states(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_control_entity_off_pauses_sunlight(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_control_entity_mocked(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_entity_is_available_skips_restored_ghosts(ha_env):
    _fuzzy_match_entities = _fuzzy_match_entities
    control_entity = control_entity
    entity_is_available = entity_is_available
    import jarvis.home_assistant
    ghost = {
        'entity_id': 'light.table_lamp',
        'state': 'unavailable',
        'attributes': {
            'restored': True,
            'friendly_name': 'Table lamp' } }
    live = {
        'entity_id': 'light.kitchen',
        'state': 'on',
        'attributes': {
            'friendly_name': 'Kitchen' } }
    @py_assert2 = entity_is_available(ghost)
    @py_assert5 = False
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(entity_is_available) if 'entity_is_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(entity_is_available) else 'entity_is_available',
            'py1': @pytest_ar._saferepr(ghost) if 'ghost' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ghost) else 'ghost',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert2 = entity_is_available(live)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(entity_is_available) if 'entity_is_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(entity_is_available) else 'entity_is_available',
            'py1': @pytest_ar._saferepr(live) if 'live' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(live) else 'live',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_fuzzy_match_skips_unavailable_lights(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_fuzzy_match_excludes_printer_sensors(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_control_entity_office_light_no_false_match(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_activate_scene_mocked(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_check_connection_waits_when_api_down(monkeypatch, ha_env):
    pass
# WARNING: Decompyle incomplete


def test_check_connection_version_from_config(ha_env, monkeypatch):
    
    def fake_request(method, path, body, timeout = (None, 15)):
        if path == '/api/':
            return {
                'message': 'API running.' }
        if None == '/api/config':
            return {
                'version': '2026.5.2' }

    monkeypatch.setattr('jarvis.home_assistant._request', fake_request)
    result = check_connection()
    @py_assert0 = result['ok']
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
    @py_assert0 = result['version']
    @py_assert3 = '2026.5.2'
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


def test_home_summary_mocked(ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_verify_automation_secret(ha_env):
    @py_assert1 = 'hook-secret'
    @py_assert3 = verify_automation_secret(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(verify_automation_secret) if 'verify_automation_secret' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(verify_automation_secret) else 'verify_automation_secret',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'wrong'
    @py_assert3 = verify_automation_secret(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(verify_automation_secret) if 'verify_automation_secret' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(verify_automation_secret) else 'verify_automation_secret',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_router_ha_routes(ha_env):
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    session = SessionContext()
    @py_assert0 = route('house status', session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route('home status', session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route('status of my home', session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route('whats on at home', session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route("what's on at home?", session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route('turn off the kitchen light', session)['action']
    @py_assert3 = 'ha_control'
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
    @py_assert0 = route('activate scene goodnight', session)['action']
    @py_assert3 = 'ha_scene'
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


def test_router_ha_routes_without_token(monkeypatch):
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    monkeypatch.delenv('JARVIS_HA_TOKEN', raising = False)
    monkeypatch.setenv('JARVIS_HA_ENABLED', '1')
    session = SessionContext()
    @py_assert0 = route('what lights are on', session)['action']
    @py_assert3 = 'ha_status'
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
    @py_assert0 = route('check light status', session)['action']
    @py_assert3 = 'ha_status'
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


def test_automation_inbound_chat(chat_app, ha_env):
    res = chat_app.post('/api/automation/inbound?secret=hook-secret', json = {
        'action': 'chat',
        'message': 'house status' })
    @py_assert1 = res.status_code
    @py_assert4 = 200
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    data = res.json()
    @py_assert1 = []
    @py_assert3 = data.get
    @py_assert5 = 'ok'
    @py_assert7 = @py_assert3(@py_assert5)
    @py_assert10 = True
    @py_assert9 = @py_assert7 is @py_assert10
    @py_assert0 = @py_assert9
    if not @py_assert9:
        @py_assert16 = data.get
        @py_assert18 = 'action'
        @py_assert20 = @py_assert16(@py_assert18)
        @py_assert23 = 'ha_status'
        @py_assert22 = @py_assert20 == @py_assert23
        @py_assert0 = @py_assert22
# WARNING: Decompyle incomplete


def test_automation_inbound_rejects_bad_secret(chat_app, ha_env):
    res = chat_app.post('/api/automation/inbound', headers = {
        'X-Jarvis-Automation-Secret': 'nope' }, json = {
        'action': 'chat',
        'message': 'hi' })
    @py_assert1 = res.status_code
    @py_assert4 = 401
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_automation_inbound_sunlight_tick(chat_app, ha_env, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_automation_inbound_disabled_without_secret(chat_app, monkeypatch):
    monkeypatch.setenv('JARVIS_AUTOMATION_SECRET', '')
    res = chat_app.post('/api/automation/inbound', json = {
        'action': 'chat',
        'message': 'hi' })
    @py_assert1 = res.status_code
    @py_assert4 = 503
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_parse_ha_token_message():
    parse_ha_token_message = parse_ha_token_message
    import jarvis.home_assistant
    @py_assert1 = 'set home assistant token: eyJhbG.test.sig'
    @py_assert3 = parse_ha_token_message(@py_assert1)
    @py_assert6 = 'eyJhbG.test.sig'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_ha_token_message) if 'parse_ha_token_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_ha_token_message) else 'parse_ha_token_message',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'eyJhbGciOiJIUzI1NiJ9.abc.defghijklmnopqrstuvwxyz'
    @py_assert3 = parse_ha_token_message(@py_assert1)
    @py_assert6 = 'eyJhbGciOiJIUzI1NiJ9.abc.defghijklmnopqrstuvwxyz'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_ha_token_message) if 'parse_ha_token_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_ha_token_message) else 'parse_ha_token_message',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_router_ha_set_token():
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    intent = route('set ha token: eyJhbG.test.signature', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'ha_set_token'
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
    @py_assert0 = intent['params']['token']
    @py_assert3 = 'eyJhbG.test.signature'
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


def test_normalize_ha_token():
    normalize_ha_token = normalize_ha_token
    import jarvis.home_assistant
    @py_assert1 = '  "eyJabc.def.ghi"  '
    @py_assert3 = normalize_ha_token(@py_assert1)
    @py_assert6 = 'eyJabc.def.ghi'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_ha_token) if 'normalize_ha_token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_ha_token) else 'normalize_ha_token',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'Bearer eyJx.y.z'
    @py_assert3 = normalize_ha_token(@py_assert1)
    @py_assert6 = 'eyJx.y.z'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_ha_token) if 'normalize_ha_token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_ha_token) else 'normalize_ha_token',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'eyJx\ny\nz'
    @py_assert3 = normalize_ha_token(@py_assert1)
    @py_assert6 = 'eyJxyz'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_ha_token) if 'normalize_ha_token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_ha_token) else 'normalize_ha_token',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_test_connection_401_message():
    test_connection = test_connection
    import jarvis.home_assistant
    result = test_connection(url = 'http://127.0.0.1:8123', token = 'not-a-real-token')
    @py_assert0 = result['ok']
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
    @py_assert1 = []
    @py_assert2 = '401'
    @py_assert5 = result['message']
    @py_assert4 = @py_assert2 in @py_assert5
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert10 = 'Invalid'
        @py_assert13 = result['message']
        @py_assert12 = @py_assert10 in @py_assert13
        @py_assert0 = @py_assert12
# WARNING: Decompyle incomplete


def test_save_config(data_dir, monkeypatch):
    env_file = data_dir / 'jarvis.env'
    monkeypatch.setattr('jarvis.env_loader.ENV_FILE', env_file)
    save_config = save_config
    status_payload = status_payload
    import jarvis.home_assistant
    result = save_config(url = 'http://127.0.0.1:8123', enabled = True, ensure_automation_secret = True)
    @py_assert0 = 'JARVIS_HA_URL'
    @py_assert4 = result.get
    @py_assert6 = 'changed'
    @py_assert8 = []
    @py_assert10 = @py_assert4(@py_assert6, @py_assert8)
    @py_assert2 = @py_assert0 in @py_assert10
    if not @py_assert2:
        @py_format12 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py11)s\n{%(py11)s = %(py5)s\n{%(py5)s = %(py3)s.get\n}(%(py7)s, %(py9)s)\n}',), (@py_assert0, @py_assert10)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
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
    @py_assert1 = env_file.is_file
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(env_file) if 'env_file' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(env_file) else 'env_file',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    payload = status_payload()
    @py_assert0 = payload['url']
    @py_assert3 = 'http://127.0.0.1:8123'
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
    @py_assert0 = payload['automation_secret_set']
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

