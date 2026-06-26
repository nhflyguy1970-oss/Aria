# Source Generated with Decompyle++
# File: test_flytying_index.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Fly tying gold index tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.flytying import index
import _pytest.assertion.rewrite, assertion
from jarvis.flytying.config import gold_recipes_path

def test_find_recipe_exact_name():
    if not gold_recipes_path().is_file():
        return None
    recipe = recipe_index.find_recipe('Adams')
    @py_assert2 = None
    @py_assert1 = recipe is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (recipe, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(recipe) if 'recipe' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe) else 'recipe',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = 'adams'
    @py_assert4 = recipe_index._recipe_name
    @py_assert7 = @py_assert4(recipe)
    @py_assert9 = @py_assert7.lower
    @py_assert11 = @py_assert9()
    @py_assert2 = @py_assert0 in @py_assert11
    if not @py_assert2:
        @py_format13 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py12)s\n{%(py12)s = %(py10)s\n{%(py10)s = %(py8)s\n{%(py8)s = %(py5)s\n{%(py5)s = %(py3)s._recipe_name\n}(%(py6)s)\n}.lower\n}()\n}',), (@py_assert0, @py_assert11)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(recipe_index) if 'recipe_index' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe_index) else 'recipe_index',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py6': @pytest_ar._saferepr(recipe) if 'recipe' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe) else 'recipe',
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None


def test_find_recipe_no_loose_substring():
    if not gold_recipes_path().is_file():
        return None
    recipe = recipe_index.find_recipe('zzznomatchpattern')
    @py_assert2 = None
    @py_assert1 = recipe is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (recipe, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(recipe) if 'recipe' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe) else 'recipe',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_search_adams():
    if not gold_recipes_path().is_file():
        return None
    (rows, mode) = recipe_index.search('adams', limit = 5)
    @py_assert2 = 'keyword'
    @py_assert1 = mode == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (mode, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(mode) if 'mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(mode) else 'mode',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
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


def test_list_recipes_returns_tuple():
    bridge = bridge
    import jarvis.flytying
    if not gold_recipes_path().is_file():
        return None
    (rows, mode) = bridge.list_recipes(limit = 3)
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


def test_matches_query_tokens():
    blob = recipe_index._search_blob({
        'name': 'Blue Wing Olive parachute',
        'type': 'dry',
        'materials': [
            'CDC',
            'olive thread'],
        'steps': [
            'Tie in tail'] })
    @py_assert1 = recipe_index._matches_query
    @py_assert3 = 'blue wing'
    @py_assert6 = @py_assert1(@py_assert3, blob)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s._matches_query\n}(%(py4)s, %(py5)s)\n}' % {
            'py0': @pytest_ar._saferepr(recipe_index) if 'recipe_index' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe_index) else 'recipe_index',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(blob) if 'blob' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(blob) else 'blob',
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None
    @py_assert1 = recipe_index._matches_query
    @py_assert3 = 'bwo'
    @py_assert6 = @py_assert1(@py_assert3, blob)
    @py_assert9 = False
    @py_assert8 = @py_assert6 is @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('is',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s._matches_query\n}(%(py4)s, %(py5)s)\n} is %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(recipe_index) if 'recipe_index' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe_index) else 'recipe_index',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(blob) if 'blob' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(blob) else 'blob',
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
    @py_assert1 = recipe_index._matches_query
    @py_assert3 = 'olive parachute'
    @py_assert6 = @py_assert1(@py_assert3, blob)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py2)s\n{%(py2)s = %(py0)s._matches_query\n}(%(py4)s, %(py5)s)\n}' % {
            'py0': @pytest_ar._saferepr(recipe_index) if 'recipe_index' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(recipe_index) else 'recipe_index',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(blob) if 'blob' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(blob) else 'blob',
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None

