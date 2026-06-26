# Source Generated with Decompyle++
# File: native_window.cpython-312.pyc (Python 3.12)

'''Native desktop window for Jarvis via pywebview (WebKitGTK on Linux).'''
from __future__ import annotations
import fcntl
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.error as urllib
import urllib.request as urllib
from pathlib import Path
logger = logging.getLogger('jarvis.native_window')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = PROJECT_ROOT / 'assets' / 'jarvis-tray.png'
DEFAULT_WIDTH = int(os.getenv('JARVIS_NATIVE_WIDTH', '1280'))
DEFAULT_HEIGHT = int(os.getenv('JARVIS_NATIVE_HEIGHT', '860'))

def _app_url(url = None):
    if 'app=1' in url:
        return url
    join = '&' if None in url else '?'
    return f'''{url}{join}app=1'''


def _window_title():
    assistant_window_title = assistant_window_title
    import jarvis.branding
    is_uncensored = is_uncensored
    import jarvis.config
    return assistant_window_title(uncensored = is_uncensored())


def _can_use_gtk():
    
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('WebKit2', '4.1')
        Gtk = Gtk
        WebKit2 = WebKit2
        import gi.repository
        import webview.platforms.gtk as webview
        return True
    except Exception:
        return False



def _can_use_qt():
    
    try:
        import qtpy
        import webview.platforms.qt as webview
        return True
    except Exception:
        return False



def _select_backend():
    forced = os.getenv('PYWEBVIEW_GUI', '').strip().lower()
    if forced in ('gtk', 'qt'):
        if (forced == 'gtk' or _can_use_gtk() or forced == 'qt') and _can_use_qt():
            return forced
        return None
    prefer_qt = None.getenv('JARVIS_PREFER_QT_WEBVIEW', '1').lower() in ('1', 'true', 'yes', 'on')
    if prefer_qt and _can_use_qt():
        return 'qt'
    if _can_use_gtk():
        return 'gtk'
    if _can_use_qt():
        return 'qt'


def is_available():
    '''True if pywebview can load a GTK or Qt backend.'''
    
    try:
        import webview
        return _select_backend() is not None
    except ImportError:
        return False



def missing_dependency_hint():
    if not is_available():
        
        try:
            import webview
            return 'No pywebview GUI backend found.\nRun: ./scripts/install-native-window.sh\n(installs Qt WebEngine via pip, or GTK via apt if you prefer)'
            return ''
        except ImportError:
            return 'pywebview is not installed.\nRun: ./scripts/install-native-window.sh'



def _ensure_backend():
    backend = _select_backend()
    if not backend:
        if not missing_dependency_hint():
            missing_dependency_hint()
        raise RuntimeError('No pywebview backend')
    os.environ['PYWEBVIEW_GUI'] = backend
    return backend


def wait_for_server(url = None, timeout_sec = None):
    live = url.rstrip('/') + '/api/live'
    health = url.rstrip('/') + '/api/health'
    import time
    deadline = time.time() + timeout_sec
    notified_wait = False
    notified_recover = False
    if time.time() < deadline:
        for endpoint in (live, health):
            urllib.request.urlopen(endpoint, timeout = 2)
            if not notified_wait and notified_recover:
                assistant_name = assistant_name
                import jarvis.branding
                _notify_tray(f'''{assistant_name()} ready''', 'Server is responding — opening window.')
                notified_recover = True
            None(None, None)
            (live, health)
            return True
        if notified_wait and time.time() > (deadline - timeout_sec) + 8:
            assistant_name = assistant_name
            import jarvis.branding
            name = assistant_name()
            _notify_tray(name, 'Waiting for server to start…')
            notified_wait = True
        time.sleep(0.4)
        if time.time() < deadline:
            continue
    if notified_wait:
        assistant_name = assistant_name
        import jarvis.branding
        _notify_tray(assistant_name(), 'Server did not respond in time — try the shortcut again.')
    return False
    with None:
        if not None:
            pass
    continue


def _notify_tray(title = None, body = None):
    
    try:
        assistant_name = assistant_name
        import jarvis.branding
        subprocess.run([
            'notify-send',
            '-a',
            assistant_name(),
            title,
            body], check = False, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, timeout = 5)
        return None
    except Exception:
        return None



def run_window_blocking(url = None, *, title, width, height, wait_for_ready):
    '''Open a blocking native window. Returns 0 on clean exit, 1 on failure.'''
    if not is_available():
        sys.stderr.write(missing_dependency_hint() + '\n')
        return 1
    import webview
    launch_url = _app_url(url)
    if not wait_for_ready and wait_for_server(url):
        assistant_name = assistant_name
        import jarvis.branding
        sys.stderr.write(f'''{assistant_name()} server not ready at {url}\n''')
        return 1
    for key, val in (('WEBKIT_DISABLE_COMPOSITING_MODE', '1'), ('WEBKIT_DISABLE_DMABUF_RENDERER', '1')):
        os.environ.setdefault(key, val)
    flags = os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS', '')
    if 'disable-gpu-compositing' not in flags:
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = f'''{flags} --disable-gpu-compositing'''.strip()
    if not width:
        width
    if not height:
        height
    kwargs = {
        'width': DEFAULT_WIDTH,
        'height': DEFAULT_HEIGHT,
        'min_size': (720, 480),
        'resizable': True,
        'background_color': '#0a0c10',
        'text_select': True }
    backend = _ensure_backend()
    icon = str(ICON_PATH) if ICON_PATH.is_file() else None
    if icon and backend == 'gtk':
        kwargs['icon'] = icon
    if not title:
        title
