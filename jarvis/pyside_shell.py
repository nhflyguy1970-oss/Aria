# Source Generated with Decompyle++
# File: pyside_shell.cpython-312.pyc (Python 3.12)

'''PySide6 / Fluent desktop shell for ARIA (P4 #89).'''
from __future__ import annotations
import logging
import os
import signal
import sys
import time
from typing import Any
from jarvis.desktop_shell import DEFAULT_HEIGHT, DEFAULT_WIDTH, ICON_PATH, InstanceLock, PROJECT_ROOT, acquire_gui_shell_lock, app_url, default_url, focus_existing_window, gui_shell_running, release_gui_shell_lock, spawn_detached, wait_for_server, window_title
logger = logging.getLogger('jarvis.pyside_shell')
LOCK = InstanceLock('pyside_shell')
_main_window: 'Any' = None
_RELOAD_ON_FOCUS_FLAG = PROJECT_ROOT / 'data' / '.gui_reload_on_focus'

def _shell_web_view(win = None):
    view = getattr(win, 'view', None)
# WARNING: Decompyle incomplete


def _reload_shell_web_view(win = None):
    view = _shell_web_view(win)
# WARNING: Decompyle incomplete


def request_shell_reload_on_focus():
    '''Next in-process focus (e.g. shortcut re-launch) hard-reloads the WebEngine page.'''
    
    try:
        _RELOAD_ON_FOCUS_FLAG.parent.mkdir(parents = True, exist_ok = True)
        _RELOAD_ON_FOCUS_FLAG.write_text('1', encoding = 'utf-8')
        return None
    except OSError:
        exc = None
        logger.debug('request_shell_reload_on_focus: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _pid_alive(pid = None):
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False



def _shell_pids():
    GUI_SHELL_LOCK = GUI_SHELL_LOCK
    import jarvis.desktop_shell
    out = set()
    for path in (LOCK.pid_file, GUI_SHELL_LOCK.pid_file):
        if not path.is_file():
            continue
        if not path.read_text(encoding = 'utf-8').strip():
            path.read_text(encoding = 'utf-8').strip()
        pid = int('0')
        if not pid:
            continue
        if not pid != os.getpid():
            continue
        out.add(pid)
    return out
    except (OSError, ValueError):
        continue


def terminate_running_shell(*, timeout_sec):
    '''Stop a running PySide shell so a fresh window can open.'''
    pids = _shell_pids()
    if not pids:
        _cleanup_shell_artifacts()
        return False
    for pid in pids:
        os.kill(pid, signal.SIGTERM)
    deadline = time.time() + timeout_sec
    if time.time() < deadline:
        pass
    for pid in pids:
        if not _pid_alive(pid):
            continue
        os.kill(pid, signal.SIGKILL)
    _cleanup_shell_artifacts()
    return True
    except ProcessLookupError:
        continue
    except OSError:
        exc = None
        logger.debug('terminate shell pid %s: %s', pid, exc)
        exc = None
        del exc
        continue
        exc = None
        del exc
    except OSError:
        continue


def _cleanup_shell_artifacts():
    GUI_SHELL_LOCK = GUI_SHELL_LOCK
    import jarvis.desktop_shell
    for path in (LOCK.pid_file, LOCK.lock_file, GUI_SHELL_LOCK.pid_file, GUI_SHELL_LOCK.lock_file, PROJECT_ROOT / 'data' / 'gui_shell_active.txt', _RELOAD_ON_FOCUS_FLAG):
        path.unlink(missing_ok = True)
    return None
    except OSError:
        continue


def focus_window():
    '''Raise the PySide main window (in-process). Returns False if no window.'''
    win = _main_window
# WARNING: Decompyle incomplete


def _install_focus_signal_handler():
    
    def _on_focus_signal(signum = None, frame = None):
        pass
    # WARNING: Decompyle incomplete

    
    try:
        signal.signal(signal.SIGUSR1, _on_focus_signal)
        return None
    except (OSError, ValueError):
        exc = None
        logger.debug('Could not install SIGUSR1 focus handler: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _register_main_window(window = None):
    global _main_window
    _main_window = window
    pid_file = LOCK.pid_file
    pid_file.parent.mkdir(parents = True, exist_ok = True)
    pid_file.write_text(str(os.getpid()), encoding = 'utf-8')


def _clear_main_window():
    global _main_window
    _main_window = None
    
    try:
        LOCK.pid_file.unlink(missing_ok = True)
        return None
    except OSError:
        return None



def reload_web_view_bypass_cache(view = None):
    '''Hard-reload WebEngine page bypassing HTTP cache.'''
    
    try:
        QWebEnginePage = QWebEnginePage
        import PySide6.QtWebEngineCore
        view.page().triggerAction(QWebEnginePage.WebAction.ReloadBypassCache)
        return None
    except Exception:
        exc = None
        logger.debug('reload_web_view_bypass_cache: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _import_pyside():
    QUrl = QUrl
    import PySide6.QtCore
    QAction = QAction
    QColor = QColor
    QIcon = QIcon
    QPalette = QPalette
    import PySide6.QtGui
    QWebEngineView = QWebEngineView
    import PySide6.QtWebEngineWidgets
    QApplication = QApplication
    QHBoxLayout = QHBoxLayout
    QMainWindow = QMainWindow
    QStatusBar = QStatusBar
    QToolBar = QToolBar
    QVBoxLayout = QVBoxLayout
    QWidget = QWidget
    import PySide6.QtWidgets
    return (QApplication, QMainWindow, QToolBar, QStatusBar, QWebEngineView, QUrl, QAction, QIcon, QPalette, QColor, QWidget, QVBoxLayout, QHBoxLayout)


def is_available():
    
    try:
        _import_pyside()
        return True
    except ImportError:
        return False



def can_run_window():
    pyside_window_ready = pyside_window_ready
    import jarvis.desktop_runtime
    return pyside_window_ready()


def fluent_available():
    
    try:
        Theme = Theme
        setTheme = setTheme
        import qfluentwidgets
        return True
    except ImportError:
        return False



def _use_fluent_chrome():
    if not os.getenv('JARVIS_GUI_MODE'):
        os.getenv('JARVIS_GUI_MODE')
    mode = 'app'.strip().lower()
    if mode == 'fluent':
        return True
    if mode == 'pyside':
        return os.getenv('JARVIS_FLUENT_WIDGETS', '1').strip().lower() not in ('0', 'false', 'no', 'off')


def missing_dependency_hint():
    desktop_deps_hint = desktop_deps_hint
    import jarvis.desktop_runtime
    extra = desktop_deps_hint()
    lines = [
        'PySide6 desktop shell cannot start on this system.',
        'Run: ./scripts/install-pyside-shell.sh',
        '(pip install PySide6 PySide6-Addons; optional: PySide6-Fluent-Widgets)']
    if extra:
        lines.append(f'''System packages: {extra}''')
    return '\n'.join(lines)


def _apply_dark_palette(app = None):
    parts = _import_pyside()
    QColor = parts[9]
    QPalette = parts[8]
    palette = QPalette()
    bg = QColor('#0a0c10')
    fg = QColor('#e8eaed')
    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, fg)
    palette.setColor(QPalette.ColorRole.Base, QColor('#11141a'))
    palette.setColor(QPalette.ColorRole.Text, fg)
    palette.setColor(QPalette.ColorRole.Button, QColor('#181c24'))
    palette.setColor(QPalette.ColorRole.ButtonText, fg)
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#4da3ff'))
    palette.setColor(QPalette.ColorRole.HighlightedText, fg)
    app.setPalette(palette)


def _apply_fluent_theme(app = None):
    if not fluent_available():
        app.setStyle('Fusion')
        _apply_dark_palette(app)
        return False
    
    try:
        Theme = Theme
        setTheme = setTheme
        import qfluentwidgets
        setTheme(Theme.DARK)
        return True
    except ImportError:
        app.setStyle('Fusion')
        _apply_dark_palette(app)
        return False



def _handle_permission_requested(permission = None, *, media_types):
    QWebEnginePermission = QWebEnginePermission
    import PySide6.QtWebEngineCore
# WARNING: Decompyle incomplete


def _grant_web_media_permissions(page = None):
    '''Auto-grant camera/mic for Presence, Cloud Live, and lock-screen face auth.'''
    pass
# WARNING: Decompyle incomplete


def _configure_web_view(view = None):
    QWebEngineSettings = QWebEngineSettings
    import PySide6.QtWebEngineCore
    QApplication = QApplication
    import PySide6.QtWidgets
    settings = view.settings()
    settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, 16)
    settings.setFontSize(QWebEngineSettings.FontSize.DefaultFixedFontSize, 14)
    settings.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, 12)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    _grant_web_media_permissions(view.page())
    zoom_raw = os.getenv('JARVIS_WEBENGINE_ZOOM', '').strip()
