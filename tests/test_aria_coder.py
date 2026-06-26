# Source Generated with Decompyle++
# File: test_aria_coder.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for aria_coder and new MCP coding tools.'''
import builtins as @py_builtins

rewrite
from jarvis import fs
import _pytest.assertion.rewrite, assertion
from jarvis.aria_coder import _infer_path_from_pytest, list_dir, run_tests_bridge, write_file_bridge
from jarvis.cursor_bridge import MCP_TOOLS, handle_mcp_tool

def test_mcp_coder_tools_registered():
    pass
# WARNING: Decompyle incomplete


def test_list_dir(tmp_path):
    (tmp_path / 'a.py').write_text('x', encoding = 'utf-8')
    (tmp_path / 'subdir').mkdir()
    entries = list_dir('.', tmp_path)
# WARNING: Decompyle incomplete


def test_write_file_bridge(tmp_path):
    result = write_file_bridge('new.txt', 'hello', tmp_path)
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
    @py_assert1 = fs.read_file
    @py_assert3 = 'new.txt'
    @py_assert6 = @py_assert1(@py_assert3, base = tmp_path)
    @py_assert9 = 'hello'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s.read_file\n}(%(py4)s, base=%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(fs) if 'fs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fs) else 'fs',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(tmp_path) if 'tmp_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tmp_path) else 'tmp_path',
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_write_file_backup(tmp_path):
    (tmp_path / 'old.txt').write_text('v1', encoding = 'utf-8')
    result = write_file_bridge('old.txt', 'v2', tmp_path)
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
    @py_assert1 = result.get
    @py_assert3 = 'backup'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = fs.read_file
    @py_assert3 = 'old.txt'
    @py_assert6 = @py_assert1(@py_assert3, base = tmp_path)
    @py_assert9 = 'v2'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s.read_file\n}(%(py4)s, base=%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(fs) if 'fs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fs) else 'fs',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(tmp_path) if 'tmp_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tmp_path) else 'tmp_path',
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_infer_path_from_pytest():
    out = 'FAILED tests/test_foo.py::test_bar - AssertionError'
    @py_assert2 = _infer_path_from_pytest(out)
    @py_assert5 = 'tests/test_foo.py'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(_infer_path_from_pytest) if '_infer_path_from_pytest' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_infer_path_from_pytest) else '_infer_path_from_pytest',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_normalize_self_fix_task():
    normalize_self_fix_task = normalize_self_fix_task
    import jarvis.aria_coder
    @py_assert1 = 'fix aria'
    @py_assert3 = normalize_self_fix_task(@py_assert1)
    @py_assert6 = ''
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_self_fix_task) if 'normalize_self_fix_task' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_self_fix_task) else 'normalize_self_fix_task',
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
    @py_assert1 = 'fix aria and apply'
    @py_assert3 = normalize_self_fix_task(@py_assert1)
    @py_assert6 = ''
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_self_fix_task) if 'normalize_self_fix_task' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_self_fix_task) else 'normalize_self_fix_task',
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
    @py_assert1 = 'fix aria: broken imports in server'
    @py_assert3 = normalize_self_fix_task(@py_assert1)
    @py_assert6 = 'broken imports in server'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_self_fix_task) if 'normalize_self_fix_task' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_self_fix_task) else 'normalize_self_fix_task',
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


def test_aria_self_diagnose_smoke_fast(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_aria_self_fix_routes_to_background():
    BACKGROUND_ACTIONS = BACKGROUND_ACTIONS
    import jarvis.background_jobs
    ensure_handlers_loaded = ensure_handlers_loaded
    import jarvis.handlers
    get_spec = get_spec
    import jarvis.handlers.registry
    ensure_handlers_loaded()
    @py_assert0 = 'aria_self_fix'
    @py_assert2 = @py_assert0 in BACKGROUND_ACTIONS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, BACKGROUND_ACTIONS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(BACKGROUND_ACTIONS) if 'BACKGROUND_ACTIONS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(BACKGROUND_ACTIONS) else 'BACKGROUND_ACTIONS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = 'aria_self_fix'
    @py_assert3 = get_spec(@py_assert1)
    @py_assert5 = @py_assert3.queue
    @py_assert8 = 'background'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}.queue\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(get_spec) if 'get_spec' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(get_spec) else 'get_spec',
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


def test_handle_list_dir_mcp(tmp_path):
    (tmp_path / 'x.py').write_text('1', encoding = 'utf-8')
    result = handle_mcp_tool('jarvis_list_dir', {
        'path': '.' }, tmp_path)
# WARNING: Decompyle incomplete


def test_handle_write_file_mcp(tmp_path):
    result = handle_mcp_tool('jarvis_write_file', {
        'path': 'mcp.txt',
        'content': 'via mcp' }, tmp_path)
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
    @py_assert1 = fs.read_file
    @py_assert3 = 'mcp.txt'
    @py_assert6 = @py_assert1(@py_assert3, base = tmp_path)
    @py_assert9 = 'via mcp'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s.read_file\n}(%(py4)s, base=%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(fs) if 'fs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fs) else 'fs',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(tmp_path) if 'tmp_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tmp_path) else 'tmp_path',
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_run_tests_bridge_smoke(tmp_path):
    tests = tmp_path / 'tests'
    tests.mkdir()
    (tests / 'test_ok.py').write_text('def test_ok():\n    assert 1\n', encoding = 'utf-8')
    result = run_tests_bridge('tests/', tmp_path, timeout = 60)
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

