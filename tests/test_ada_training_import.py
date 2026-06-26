# Source Generated with Decompyle++
# File: test_ada_training_import.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Ada USB training row mapping for FunctionGemma export.'''
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
from jarvis.router_training import _parse_ada_row, load_ada_training_rows

def test_parse_ada_control_light():
    row = json.loads('{"messages": [{"role": "user", "content": "Turn on bedroom"}, {"role": "assistant", "tool_calls": [{"function": {"name": "control_light", "arguments": {"action": "on", "device_name": "bedroom"}}}]}]}')
    (user, call) = _parse_ada_row(row)
    @py_assert2 = 'Turn on bedroom'
    @py_assert1 = user == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (user, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(user) if 'user' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(user) else 'user',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = 'ha_control'
    @py_assert2 = @py_assert0 in call
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, call)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(call) if 'call' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(call) else 'call' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'target: bedroom'
    @py_assert2 = @py_assert0 in call
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, call)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(call) if 'call' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(call) else 'call' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'action: on'
    @py_assert2 = @py_assert0 in call
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, call)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(call) if 'call' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(call) else 'call' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_parse_ada_skips_calendar():
    row = json.loads('{"messages": [{"role": "user", "content": "Lunch Monday"}, {"role": "assistant", "tool_calls": [{"function": {"name": "create_calendar_event", "arguments": {"title": "lunch"}}}]}]}')
    @py_assert2 = _parse_ada_row(row)
    @py_assert5 = None
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(_parse_ada_row) if '_parse_ada_row' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_parse_ada_row) else '_parse_ada_row',
            'py1': @pytest_ar._saferepr(row) if 'row' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(row) else 'row',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_load_ada_rows_from_usb_if_present():
    rows = load_ada_training_rows()
    if rows:
        @py_assert1 = rows[0][0]
        @py_assert4 = isinstance(@py_assert1, str)
        if not @py_assert4:
            @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
                'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
                'py2': @pytest_ar._saferepr(@py_assert1),
                'py3': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
                'py5': @pytest_ar._saferepr(@py_assert4) }
            raise AssertionError(@pytest_ar._format_explanation(@py_format6))
        @py_assert1 = None
        @py_assert4 = None
        @py_assert0 = rows[0][1]
        @py_assert2 = @py_assert0.startswith
        @py_assert4 = 'call:'
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
        return None