# WARNING: Decompyle incomplete


def _native_dashboard_enabled():
    raw = os.getenv('JARVIS_PYSIDE_NATIVE_DASHBOARD', '').strip().lower()
    if raw in ('0', 'false', 'no', 'off'):
        return False
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    return _use_fluent_chrome()


def _build_native_fluent_window(url = None):
    build_aria_fluent_window = build_aria_fluent_window
    fluent_shell_available = fluent_shell_available
    import jarvis.gui.pyside.fluent_shell
    if not fluent_shell_available():
        raise RuntimeError('PySide6-Fluent-Widgets required for native dashboard')
    icon = str(ICON_PATH) if ICON_PATH.is_file() else ''
    return build_aria_fluent_window(url, icon_path = icon)


def _wire_shell_close_quit(window = None):
    '''Quit the Qt event loop when the user closes the shell window.'''
    pass
# WARNING: Decompyle incomplete


def _focus_running_shell(*, request_reload):
    if not gui_shell_running() and LOCK.another_running():
        return False
    if request_reload:
        request_shell_reload_on_focus()
    return focus_existing_window()


def _prepare_shell_launch(*, force_new):
    '''Focus an existing shell, or tear it down when focus fails / force_new.'''
    if not gui_shell_running() and LOCK.another_running():
        return True
    if force_new:
        logger.info('Replacing running PySide shell (force new window)')
        terminate_running_shell()
        return True
    if _focus_running_shell():
        return False
    logger.warning('PySide shell running but could not be focused — restarting window')
    terminate_running_shell()
    return True


