# Source Generated with Decompyle++
# File: test_p1_voice.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''P1 voice routing and sessions tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
from pathlib import Path
import pytest

def test_brain_routing_deep():
    needs_deep_thinking = needs_deep_thinking
    select_chat_model = select_chat_model
    import jarvis.brain_routing
    @py_assert1 = 'explain why recursion overflows'
    @py_assert3 = needs_deep_thinking(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(needs_deep_thinking) if 'needs_deep_thinking' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(needs_deep_thinking) else 'needs_deep_thinking',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = 'hello'
    @py_assert3 = needs_deep_thinking(@py_assert1)
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(needs_deep_thinking) if 'needs_deep_thinking' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(needs_deep_thinking) else 'needs_deep_thinking',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    m = select_chat_model('hello', { })
    if not m:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(m) if 'm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(m) else 'm' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = 'hello'
    @py_assert3 = { }
    @py_assert5 = 'session-pick:7b'
    @py_assert7 = select_chat_model(@py_assert1, @py_assert3, session_chat_model = @py_assert5)
    @py_assert10 = 'session-pick:7b'
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py0)s(%(py2)s, %(py4)s, session_chat_model=%(py6)s)\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(select_chat_model) if 'select_chat_model' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(select_chat_model) else 'select_chat_model',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None


def test_local_router_parse():
    _parse_json = _parse_json
    import jarvis.local_router
    raw = '{"action":"planner_set_timer","params":{"duration":"5 minutes"},"thinking":"timer"}'
    data = _parse_json(raw)
    @py_assert1 = []
    @py_assert0 = data
    if data:
        @py_assert4 = data['action']
        @py_assert7 = 'planner_set_timer'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_chat_sessions(tmp_path, monkeypatch):
    db = tmp_path / 'chat_sessions.db'
    monkeypatch.setattr('jarvis.chat_sessions.DB_PATH', db)
    monkeypatch.setattr('jarvis.chat_sessions._init', (lambda : pass))
    cs = chat_sessions
    import jarvis.chat_sessions
    conn = cs._conn()
    conn.executescript('\n            CREATE TABLE IF NOT EXISTS sessions (\n                id TEXT PRIMARY KEY, title TEXT NOT NULL, branch_id TEXT,\n                pinned INTEGER DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL\n            );\n            ')
    None(None, None)
    s = cs.create_session('Test thread')
    @py_assert0 = s['title']
    @py_assert3 = 'Test thread'
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
    @py_assert1 = cs.pin_session
    @py_assert3 = s['id']
    @py_assert5 = True
    @py_assert7 = @py_assert1(@py_assert3, @py_assert5)
    if not @py_assert7:
        @py_format9 = 'assert %(py8)s\n{%(py8)s = %(py2)s\n{%(py2)s = %(py0)s.pin_session\n}(%(py4)s, %(py6)s)\n}' % {
            'py0': @pytest_ar._saferepr(cs) if 'cs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cs) else 'cs',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    return None
    with None:
        if not None:
            pass
    continue


def test_router_training_export(tmp_path, monkeypatch):
    out = tmp_path / 'router_training.jsonl'
    monkeypatch.setattr('jarvis.router_training.OUT', out)
    export_training_jsonl = export_training_jsonl
    import jarvis.router_training
    path = export_training_jsonl()
    @py_assert1 = path.exists
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.exists\n}()\n}' % {
            'py0': @pytest_ar._saferepr(path) if 'path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(path) else 'path',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    lines = path.read_text(encoding = 'utf-8').strip().splitlines()
    @py_assert2 = len(lines)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 >= @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('>=',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} >= %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(lines) if 'lines' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(lines) else 'lines',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    row = json.loads(lines[0])
    @py_assert0 = 'messages'
    @py_assert2 = @py_assert0 in row
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, row)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(row) if 'row' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(row) else 'row' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_conversation_truncate():
    Conversation = Conversation
    import jarvis.conversation
    c = Conversation('sys')
    c.add_user('hi')
    c.add_assistant('long reply')
    @py_assert1 = c.truncate_last_assistant
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.truncate_last_assistant\n}()\n}' % {
            'py0': @pytest_ar._saferepr(c) if 'c' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(c) else 'c',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert0 = 'interrupted'
    @py_assert3 = c.messages[-1]['content']
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


