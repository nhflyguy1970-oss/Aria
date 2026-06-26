# Source Generated with Decompyle++
# File: test_desktop_shells.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Desktop shell tests (P4 #88 / #89).'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda monkeypatch: gui_mode = gui_modeimport jarvis.gui_launchermonkeypatch.setenv('JARVIS_GUI_MODE', 'electron')@py_assert1 = gui_mode()@py_assert4 = 'electron'@py_assert3 = @py_assert1 == @py_assert4if not @py_assert3:
@py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
'py0': @pytest_ar._saferepr(gui_mode) if 'gui_mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gui_mode) else 'gui_mode',
'py2': @pytest_ar._saferepr(@py_assert1),
'py5': @pytest_ar._saferepr(@py_assert4) }@py_format8 = 'assert %(py7)s' % {
'py7': @py_format6 }raise AssertionError(@pytest_ar._format_explanation(@py_format8))@py_assert1 = None@py_assert3 = None@py_assert4 = Nonemonkeypatch.setenv('JARVIS_GUI_MODE', 'pyside')@py_assert1 = gui_mode()@py_assert4 = 'pyside'@py_assert3 = @py_assert1 == @py_assert4if not @py_assert3:
@py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
'py0': @pytest_ar._saferepr(gui_mode) if 'gui_mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gui_mode) else 'gui_mode',
'py2': @pytest_ar._saferepr(@py_assert1),
'py5': @pytest_ar._saferepr(@py_assert4) }@py_format8 = 'assert %(py7)s' % {
'py7': @py_format6 }raise AssertionError(@pytest_ar._format_explanation(@py_format8))@py_assert1 = None@py_assert3 = None@py_assert4 = Nonemonkeypatch.setenv('JARVIS_GUI_MODE', 'fluent')@py_assert1 = gui_mode()@py_assert4 = 'fluent'@py_assert3 = @py_assert1 == @py_assert4if not @py_assert3:
@py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
'py0': @pytest_ar._saferepr(gui_mode) if 'gui_mode' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(gui_mode) else 'gui_mode',
'py2': @pytest_ar._saferepr(@py_assert1),
'py5': @pytest_ar._saferepr(@py_assert4) }@py_format8 = 'assert %(py7)s' % {
'py7': @py_format6 }raise AssertionError(@pytest_ar._format_explanation(@py_format8))@py_assert1 = None@py_assert3 = None@py_assert4 = None) = import _pytest.assertion.rewrite, assertion

def test_open_gui_electron(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_open_gui_pyside(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_desktop_shell_app_url():
    app_url = app_url
    import jarvis.desktop_shell
    @py_assert1 = 'http://127.0.0.1:8765'
    @py_assert3 = app_url(@py_assert1)
    @py_assert6 = 'http://127.0.0.1:8765?app=1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(app_url) if 'app_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_url) else 'app_url',
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
    @py_assert1 = 'http://127.0.0.1:8765'
    @py_assert3 = 'pyside'
    @py_assert5 = app_url(@py_assert1, shell = @py_assert3)
    @py_assert8 = 'http://127.0.0.1:8765?app=1&shell=pyside'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, shell=%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(app_url) if 'app_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_url) else 'app_url',
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


def test_electron_status_shape():
    status = status
    import jarvis.electron_shell
    st = status()
    @py_assert0 = 'available'
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
    @py_assert0 = 'installed'
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


def test_pyside_status_shape():
    status = status
    import jarvis.pyside_shell
    st = status()
    @py_assert0 = 'available'
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
    @py_assert0 = 'fluent'
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


def test_pyside_detach_flag(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_pyside_auto_detach_without_foreground(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_pyside_foreground_child(monkeypatch):
    main = main
    import jarvis.pyside_shell
    monkeypatch.setenv('JARVIS_PYSIDE_FOREGROUND', '1')
    monkeypatch.setattr('jarvis.pyside_shell.run_window_blocking', (lambda url: 0))
    @py_assert1 = [
        'http://127.0.0.1:8765']
    @py_assert3 = main(@py_assert1)
    @py_assert6 = 0
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(main) if 'main' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(main) else 'main',
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


def test_p4_shell_flags():
    electron_shell_enabled = electron_shell_enabled
    pyside_shell_enabled = pyside_shell_enabled
    import jarvis.p4_flags
    @py_assert2 = electron_shell_enabled()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(electron_shell_enabled) if 'electron_shell_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(electron_shell_enabled) else 'electron_shell_enabled',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None
    @py_assert2 = pyside_shell_enabled()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(pyside_shell_enabled) if 'pyside_shell_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pyside_shell_enabled) else 'pyside_shell_enabled',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None


def test_pyside_grants_media_permissions():
    '''WebEngine must auto-grant camera/mic or Presence webcam fails silently.'''
    import pytest
    MagicMock = MagicMock
    import unittest.mock
# WARNING: Decompyle incomplete


def test_pyside_grants_media_permissions_legacy_feature():
    '''Legacy featurePermissionRequested path remains wired for older Qt builds.'''
    import pytest
    MagicMock = MagicMock
    import unittest.mock
# WARNING: Decompyle incomplete


def test_gui_shell_lock_helpers():
    import pytest
    GUI_SHELL_LOCK = GUI_SHELL_LOCK
    acquire_gui_shell_lock = acquire_gui_shell_lock
    gui_shell_running = gui_shell_running
    release_gui_shell_lock = release_gui_shell_lock
    import jarvis.desktop_shell
    if gui_shell_running():
        pytest.skip('Live GUI shell holds gui_shell.lock — close shell for isolated lock test')
    release_gui_shell_lock()
    @py_assert1 = 'test'
    @py_assert3 = acquire_gui_shell_lock(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(acquire_gui_shell_lock) if 'acquire_gui_shell_lock' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(acquire_gui_shell_lock) else 'acquire_gui_shell_lock',
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
    @py_assert1 = GUI_SHELL_LOCK.lock_file
    @py_assert3 = @py_assert1.is_file
    @py_assert5 = @py_assert3()
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.lock_file\n}.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(GUI_SHELL_LOCK) if 'GUI_SHELL_LOCK' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(GUI_SHELL_LOCK) else 'GUI_SHELL_LOCK',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    release_gui_shell_lock()
    @py_assert1 = 'test'
    @py_assert3 = acquire_gui_shell_lock(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(acquire_gui_shell_lock) if 'acquire_gui_shell_lock' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(acquire_gui_shell_lock) else 'acquire_gui_shell_lock',
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
    release_gui_shell_lock()


def test_ui_version_sync():
    Path = Path
    import pathlib
    UI_VERSION = UI_VERSION
    import jarvis.gui.server
    root = Path(__file__).resolve().parent.parent
    html = (root / 'jarvis' / 'gui' / 'static' / 'index.html').read_text(encoding = 'utf-8')
    app_js = (root / 'jarvis' / 'gui' / 'static' / 'app.js').read_text(encoding = 'utf-8')
    @py_assert0 = f'''content="{UI_VERSION}"'''
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = f'''app.js?v={UI_VERSION}'''
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'JARVIS_UI_VERSION'
    @py_assert2 = @py_assert0 in app_js
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, app_js)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(app_js) if 'app_js' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_js) else 'app_js' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'meta[name="jarvis-ui-version"]'
    @py_assert2 = @py_assert0 in app_js
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, app_js)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(app_js) if 'app_js' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_js) else 'app_js' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_switch_to_view_fallback():
    Path = Path
    import pathlib
    app_js = (Path(__file__).resolve().parent.parent / 'jarvis' / 'gui' / 'static' / 'app.js').read_text(encoding = 'utf-8')
    @py_assert0 = 'KNOWN_VIEWS'
    @py_assert2 = @py_assert0 in app_js
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, app_js)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(app_js) if 'app_js' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_js) else 'app_js' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'falling back to chat'
    @py_assert2 = @py_assert0 in app_js
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, app_js)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(app_js) if 'app_js' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(app_js) else 'app_js' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

