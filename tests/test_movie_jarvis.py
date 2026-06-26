# Source Generated with Decompyle++
# File: test_movie_jarvis.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for Movie Jarvis completion features.'''
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion

def test_good_morning_routes_to_briefing(monkeypatch):
    monkeypatch.setenv('JARVIS_BRIEFING', '1')
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    @py_assert0 = route('good morning', SessionContext())['action']
    @py_assert3 = 'morning_briefing'
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


def test_document_search_route():
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    intent = route('search my documents warranty coverage', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'document_search'
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


def test_requires_jarvis_restart():
    requires_jarvis_restart = requires_jarvis_restart
    import jarvis.upgrade_wizard
    @py_assert1 = [
        {
            'path': 'jarvis/gui/static/app.js' }]
    @py_assert3 = requires_jarvis_restart(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(requires_jarvis_restart) if 'requires_jarvis_restart' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(requires_jarvis_restart) else 'requires_jarvis_restart',
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
    @py_assert1 = [
        {
            'path': 'tests/test_foo.py' }]
    @py_assert3 = requires_jarvis_restart(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(requires_jarvis_restart) if 'requires_jarvis_restart' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(requires_jarvis_restart) else 'requires_jarvis_restart',
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


def test_run_whitelisted_script_rejects_paths(data_dir, monkeypatch):
    SCRIPTS_DIR = SCRIPTS_DIR
    run_whitelisted_script = run_whitelisted_script
    import jarvis.remote_control
    monkeypatch.setattr('jarvis.remote_control.SCRIPTS_DIR', data_dir / 'scripts')
    SCRIPTS_DIR.mkdir(parents = True, exist_ok = True)
    (ok, msg) = run_whitelisted_script('../etc/passwd')
    @py_assert2 = False
    @py_assert1 = ok is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (ok, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(ok) if 'ok' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ok) else 'ok',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert2 = 'simple'
    @py_assert6 = msg.lower
    @py_assert8 = @py_assert6()
    @py_assert4 = @py_assert2 in @py_assert8
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert13 = 'path'
        @py_assert17 = msg.lower
        @py_assert19 = @py_assert17()
        @py_assert15 = @py_assert13 in @py_assert19
        @py_assert0 = @py_assert15
# WARNING: Decompyle incomplete


def test_environment_snapshot():
    snapshot = snapshot
    import jarvis.environment
    snap = snapshot(include_resources = False)
    @py_assert0 = 'profile'
    @py_assert2 = @py_assert0 in snap
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, snap)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(snap) if 'snap' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(snap) else 'snap' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'disk_free_gb'
    @py_assert2 = @py_assert0 in snap
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, snap)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(snap) if 'snap' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(snap) else 'snap' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_ics_parse_events():
    date = date
    import datetime
    _parse_ics_events = _parse_ics_events
    import jarvis.calendar_ics
    ics = 'BEGIN:VCALENDAR\nBEGIN:VEVENT\nSUMMARY:Team standup\nDTSTART:20260608T093000\nEND:VEVENT\nEND:VCALENDAR'
    events = _parse_ics_events(ics, date(2026, 6, 8))
    @py_assert2 = len(events)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(events) if 'events' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(events) else 'events',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = events[0]['summary']
    @py_assert3 = 'Team standup'
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
    @py_assert0 = events[0]['time']
    @py_assert3 = '09:30'
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


def test_enqueue_fix_tests(monkeypatch):
    monkeypatch.setenv('JARVIS_BRIEFING', '1')
    submit_fix_tests = submit_fix_tests
    import jarvis.coding_jobs
    
    class FakeAssistant:
        
        def _coding_fix_tests(self, params, message):
            return {
                'ok': True,
                'message': 'done' }


    job_id = submit_fix_tests(FakeAssistant(), {
        'path': 'foo.py' }, 'debug until tests pass')
    @py_assert2 = len(job_id)
    @py_assert5 = 12
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(job_id) if 'job_id' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(job_id) else 'job_id',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None