# WARNING: Decompyle incomplete

PID_FILE = PROJECT_ROOT / 'data' / 'native_window.pid'
LOCK_FILE = PROJECT_ROOT / 'data' / 'native_window.lock'
_lock_handle = None

def _terminate_duplicate_windows():
    '''Remove stale PID file entries only; flock prevents duplicate live instances.'''
    if not PID_FILE.is_file():
        return None
    
    try:
        old_pid = int(PID_FILE.read_text(encoding = 'utf-8').strip())
        if old_pid != os.getpid():
            if not _pid_alive(old_pid):
                
                try:
                    PID_FILE.unlink(missing_ok = True)
                    return None
                    return None
                    return None
                    except (ValueError, OSError):
                        return None
                except OSError:
                    return None




def _acquire_instance_lock():
    '''Exclusive lock — one native window per machine.'''
    global _lock_handle, _lock_handle
    LOCK_FILE.parent.mkdir(parents = True, exist_ok = True)
    _lock_handle = open(LOCK_FILE, 'a+', encoding = 'utf-8')
    
    try:
        fcntl.flock(_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_handle.seek(0)
        _lock_handle.truncate()
        _lock_handle.write(str(os.getpid()))
        _lock_handle.flush()
        return True
    except BlockingIOError:
        _lock_handle.close()
    except OSError:
        pass

    _lock_handle = None
    return False


def _release_instance_lock():
    pass
# WARNING: Decompyle incomplete


def _focus_shell_via_pid(pid_file = None, *, signal_focus):
    if not pid_file.is_file():
        return False
    
    try:
        pid = int(pid_file.read_text(encoding = 'utf-8').strip())
        if not pid or _pid_alive(pid):
            
            try:
                pid_file.unlink(missing_ok = True)
                return False
                if signal_focus:
                    
                    try:
                        os.kill(pid, signal.SIGUSR1)
                        return True
                        return False
                        except (OSError, ValueError):
                            return False
                        except OSError:
                            return False
                    except OSError:
                        return False





def _window_title_visible(title = None):
    import shutil
# WARNING: Decompyle incomplete


def _focus_pyside_window():
    
    try:
        pyside_focus = focus_window
        import jarvis.pyside_shell
        if pyside_focus():
            return True
        pid_file = PROJECT_ROOT / 'data' / 'pyside_shell.pid'
        if not pid_file.is_file():
            return False
        
        try:
            if not pid_file.read_text(encoding = 'utf-8').strip():
                pid_file.read_text(encoding = 'utf-8').strip()
            pid = int('0')
            if not pid or _pid_alive(pid):
                
                try:
                    pid_file.unlink(missing_ok = True)
                    return False
                    
                    try:
                        os.kill(pid, signal.SIGUSR1)
                        time.sleep(0.35)
                        return _window_title_visible(title = None)
                        except Exception:
                            continue
                        except (OSError, ValueError):
                            return False
                        except OSError:
                            return False
                    except OSError:
                        return False






def _focus_existing_window(title = None):
    pass
# WARNING: Decompyle incomplete


def _pid_alive(pid = None):
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False



def _write_pid():
    PID_FILE.parent.mkdir(parents = True, exist_ok = True)
    PID_FILE.write_text(str(os.getpid()), encoding = 'utf-8')


def _clear_pid():
    
    try:
        PID_FILE.unlink(missing_ok = True)
        return None
    except OSError:
        return None



def _existing_window_running():
    if not PID_FILE.is_file():
        return False
    
    try:
        pid = int(PID_FILE.read_text(encoding = 'utf-8').strip())
        if not _pid_alive(pid):
            _clear_pid()
            return False
        return True
    except (OSError, ValueError):
        return False



def launch_native_window(url = None):
    '''Spawn or focus a single native window process.'''
    if not is_available():
        return False
    gui_shell_running = gui_shell_running
    import jarvis.desktop_shell
    if _existing_window_running() or gui_shell_running():
        _focus_existing_window(_window_title())
        return True
    cmd = [
        sys.executable,
        '-m',
        'jarvis.native_window',
        url,
        '--no-wait']
    
    try:
        subprocess.Popen(cmd, cwd = str(PROJECT_ROOT), stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, start_new_session = True)
        return True
    except OSError:
        exc = None
        logger.warning('Native window launch failed: %s', exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def main(argv = None):
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    load_jarvis_env()
# WARNING: Decompyle incomplete

if __name__ == '__main__':
    raise SystemExit(main())
