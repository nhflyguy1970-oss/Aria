# Source Generated with Decompyle++
# File: test_p5_integration.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''P5 integration, learning, and ops tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda : p5_flags = p5_flagsimport jarvis.p5_flagsflags = p5_flags()@py_assert1 = flags.get@py_assert3 = 'cad_teaching'@py_assert5 = @py_assert1(@py_assert3)@py_assert8 = None@py_assert7 = @py_assert5 is not @py_assert8if not @py_assert7:
@py_format10 = @pytest_ar._call_reprcompare(('is not',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is not %(py9)s',), (@py_assert5, @py_assert8)) % {
'py0': @pytest_ar._saferepr(flags) if 'flags' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flags) else 'flags',
'py2': @pytest_ar._saferepr(@py_assert1),
'py4': @pytest_ar._saferepr(@py_assert3),
'py6': @pytest_ar._saferepr(@py_assert5),
'py9': @pytest_ar._saferepr(@py_assert8) }@py_format12 = 'assert %(py11)s' % {
'py11': @py_format10 }raise AssertionError(@pytest_ar._format_explanation(@py_format12))@py_assert1 = None@py_assert3 = None@py_assert5 = None@py_assert7 = None@py_assert8 = None@py_assert1 = flags.get@py_assert3 = 'pin_lock'@py_assert5 = @py_assert1(@py_assert3)@py_assert8 = None@py_assert7 = @py_assert5 is not @py_assert8if not @py_assert7:
@py_format10 = @pytest_ar._call_reprcompare(('is not',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is not %(py9)s',), (@py_assert5, @py_assert8)) % {
'py0': @pytest_ar._saferepr(flags) if 'flags' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flags) else 'flags',
'py2': @pytest_ar._saferepr(@py_assert1),
'py4': @pytest_ar._saferepr(@py_assert3),
'py6': @pytest_ar._saferepr(@py_assert5),
'py9': @pytest_ar._saferepr(@py_assert8) }@py_format12 = 'assert %(py11)s' % {
'py11': @py_format10 }raise AssertionError(@pytest_ar._format_explanation(@py_format12))@py_assert1 = None@py_assert3 = None@py_assert5 = None@py_assert7 = None@py_assert8 = None) = import _pytest.assertion.rewrite, assertion

def test_upgrade_apply_confirm(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_debug_bundle_cad_section():
    collect = collect
    import jarvis.debug_bundle
    bundle = collect(log_bytes = 500)
    @py_assert0 = 'cad_print'
    @py_assert2 = @py_assert0 in bundle
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, bundle)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(bundle) if 'bundle' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bundle) else 'bundle' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_usb_ports_list():
    list_serial_ports = list_serial_ports
    import jarvis.engineering.usb_printer
    ports = list_serial_ports()
    @py_assert3 = isinstance(ports, list)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py1)s, %(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(ports) if 'ports' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ports) else 'ports',
            'py2': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert3 = None


def test_voice_cheatsheet_default_exists():
    default_keys = default_keys
    import jarvis.cheatsheets
    @py_assert0 = 'voice'
    @py_assert4 = default_keys()
    @py_assert2 = @py_assert0 in @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(default_keys) if 'default_keys' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(default_keys) else 'default_keys',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None