def _build_shell_window(url = None, *, fluent):
    '''Full-bleed WebEngine shell — same layout footprint as Chrome --app.'''
    pass
# WARNING: Decompyle incomplete


def _build_fluent_window(url = None):
    return _build_shell_window(url, fluent = True)


def _build_window(url = None):
    return _build_shell_window(url, fluent = False)


def _fluent_shell_available():
    
    try:
        fluent_shell_available = fluent_shell_available
        import jarvis.gui.pyside.fluent_shell
        return fluent_shell_available()
    except ImportError:
        return False



def run_window_blocking(url = None, *, wait_for_ready):
    if not is_available():
        sys.stderr.write(missing_dependency_hint() + '\n')
        return 1
    force_new = os.getenv('JARVIS_SHELL_FORCE_NEW', '').strip().lower() in ('1', 'true', 'yes', 'on')
    if not _prepare_shell_launch(force_new = force_new):
        return 0
    if not acquire_gui_shell_lock('fluent' if _use_fluent_chrome() else 'pyside'):
        if _focus_running_shell():
            return 0
        terminate_running_shell()
        if not acquire_gui_shell_lock('fluent' if _use_fluent_chrome() else 'pyside'):
            sys.stderr.write('Another GUI shell is still starting\n')
            return 1
    _install_focus_signal_handler()
# WARNING: Decompyle incomplete


def launch_pyside_shell(url = None):
    if not is_available() or can_run_window():
        return False
    if not _prepare_shell_launch(force_new = False):
        return True
    python_exe = python_exe
    import jarvis.desktop_shell
    return spawn_detached([
        python_exe(),
        '-m',
        'jarvis.pyside_shell',
        url,
        '--no-wait'], extra_env = {
        'JARVIS_PYSIDE_FOREGROUND': '1' })


def status():
    
    try:
        native_fluent = fluent_shell_available
        import jarvis.gui.pyside.fluent_shell
        if fluent_available():
            fluent_available()
        if _native_dashboard_enabled():
            _native_dashboard_enabled()
        if not gui_shell_running():
            gui_shell_running()
        return {
            'available': is_available(),
            'fluent': fluent_available(),
            'fluent_active': _use_fluent_chrome(),
            'native_dashboard': native_fluent(),
            'running': LOCK.another_running(),
            'mode': os.getenv('JARVIS_GUI_MODE', '') }
    except ImportError:
        
        native_fluent = lambda : False
        continue



def main(argv = None):
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    load_jarvis_env()
# WARNING: Decompyle incomplete

if __name__ == '__main__':
    raise SystemExit(main())