def test_voice_duplex_modes():
    voice_duplex = voice_duplex
    import jarvis
    @py_assert1 = voice_duplex.ignore_wake_during_playback
    @py_assert3 = @py_assert1.__name__
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.ignore_wake_during_playback\n}.__name__\n}' % {
            'py0': @pytest_ar._saferepr(voice_duplex) if 'voice_duplex' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(voice_duplex) else 'voice_duplex',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_stt_routes_whisper_by_default(monkeypatch):
    monkeypatch.setenv('JARVIS_REALTIMESTT', '0')
    stt_backend = stt_backend
    import jarvis.voice_settings
    @py_assert1 = stt_backend()
    @py_assert4 = 'whisper'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(stt_backend) if 'stt_backend' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(stt_backend) else 'stt_backend',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_stt_status_reports_realtimestt(monkeypatch):
    monkeypatch.setenv('JARVIS_REALTIMESTT', '0')
    stt_status = stt_status
    import jarvis.stt
    st = stt_status()
    @py_assert0 = st['backend']
    @py_assert3 = 'whisper'
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
    @py_assert0 = 'realtimestt'
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
    @py_assert0 = st['realtimestt_enabled']
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


def test_emit_stt_partial_publishes_ws(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_save_voice_settings_rejects_missing_realtimestt(monkeypatch):
    monkeypatch.setenv('JARVIS_REALTIMESTT', '1')
    load_voice_settings = load_voice_settings
    save_voice_settings = save_voice_settings
    import jarvis.voice_settings
    saved = save_voice_settings({
        'stt_backend': 'realtimestt' })
    @py_assert1 = []
    @py_assert2 = saved['stt_backend']
    @py_assert5 = 'whisper'
    @py_assert4 = @py_assert2 == @py_assert5
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert10 = load_voice_settings()['stt_backend']
        @py_assert13 = ('whisper', 'realtimestt')
        @py_assert12 = @py_assert10 in @py_assert13
        @py_assert0 = @py_assert12
# WARNING: Decompyle incomplete


def test_upgrade_deps_report():
    dependency_report = dependency_report
    dependency_summary = dependency_summary
    import jarvis.upgrade_deps
    report = dependency_report()
    @py_assert1 = []
    @py_assert2 = 'pip'
    @py_assert4 = @py_assert2 in report
    @py_assert0 = @py_assert4
    if @py_assert4:
        @py_assert9 = 'ollama_models'
        @py_assert11 = @py_assert9 in report
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_upgrade_deps_functiongemma_hf(monkeypatch):
    dependency_report = dependency_report
    import jarvis.upgrade_deps
    monkeypatch.setattr('jarvis.upgrade_deps._functiongemma_installed', (lambda : {
'installed': True,
'resolved': '/models/fg',
'backend': 'hf' }))
    monkeypatch.setattr('jarvis.upgrade_deps._ollama_model_status', (lambda model, fallbacks = (None,): {
'installed': False,
'resolved': None }))
    report = dependency_report()
    fg = (lambda .0: pass# WARNING: Decompyle incomplete
)(report['ollama_models']())
    @py_assert0 = fg['installed']
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
    @py_assert1 = fg.get
    @py_assert3 = 'backend'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'hf'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(fg) if 'fg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fg) else 'fg',
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
    @py_assert1 = []
    @py_assert2 = 'functiongemma'
    @py_assert5 = ' '
    @py_assert7 = @py_assert5.join
    @py_assert9 = report['missing']['ollama_pull']
    @py_assert11 = @py_assert7(@py_assert9)
    @py_assert13 = @py_assert11.lower
    @py_assert15 = @py_assert13()
    @py_assert4 = @py_assert2 not in @py_assert15
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert20 = fg['installed']
        @py_assert0 = @py_assert20
# WARNING: Decompyle incomplete

