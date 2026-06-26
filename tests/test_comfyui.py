# Source Generated with Decompyle++
# File: test_comfyui.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for ComfyUI client helpers.'''
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion
from jarvis import comfyui

def test_is_available_false_when_unreachable():
    patch('urllib.request.urlopen', side_effect = OSError('down'))
    @py_assert1 = comfyui.is_available
    @py_assert3 = @py_assert1()
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_available\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(comfyui) if 'comfyui' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(comfyui) else 'comfyui',
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
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_generate_returns_error_when_unavailable():
    patch('jarvis.comfyui.is_available', return_value = False)
    patch('jarvis.services.ensure_comfyui', return_value = False)
    out = comfyui.generate('test prompt')
    @py_assert1 = out.startswith
    @py_assert3 = 'ERROR:'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    None(None, None)
    None(None, None)
    return None
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass

