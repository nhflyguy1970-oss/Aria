# Source Generated with Decompyle++
# File: test_flytying_features.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Fly tying aliases, user store, and search tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.flytying.aliases import expand_query
import _pytest.assertion.rewrite, assertion
from jarvis.flytying.hook_utils import parse_hook
from jarvis.flytying.substitutions import suggest_substitutions
from jarvis.flytying.user_store import add_structured_item, compose_material_name, list_materials, save_materials, toggle_favorite, update_inventory_item

def test_expand_query_bwo():
    (expanded, terms) = expand_query('bwo')
    @py_assert1 = []
    @py_assert2 = 'bwo'
    @py_assert4 = @py_assert2 in terms
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert0 = expanded
    if not @py_assert0:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert4,), ('%(py3)s in %(py5)s',), (@py_assert2, terms)) % {
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(terms) if 'terms' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(terms) else 'terms' }
        @py_format8 = '%(py7)s' % {
            'py7': @py_format6 }
        @py_assert1.append(@py_format8)
        if not @py_assert4:
            @py_format10 = '%(py9)s' % {
                'py9': @pytest_ar._saferepr(expanded) if 'expanded' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(expanded) else 'expanded' }
            @py_assert1.append(@py_format10)
        @py_format11 = @pytest_ar._format_boolop(@py_assert1, 1) % { }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert1 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert1 = []
    @py_assert2 = 'blue wing olive'
    @py_assert4 = @py_assert2 in expanded
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'baetis'
        @py_assert11 = @py_assert9 in expanded
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_parse_hook_sizes():
    p = parse_hook('size 14 dry fly hook')
    @py_assert0 = p['size_min']
    @py_assert3 = 14
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
    @py_assert0 = p['size_max']
    @py_assert3 = 14
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


def test_substitutions_cdc():
    subs = suggest_substitutions('cdc')
    if not subs:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(subs) if 'subs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(subs) else 'subs' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = subs()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_user_materials_roundtrip(tmp_path, monkeypatch):
    user_store = user_store
    import jarvis.flytying
    monkeypatch.setattr(user_store, 'MATERIALS_FILE', tmp_path / 'mats.json')
    save_materials([
        'olive dubbing',
        'grizzly hackle'])
    @py_assert0 = 'olive dubbing'
    @py_assert4 = list_materials()
    @py_assert2 = @py_assert0 in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(list_materials) if 'list_materials' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_materials) else 'list_materials',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_favorite_toggle(tmp_path, monkeypatch):
    user_store = user_store
    import jarvis.flytying
    monkeypatch.setattr(user_store, 'FAVORITES_FILE', tmp_path / 'fav.json')
    r1 = toggle_favorite('recipe-1')
    @py_assert0 = r1['favorited']
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
    r2 = toggle_favorite('recipe-1')
    @py_assert0 = r2['favorited']
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


def test_unified_search_empty():
    unified_search = unified_search
    import jarvis.flytying.search
    out = unified_search('', limit = 3)
    @py_assert0 = out['ok']
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
    @py_assert0 = out['search_mode']
    @py_assert3 = ('browse', 'empty', 'keyword')
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


def test_compose_material_name():
    @py_assert1 = 'dry hook'
    @py_assert3 = 'olive'
    @py_assert5 = '14'
    @py_assert7 = 'Uni'
    @py_assert9 = compose_material_name(@py_assert1, color = @py_assert3, size = @py_assert5, brand = @py_assert7)
    @py_assert12 = 'olive 14 dry hook (Uni)'
    @py_assert11 = @py_assert9 == @py_assert12
    if not @py_assert11:
        @py_format14 = @pytest_ar._call_reprcompare(('==',), (@py_assert11,), ('%(py10)s\n{%(py10)s = %(py0)s(%(py2)s, color=%(py4)s, size=%(py6)s, brand=%(py8)s)\n} == %(py13)s',), (@py_assert9, @py_assert12)) % {
            'py0': @pytest_ar._saferepr(compose_material_name) if 'compose_material_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(compose_material_name) else 'compose_material_name',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py13': @pytest_ar._saferepr(@py_assert12) }
        @py_format16 = 'assert %(py15)s' % {
            'py15': @py_format14 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format16))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert12 = None
    @py_assert1 = 'dubbing'
    @py_assert3 = 'olive'
    @py_assert5 = compose_material_name(@py_assert1, color = @py_assert3)
    @py_assert8 = 'olive dubbing'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, color=%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(compose_material_name) if 'compose_material_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(compose_material_name) else 'compose_material_name',
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
    @py_assert1 = 'thread'
    @py_assert3 = 'Uni'
    @py_assert5 = compose_material_name(@py_assert1, brand = @py_assert3)
    @py_assert8 = 'thread (Uni)'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, brand=%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(compose_material_name) if 'compose_material_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(compose_material_name) else 'compose_material_name',
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


def test_structured_add_and_update(tmp_path, monkeypatch):
    user_store = user_store
    import jarvis.flytying
    monkeypatch.setattr(user_store, 'MATERIALS_FILE', tmp_path / 'mats.json')
    add = add_structured_item('dry hook', color = 'olive', size = '14', brand = 'Uni')
    @py_assert0 = add['ok']
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
    @py_assert0 = 'olive 14 dry hook (Uni)'
    @py_assert4 = list_materials()
    @py_assert2 = @py_assert0 in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(list_materials) if 'list_materials' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_materials) else 'list_materials',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    item_id = add['item']['id']
    upd = update_inventory_item(item_id, {
        'size': '16' })
    @py_assert0 = upd['ok']
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
    @py_assert0 = '16'
    @py_assert3 = upd['item']['name']
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

