# Source Generated with Decompyle++
# File: test_p0_planner.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for P0 planner and HA fuzzy helpers.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
from pathlib import Path
import pytest
planner_db = (lambda tmp_path, monkeypatch: db = tmp_path / 'planner.db'monkeypatch.setattr('jarvis.planner_store.DB_PATH', db)monkeypatch.setattr('jarvis.planner_store._init_db', (lambda : pass))
    ps = planner_store
    import jarvis.planner_store
    conn = ps._conn()
    conn.executescript('\n            CREATE TABLE IF NOT EXISTS tasks (\n                id TEXT PRIMARY KEY, text TEXT NOT NULL, completed INTEGER DEFAULT 0, created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS events (\n                id TEXT PRIMARY KEY, title TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT,\n                description TEXT, created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS timers (\n                id TEXT PRIMARY KEY, label TEXT, ends_at TEXT NOT NULL, created_at TEXT NOT NULL\n            );\n            CREATE TABLE IF NOT EXISTS alarms (\n                id TEXT PRIMARY KEY, label TEXT, fire_at TEXT NOT NULL,\n                enabled INTEGER DEFAULT 1, fired INTEGER DEFAULT 0, created_at TEXT NOT NULL\n            );\n            ')
    None(None, None)
    return ps
    with None:
        if not None:
            pass
    return ps
)()

def test_planner_task_and_timer(planner_db):
    ps = planner_db
    task = ps.add_task('buy milk')
    @py_assert0 = task['text']
    @py_assert3 = 'buy milk'
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
    @py_assert2 = ps.list_tasks
    @py_assert4 = @py_assert2()
    @py_assert6 = len(@py_assert4)
    @py_assert9 = 1
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py0)s(%(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py1)s.list_tasks\n}()\n})\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    timer = ps.set_timer('5 minutes', 'tea')
    @py_assert0 = timer['remaining_seconds']
    @py_assert3 = 299
    @py_assert2 = @py_assert0 >= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('>=',), (@py_assert2,), ('%(py1)s >= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert2 = ps.active_timers
    @py_assert4 = @py_assert2()
    @py_assert6 = len(@py_assert4)
    @py_assert9 = 1
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py0)s(%(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py1)s.active_timers\n}()\n})\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_parse_duration(planner_db):
    ps = planner_db
    @py_assert1 = ps._parse_duration
    @py_assert3 = '10 minutes'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 600
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._parse_duration\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
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
    @py_assert1 = ps._parse_duration
    @py_assert3 = '1 hour'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 3600
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._parse_duration\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
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


def test_tick_alarms_notifies_expired_timer(planner_db, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_events_for_day_iso_datetime(planner_db):
    ps = planner_db
    ps.add_event('Meeting', when = '2026-06-19', time_str = '14:30')
    day_events = ps.events_for_day('2026-06-19')
    @py_assert2 = len(day_events)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(day_events) if 'day_events' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(day_events) else 'day_events',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = day_events[0]['title']
    @py_assert3 = 'Meeting'
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
    @py_assert0 = day_events[0]['start_time']
    @py_assert2 = @py_assert0.startswith
    @py_assert4 = '2026-06-19T14:30'
    @py_assert6 = @py_assert2(@py_assert4)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.startswith\n}(%(py5)s)\n}' % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_complete_task_no_fuzzy_match(planner_db):
    ps = planner_db
    ps.add_task('buy milk')
    ps.add_task('buy milkshake')
    @py_assert1 = ps.complete_task
    @py_assert3 = 'milk'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.complete_task\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
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
    @py_assert2 = ps.list_tasks
    @py_assert4 = @py_assert2()
    @py_assert6 = len(@py_assert4)
    @py_assert9 = 2
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py0)s(%(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py1)s.list_tasks\n}()\n})\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    @py_assert1 = ps.complete_task
    @py_assert3 = 'buy milk'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.complete_task\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
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
    @py_assert2 = ps.list_tasks
    @py_assert4 = @py_assert2()
    @py_assert6 = len(@py_assert4)
    @py_assert9 = 1
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py0)s(%(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py1)s.list_tasks\n}()\n})\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(ps) if 'ps' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ps) else 'ps',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    @py_assert0 = ps.list_tasks()[0]['text']
    @py_assert3 = 'buy milkshake'
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


def test_add_event_tomorrow_with_time(planner_db, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_ha_aliases_resolve(tmp_path, monkeypatch):
    alias_file = tmp_path / 'ha_aliases.json'
    alias_file.write_text(json.dumps({
        'aliases': {
            'office': [
                'light.left',
                'light.right'] } }), encoding = 'utf-8')
    monkeypatch.setattr('jarvis.ha_aliases.ALIASES_FILE', alias_file)
    resolve_alias = resolve_alias
    import jarvis.ha_aliases
    @py_assert1 = 'office'
    @py_assert3 = resolve_alias(@py_assert1)
    @py_assert6 = [
        'light.left',
        'light.right']
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_alias) if 'resolve_alias' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_alias) else 'resolve_alias',
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


def test_tool_permissions_defaults():
    get_permissions = get_permissions
    import jarvis.tool_permissions
    perms = get_permissions()
    @py_assert0 = perms['write_file']
    @py_assert3 = 'ask'
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
    @py_assert0 = perms['ha_control']
    @py_assert3 = 'never'
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


def test_system_info_builds():
    build_system_info = build_system_info
    import jarvis.system_info
    info = build_system_info()
    @py_assert0 = 'greeting'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'feature_flags'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_checklist():
    run_checklist = run_checklist
    import jarvis.p0_checklist
    result = run_checklist()
    @py_assert0 = 'checks'
    @py_assert2 = @py_assert0 in result
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, result)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = result['total']
    @py_assert3 = 3
    @py_assert2 = @py_assert0 >= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('>=',), (@py_assert2,), ('%(py1)s >= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'passed_required'
    @py_assert2 = @py_assert0 in result
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, result)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'total_required'
    @py_assert2 = @py_assert0 in result
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, result)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = result['passed_required']
    @py_assert3 = result['total_required']
    @py_assert2 = @py_assert0 <= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('<=',), (@py_assert2,), ('%(py1)s <= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None

