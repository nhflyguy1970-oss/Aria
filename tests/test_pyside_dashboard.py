# Source Generated with Decompyle++
# File: test_pyside_dashboard.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''PySide native dashboard widget tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda : api_client = api_clientdashboard = dashboardstyles = stylesimport jarvis.gui.pyside@py_assert1 = api_client.fetch_dashboardif not @py_assert1:
@py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.fetch_dashboard\n}' % {
'py0': @pytest_ar._saferepr(api_client) if 'api_client' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(api_client) else 'api_client',
'py2': @pytest_ar._saferepr(@py_assert1) }raise AssertionError(@pytest_ar._format_explanation(@py_format3))@py_assert1 = None@py_assert1 = dashboard.DashboardViewif not @py_assert1:
@py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.DashboardView\n}' % {
'py0': @pytest_ar._saferepr(dashboard) if 'dashboard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dashboard) else 'dashboard',
'py2': @pytest_ar._saferepr(@py_assert1) }raise AssertionError(@pytest_ar._format_explanation(@py_format3))@py_assert1 = None@py_assert1 = styles.AURA_STYLESHEETif not @py_assert1:
@py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.AURA_STYLESHEET\n}' % {
'py0': @pytest_ar._saferepr(styles) if 'styles' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(styles) else 'styles',
'py2': @pytest_ar._saferepr(@py_assert1) }raise AssertionError(@pytest_ar._format_explanation(@py_format3))@py_assert1 = None) = import _pytest.assertion.rewrite, assertion

def test_pyside_dashboard_stat_routes():
    Path = Path
    import pathlib
    src = (Path(__file__).resolve().parent.parent / 'jarvis' / 'gui' / 'pyside' / 'dashboard.py').read_text(encoding = 'utf-8')
    @py_assert0 = 'StatCard("Headlines", "documents"'
    @py_assert2 = @py_assert0 in src
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, src)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(src) if 'src' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(src) else 'src' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'StatCard("Kasa devices", "chat"'
    @py_assert2 = @py_assert0 in src
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, src)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(src) if 'src' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(src) else 'src' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_fluent_shell_availability():
    fluent_shell_available = fluent_shell_available
    import jarvis.gui.pyside.fluent_shell
    _native_dashboard_enabled = _native_dashboard_enabled
    is_available = is_available
    import jarvis.pyside_shell
    @py_assert1 = is_available()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(is_available) if 'is_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_available) else 'is_available',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    _ = fluent_shell_available()
    _ = _native_dashboard_enabled()

