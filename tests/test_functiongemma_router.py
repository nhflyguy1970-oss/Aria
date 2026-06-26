# Source Generated with Decompyle++
# File: test_functiongemma_router.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''FunctionGemma router tests (P1 #23).'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import sys = import _pytest.assertion.rewrite, assertion

def test_parse_function_call_timer():
    parse_function_call = parse_function_call
    import jarvis.functiongemma_router
    raw = '<start_function_call>call:planner_set_timer{duration: 10 minutes}<end_function_call>'
    data = parse_function_call(raw)
    @py_assert2 = None
    @py_assert1 = data is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (data, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = data['action']
    @py_assert3 = 'planner_set_timer'
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
    @py_assert0 = data['params']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'duration'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = '10 minutes'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_parse_function_call_thinking():
    parse_function_call = parse_function_call
    import jarvis.functiongemma_router
    data = parse_function_call('<start_function_call>call:thinking{}<end_function_call>')
    @py_assert0 = data['action']
    @py_assert3 = 'chat'
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
    @py_assert0 = data['params']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'thinking_mode'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = 'deep'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_build_tool_schemas():
    build_tool_schemas = build_tool_schemas
    import jarvis.functiongemma_router
    schemas = build_tool_schemas(limit = 20)
# WARNING: Decompyle incomplete


def test_try_functiongemma_route_mock(monkeypatch):
    try_functiongemma_route = try_functiongemma_route
    import jarvis.functiongemma_router
    SessionContext = SessionContext
    import jarvis.session
    monkeypatch.setenv('JARVIS_LOCAL_ROUTER', '1')
    monkeypatch.setattr('jarvis.functiongemma_router._load_hf', (lambda : True))
    monkeypatch.setattr('jarvis.functiongemma_router._generate_hf', (lambda _msg, _tools: '<start_function_call>call:planner_today{}<end_function_call>'))
    hit = try_functiongemma_route("what's on my planner today", SessionContext())
    @py_assert2 = None
    @py_assert1 = hit is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (hit, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(hit) if 'hit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hit) else 'hit',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = hit['action']
    @py_assert3 = 'planner_today'
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
    @py_assert0 = hit['router']
    @py_assert3 = 'functiongemma'
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


def test_local_router_auto_fallback(monkeypatch):
    try_local_route = try_local_route
    import jarvis.local_router
    SessionContext = SessionContext
    import jarvis.session
    monkeypatch.setenv('JARVIS_LOCAL_ROUTER', '1')
    monkeypatch.setenv('JARVIS_ROUTER_BACKEND', 'auto')
    monkeypatch.setattr('jarvis.functiongemma_router.try_functiongemma_route', (lambda : pass))
    monkeypatch.setattr('jarvis.llm.ask_with_system', (lambda : '{"action":"chat","params":{},"thinking":"chat"}'))
    hit = try_local_route('tell me a joke about databases', SessionContext())
    @py_assert2 = None
    @py_assert1 = hit is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (hit, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(hit) if 'hit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hit) else 'hit',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = hit['router']
    @py_assert3 = 'local'
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


def test_resolve_device_rocm_defaults_cpu(monkeypatch):
    import types
    fg = functiongemma_router
    import jarvis
    monkeypatch.delenv('JARVIS_FUNCTIONGEMMA_DEVICE', raising = False)
    fake_torch = types.SimpleNamespace(cuda = types.SimpleNamespace(is_available = (lambda : True)), version = types.SimpleNamespace(hip = '6.0'))
    monkeypatch.setitem(sys.modules, 'torch', fake_torch)
    @py_assert1 = fg._resolve_device
    @py_assert3 = @py_assert1()
    @py_assert6 = 'cpu'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s._resolve_device\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(fg) if 'fg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fg) else 'fg',
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


def test_fallback_on_parse_failure(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_fallback_on_load_failure(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_export_functiongemma_jsonl(tmp_path, monkeypatch):
    out = tmp_path / 'fg.jsonl'
    monkeypatch.setattr('jarvis.router_training.FG_OUT', out)
    export_functiongemma_jsonl = export_functiongemma_jsonl
    import jarvis.router_training
    path = export_functiongemma_jsonl()
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
    @py_assert1 = path.read_text
    @py_assert3 = 'utf-8'
    @py_assert5 = @py_assert1(encoding = @py_assert3)
    @py_assert7 = @py_assert5.strip
    @py_assert9 = @py_assert7()
    if not @py_assert9:
        @py_format11 = 'assert %(py10)s\n{%(py10)s = %(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.read_text\n}(encoding=%(py4)s)\n}.strip\n}()\n}' % {
            'py0': @pytest_ar._saferepr(path) if 'path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(path) else 'path',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None

