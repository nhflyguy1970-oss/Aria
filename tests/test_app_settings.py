# Source Generated with Decompyle++
# File: test_app_settings.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Persisted GUI preferences.'''
import builtins as @py_builtins

rewrite
from jarvis import app_settings
import _pytest.assertion.rewrite, assertion

def test_uncensored_pref_roundtrip(data_dir, monkeypatch):
    monkeypatch.setattr(app_settings, 'SETTINGS_FILE', data_dir / 'app_settings.json')
    @py_assert1 = app_settings.get_uncensored
    @py_assert3 = @py_assert1()
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.get_uncensored\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(app_settings) if 'app_settings' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_settings) else 'app_settings',
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
    app_settings.set_uncensored_pref(True)
    @py_assert1 = app_settings.get_uncensored
    @py_assert3 = @py_assert1()
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.get_uncensored\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(app_settings) if 'app_settings' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_settings) else 'app_settings',
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
    app_settings.set_uncensored_pref(False)
    @py_assert1 = app_settings.get_uncensored
    @py_assert3 = @py_assert1()
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.get_uncensored\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(app_settings) if 'app_settings' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_settings) else 'app_settings',
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

