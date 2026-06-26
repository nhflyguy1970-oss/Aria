# Source Generated with Decompyle++
# File: test_flytying_barcode.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Barcode and inventory scan tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.flytying.barcode import barcode_kind, learn_barcode_mapping, list_barcode_mappings, lookup_barcode, make_custom_barcode, normalize_barcode
learn_barcode_mapping = learn_barcode_mapping
list_barcode_mappings = list_barcode_mappings
lookup_barcode = lookup_barcode
make_custom_barcode = make_custom_barcode
normalize_barcode = normalize_barcode
import _pytest.assertion.rewrite, assertion
from jarvis.flytying.user_store import add_inventory_item, list_inventory_items, list_materials, remove_inventory_item, save_materials, scan_barcode_into_inventory

def test_normalize_upc_padding():
    @py_assert1 = '012345678905'
    @py_assert3 = normalize_barcode(@py_assert1)
    @py_assert6 = '012345678905'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_barcode) if 'normalize_barcode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_barcode) else 'normalize_barcode',
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
    @py_assert1 = '12345678905'
    @py_assert3 = normalize_barcode(@py_assert1)
    @py_assert6 = '012345678905'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_barcode) if 'normalize_barcode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_barcode) else 'normalize_barcode',
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
    @py_assert1 = 'FT:olive-dubbing'
    @py_assert3 = normalize_barcode(@py_assert1)
    @py_assert6 = 'FT:OLIVE-DUBBING'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_barcode) if 'normalize_barcode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_barcode) else 'normalize_barcode',
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


def test_barcode_kind():
    @py_assert1 = '012345678905'
    @py_assert3 = barcode_kind(@py_assert1)
    @py_assert6 = 'upc_ean'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(barcode_kind) if 'barcode_kind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(barcode_kind) else 'barcode_kind',
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
    @py_assert1 = 'FT:thread-olive'
    @py_assert3 = barcode_kind(@py_assert1)
    @py_assert6 = 'custom'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(barcode_kind) if 'barcode_kind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(barcode_kind) else 'barcode_kind',
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


def test_local_barcode_map_roundtrip(tmp_path, monkeypatch):
    bc = barcode
    import jarvis.flytying
    monkeypatch.setattr(bc, 'BARCODE_MAP_FILE', tmp_path / 'map.json')
    learn_barcode_mapping('012345678905', 'Test Thread', brand = 'Uni')
    hit = lookup_barcode('012345678905', online = False)
    @py_assert0 = hit['found']
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
    @py_assert0 = 'Test Thread'
    @py_assert3 = hit['name']
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
    @py_assert0 = '012345678905'
    @py_assert4 = list_barcode_mappings()
    @py_assert2 = @py_assert0 in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(list_barcode_mappings) if 'list_barcode_mappings' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_barcode_mappings) else 'list_barcode_mappings',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_inventory_scan_needs_name(tmp_path, monkeypatch):
    bc = barcode
    import jarvis.flytying
    user_store = user_store
    import jarvis.flytying
    monkeypatch.setattr(user_store, 'MATERIALS_FILE', tmp_path / 'mats.json')
    monkeypatch.setattr(bc, 'BARCODE_MAP_FILE', tmp_path / 'map.json')
    result = scan_barcode_into_inventory('999999999999', online_lookup = False)
    @py_assert0 = result['needs_name']
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
    @py_assert0 = result['added']
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
    named = scan_barcode_into_inventory('999999999999', name = 'Mystery Dubbing', online_lookup = False)
    @py_assert0 = named['added']
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
    @py_assert0 = 'Mystery Dubbing'
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


def test_inventory_add_remove(tmp_path, monkeypatch):
    user_store = user_store
    import jarvis.flytying
    monkeypatch.setattr(user_store, 'MATERIALS_FILE', tmp_path / 'mats.json')
    save_materials([
        'grizzly hackle'])
    add_inventory_item('Olive CDC', barcode = 'FT:OLIVE-CDC', source = 'scan_custom')
    @py_assert2 = list_inventory_items()
    @py_assert4 = len(@py_assert2)
    @py_assert7 = 2
    @py_assert6 = @py_assert4 >= @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('>=',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n})\n} >= %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(list_inventory_items) if 'list_inventory_items' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_inventory_items) else 'list_inventory_items',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    item = list_inventory_items()[-1]
    remove_inventory_item(str(item.get('id')))
    @py_assert0 = 'Olive CDC'
    @py_assert4 = list_materials()
    @py_assert2 = @py_assert0 not in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(list_materials) if 'list_materials' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_materials) else 'list_materials',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_custom_label_code():
    code = make_custom_barcode('Olive Dubbing')
    @py_assert1 = code.startswith
    @py_assert3 = 'FT:olive-dubbing'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(code) if 'code' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(code) else 'code',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None

