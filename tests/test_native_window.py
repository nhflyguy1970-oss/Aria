# Source Generated with Decompyle++
# File: test_native_window.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for native window launcher.'''
import builtins as @py_builtins

rewrite
from jarvis.gui_launcher import _app_url, gui_mode, open_gui
gui_mode = gui_mode
open_gui = open_gui
import _pytest.assertion.rewrite, assertion
from jarvis.native_window import is_available

def test_gui_mode_defaults_fluent(monkeypatch):
    monkeypatch.delenv('JARVIS_GUI_MODE', raising = False)
    @py_assert1 = gui_mode()
    @py_assert4 = 'fluent'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(gui_mode) if 'gui_mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gui_mode) else 'gui_mode',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_gui_mode_native(monkeypatch):
    monkeypatch.setenv('JARVIS_GUI_MODE', 'native')
    @py_assert1 = gui_mode()
    @py_assert4 = 'native'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(gui_mode) if 'gui_mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gui_mode) else 'gui_mode',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_open_gui_prefers_native_when_available(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_open_gui_auto_uses_chrome_app(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_open_gui_app_mode(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_is_available_with_qt(monkeypatch):
    monkeypatch.delenv('PYWEBVIEW_GUI', raising = False)
    monkeypatch.setattr('jarvis.native_window._can_use_gtk', (lambda : False))
    monkeypatch.setattr('jarvis.native_window._can_use_qt', (lambda : True))
    @py_assert1 = is_available()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(is_available) if 'is_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_available) else 'is_available',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_select_backend_prefers_qt_when_configured(monkeypatch):
    _select_backend = _select_backend
    import jarvis.native_window
    monkeypatch.delenv('PYWEBVIEW_GUI', raising = False)
    monkeypatch.setenv('JARVIS_PREFER_QT_WEBVIEW', '1')
    monkeypatch.setattr('jarvis.native_window._can_use_gtk', (lambda : True))
    monkeypatch.setattr('jarvis.native_window._can_use_qt', (lambda : True))
    @py_assert1 = _select_backend()
    @py_assert4 = 'qt'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_select_backend) if '_select_backend' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_select_backend) else '_select_backend',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_app_url_adds_query():
    @py_assert1 = 'http://127.0.0.1:8765'
    @py_assert3 = _app_url(@py_assert1)
    @py_assert6 = 'http://127.0.0.1:8765?app=1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_app_url) if '_app_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_app_url) else '_app_url',
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
    @py_assert1 = 'http://127.0.0.1:8765?x=1'
    @py_assert3 = _app_url(@py_assert1)
    @py_assert6 = 'http://127.0.0.1:8765?x=1&app=1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_app_url) if '_app_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_app_url) else '_app_url',
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
    @py_assert1 = 'http://127.0.0.1:8765?app=1'
    @py_assert3 = _app_url(@py_assert1)
    @py_assert6 = 'http://127.0.0.1:8765?app=1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_app_url) if '_app_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_app_url) else '_app_url',
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


def test_daemon_tray_native_open_with_no_browser():
    Path = Path
    import pathlib
    src = (Path(__file__).resolve().parent.parent / 'jarvis' / 'daemon.py').read_text(encoding = 'utf-8')
    @py_assert1 = []
    @py_assert2 = 'JARVIS_NO_BROWSER=1 skips browser'
    @py_assert4 = @py_assert2 in src
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'native_shell_modes'
        @py_assert11 = @py_assert9 in src
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete

