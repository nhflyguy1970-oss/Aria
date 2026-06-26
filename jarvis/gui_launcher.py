# Source Generated with Decompyle++
# File: gui_launcher.cpython-312.pyc (Python 3.12)

'''Unified GUI launcher: Chrome app, Electron, PySide6, or legacy pywebview native.'''
from __future__ import annotations
import logging
import os
import sys
from jarvis.browser_util import open_url
logger = logging.getLogger('jarvis.gui_launcher')
_SHELL_MODES = frozenset({
    'app',
    'auto',
    'fluent',
    'native',
    'pyside',
    'browser',
    'electron'})

def gui_mode():
    '''Return app | browser | native | electron | pyside | fluent | auto.'''
    mode = os.getenv('JARVIS_GUI_MODE', 'fluent').strip().lower()
    if mode in _SHELL_MODES:
        return mode


def _app_url(url = None):
    app_url = app_url
    import jarvis.desktop_shell
    return app_url(url)


def open_gui(url = None):
    '''Open Jarvis UI in the configured desktop shell.'''
    mode = gui_mode()
    if mode == 'electron':
        is_available = is_available
        launch_electron_shell = launch_electron_shell
        missing_dependency_hint = missing_dependency_hint
        import jarvis.electron_shell
        if is_available():
            if launch_electron_shell(url):
                return True
            logger.warning('Electron shell launch failed')
            return False
        logger.warning(missing_dependency_hint())
        return False
    if mode in ('pyside', 'fluent'):
        can_run_window = can_run_window
        is_available = is_available
        launch_pyside_shell = launch_pyside_shell
        missing_dependency_hint = missing_dependency_hint
        import jarvis.pyside_shell
        if is_available() and can_run_window():
            if launch_pyside_shell(url):
                return True
            logger.warning('PySide shell launch failed — falling back to Chrome app window')
        else:
            logger.warning(missing_dependency_hint())
        if not open_url(_app_url(url), app_window = True):
            open_url(_app_url(url), app_window = True)
        return open_url(url, app_window = False)
    if None == 'native':
        is_available = is_available
        launch_native_window = launch_native_window
        missing_dependency_hint = missing_dependency_hint
        import jarvis.native_window
        if is_available():
            if launch_native_window(url):
                return True
            logger.warning('Native window launch failed')
            return False
        logger.warning(missing_dependency_hint())
        return False
    use_app_window = mode in ('app', 'auto')
    launch_url = _app_url(url) if use_app_window else url
    if open_url(launch_url, app_window = use_app_window):
        return True
    if mode == 'browser':
        return False
    return open_url(launch_url, app_window = False)


def main(argv = None):
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    load_jarvis_env()
# WARNING: Decompyle incomplete

if __name__ == '__main__':
    raise SystemExit(main())
