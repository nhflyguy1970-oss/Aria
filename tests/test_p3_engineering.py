# Source Generated with Decompyle++
# File: test_p3_engineering.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''P3 engineering / CAD / print tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import struct = import _pytest.assertion.rewrite, assertion
from pathlib import Path

def test_cad_status():
    cad_status = cad_status
    import jarvis.engineering.cad_deps
    st = cad_status()
    @py_assert0 = 'openscad'
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
    @py_assert0 = 'build123d'
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


def test_verify_ascii_stl(tmp_path):
    verify_stl = verify_stl
    import jarvis.engineering.cad_verify
    stl = tmp_path / 'cube.stl'
    stl.write_text('solid test\nfacet normal 0 0 1\n  outer loop\n    vertex 0 0 0\n    vertex 10 0 0\n    vertex 0 10 0\n  endloop\nendfacet\nendsolid test\n', encoding = 'utf-8')
    v = verify_stl(stl)
    @py_assert0 = v['ok']
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
    @py_assert0 = v['triangles']
    @py_assert3 = 1
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


def test_verify_binary_stl(tmp_path):
    verify_stl = verify_stl
    import jarvis.engineering.cad_verify
    stl = tmp_path / 'b.stl'
    header = b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    tri_count = 1
    tri = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('<9f', 0, 0, 0, 10, 0, 0, 0, 10, 0) + b'\x00\x00'
    stl.write_bytes(header + struct.pack('<I', tri_count) + tri)
    v = verify_stl(stl)
    @py_assert0 = v['ok']
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
    @py_assert0 = v['triangles']
    @py_assert3 = 1
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


def test_cad_router_pick():
    pick_backend = pick_backend
    import jarvis.engineering.cad_router
    @py_assert1 = 'make a hose adapter bracket'
    @py_assert3 = 'auto'
    @py_assert5 = pick_backend(@py_assert1, prefer = @py_assert3)
    @py_assert8 = ('openscad', 'build123d', 'meshy')
    @py_assert7 = @py_assert5 in @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('in',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, prefer=%(py4)s)\n} in %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(pick_backend) if 'pick_backend' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pick_backend) else 'pick_backend',
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


def test_cad_store_register(tmp_path, monkeypatch):
    monkeypatch.setattr('jarvis.engineering.cad_store.ENGINEERING_DIR', tmp_path)
    monkeypatch.setattr('jarvis.engineering.cad_store.INDEX_FILE', tmp_path / 'models.json')
    list_models = list_models
    register_model = register_model
    import jarvis.engineering.cad_store
    register_model(prompt = 'test cube', backend = 'openscad', stl_path = str(tmp_path / 'a.stl'))
    @py_assert2 = list_models()
    @py_assert4 = len(@py_assert2)
    @py_assert7 = 1
    @py_assert6 = @py_assert4 >= @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('>=',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n})\n} >= %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(list_models) if 'list_models' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_models) else 'list_models',
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


def test_openscad_render(tmp_path):
    import shutil
    if not shutil.which('openscad'):
        return None
    render_scad = render_scad
    import jarvis.engineering.openscad_runner
    scad = tmp_path / 'cube.scad'
    stl = tmp_path / 'cube.stl'
    scad.write_text('cube(10);\n', encoding = 'utf-8')
    r = render_scad(scad, stl)
    @py_assert1 = r.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(r) if 'r' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(r) else 'r',
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
    @py_assert1 = stl.is_file
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(stl) if 'stl' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(stl) else 'stl',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_p3_flags():
    p3_flags = p3_flags
    import jarvis.p3_flags
    flags = p3_flags()
    @py_assert0 = 'cad'
    @py_assert2 = @py_assert0 in flags
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, flags)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(flags) if 'flags' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flags) else 'flags' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'printer'
    @py_assert2 = @py_assert0 in flags
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, flags)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(flags) if 'flags' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flags) else 'flags' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

