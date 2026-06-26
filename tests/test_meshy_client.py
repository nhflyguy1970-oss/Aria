# Source Generated with Decompyle++
# File: test_meshy_client.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for Meshy client helpers.'''
import builtins as @py_builtins

rewrite
from jarvis.meshy_client import meshy_api_key, meshy_available
meshy_available = meshy_available
import _pytest.assertion.rewrite, assertion

def test_meshy_available_without_key(monkeypatch):
    monkeypatch.delenv('JARVIS_MESHY_API_KEY', raising = False)
    monkeypatch.delenv('MESHY_API_KEY', raising = False)
    @py_assert1 = meshy_api_key()
    @py_assert4 = ''
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(meshy_api_key) if 'meshy_api_key' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meshy_api_key) else 'meshy_api_key',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = meshy_available()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(meshy_available) if 'meshy_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meshy_available) else 'meshy_available',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_meshy_available_with_key(monkeypatch):
    monkeypatch.setenv('JARVIS_MESHY_API_KEY', 'msk-test')
    @py_assert1 = meshy_available()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(meshy_available) if 'meshy_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meshy_available) else 'meshy_available',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

