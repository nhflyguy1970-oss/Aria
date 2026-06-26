# Source Generated with Decompyle++
# File: test_flytying_bridge.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Fly tying bridge list/suggest tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.flytying import bridge
import _pytest.assertion.rewrite, assertion
from jarvis.flytying.config import gold_recipes_path

def test_list_recipes_from_gold():
    (rows, mode) = bridge.list_recipes(limit = 5)
    if not gold_recipes_path().is_file():
        return None
    @py_assert3 = isinstance(rows, list)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py1)s, %(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(rows) if 'rows' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rows) else 'rows',
            'py2': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert3 = None
    @py_assert2 = ('browse', 'keyword', 'hybrid', 'empty')
    @py_assert1 = mode in @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert1,), ('%(py0)s in %(py3)s',), (mode, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(mode) if 'mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(mode) else 'mode',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    if rows:
        @py_assert0 = 'name'
        @py_assert3 = rows[0]
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
        return None


def test_suggest_from_materials_empty():
    @py_assert1 = bridge.suggest_from_materials
    @py_assert3 = []
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = []
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.suggest_from_materials\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(bridge) if 'bridge' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bridge) else 'bridge',
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


def test_list_recipes_searches_steps():
    (rows, _mode) = bridge.list_recipes(q = 'pheasant tail', limit = 5)
    if not gold_recipes_path().is_file():
        return None
    @py_assert2 = len(rows)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 >= @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('>=',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} >= %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(rows) if 'rows' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rows) else 'rows',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_search_recipes_adams():
    if not gold_recipes_path().is_file():
        return None
    rows = bridge.search_recipes('adams', limit = 5)
    @py_assert2 = len(rows)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 >= @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('>=',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} >= %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(rows) if 'rows' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rows) else 'rows',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = 'adams'
    @py_assert4 = []
    @py_assert5 = rows[0]
    @py_assert7 = @py_assert5.get
    @py_assert9 = 'name'
    @py_assert11 = @py_assert7(@py_assert9)
    @py_assert3 = @py_assert11
    if not @py_assert11:
        @py_assert14 = ''
        @py_assert3 = @py_assert14
    @py_assert19 = @py_assert3.lower
    @py_assert21 = @py_assert19()
    @py_assert2 = @py_assert0 in @py_assert21
# WARNING: Decompyle incomplete

