# Source Generated with Decompyle++
# File: desktop_shell.cpython-312.pyc (Python 3.12)

'''Shared helpers for optional desktop shells (Electron, PySide6, native).'''
from __future__ import annotations
import fcntl
import logging
import os
import subprocess
import sys
from pathlib import Path
logger = logging.getLogger('jarvis.desktop_shell')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = PROJECT_ROOT / 'assets' / 'jarvis-tray.png'
DEFAULT_WIDTH = int(os.getenv('JARVIS_NATIVE_WIDTH', '1280'))
DEFAULT_HEIGHT = int(os.getenv('JARVIS_NATIVE_HEIGHT', '860'))

def app_url(url = None, *, shell):
    out = url
    if 'app=1' not in out:
        out = f'''{out}{'&' if '?' in out else '?'}app=1'''
    if shell and f'''shell={shell}''' not in out:
        out = f'''{out}&shell={shell}'''
    return out


def window_title():
    assistant_window_title = assistant_window_title
    import jarvis.branding
    is_uncensored = is_uncensored
    import jarvis.config
    return assistant_window_title(uncensored = is_uncensored())


def default_url():
    host = os.getenv('JARVIS_HOST', '127.0.0.1')
    if host in ('0.0.0.0', '::'):
        host = '127.0.0.1'
    port = os.getenv('JARVIS_PORT', '8765')
    return f'''http://{host}:{port}'''


def wait_for_server(url = None, timeout_sec = None):
    _wait = wait_for_server
    import jarvis.native_window
    return _wait(url, timeout_sec = timeout_sec)


def focus_existing_window(title = None):
    _focus_existing_window = _focus_existing_window
    import jarvis.native_window
    if not title:
        title
    return _focus_existing_window(window_title())


def pid_alive(pid = None):
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False



class InstanceLock:
    '''Exclusive flock for one shell window per name.'''
    
    def __init__(self = None, name = None):
        self.name = name
        self.lock_file = PROJECT_ROOT / 'data' / f'''{name}.lock'''
        self.pid_file = PROJECT_ROOT / 'data' / f'''{name}.pid'''
        self._handle = None

    
    def acquire(self = None):
        self.lock_file.parent.mkdir(parents = True, exist_ok = True)
        if self.another_running():
            return False
        self._handle = open(self.lock_file, 'a+', encoding = 'utf-8')
        
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._handle.seek(0)
            self._handle.truncate()
            self._handle.write(str(os.getpid()))
            self._handle.flush()
            self.pid_file.write_text(str(os.getpid()), encoding = 'utf-8')
            return True
        except BlockingIOError:
            self._handle.close()
        except OSError:
            pass

        self._handle = None
        if not self.another_running():
            self.lock_file.unlink(missing_ok = True)
        else:
            except OSError:
                pass
            self._handle = open(self.lock_file, 'a+', encoding = 'utf-8')
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._handle.close()
        except OSError:
            pass
        self._handle = None
        return False
        return False
        continue

    
    def release(self = None):
        pass
    # WARNING: Decompyle incomplete

    
    def another_running(self = None):
        if not self.lock_file.is_file():
            return False
    # WARNING: Decompyle incomplete


GUI_SHELL_LOCK = InstanceLock('gui_shell')
_ACTIVE_SHELL_FILE = PROJECT_ROOT / 'data' / 'gui_shell_active.txt'

def acquire_gui_shell_lock(shell_name = None):
    '''Exclusive lock — one desktop shell (pyside/electron/native) at a time.'''
    if not GUI_SHELL_LOCK.acquire():
        return False
    
    try:
        _ACTIVE_SHELL_FILE.write_text(shell_name, encoding = 'utf-8')
        return True
    except OSError:
        return True



def release_gui_shell_lock():
    GUI_SHELL_LOCK.release()
    
    try:
        _ACTIVE_SHELL_FILE.unlink(missing_ok = True)
        return None
    except OSError:
        return None



def gui_shell_running():
    return GUI_SHELL_LOCK.another_running()


def active_gui_shell():
    
    try:
        return _ACTIVE_SHELL_FILE.read_text(encoding = 'utf-8').strip()
    except OSError:
        return ''



def spawn_detached(cmd = None, *, env, extra_env):
    
    try:
        if not env:
            env
        proc_env = dict(os.environ)
        if extra_env:
            proc_env.update(extra_env)
        subprocess.Popen(cmd, cwd = str(PROJECT_ROOT), env = proc_env, stdin = subprocess.DEVNULL, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, start_new_session = True, close_fds = True)
        return True
    except OSError:
        exc = None
        logger.warning('Detached launch failed: %s', exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def python_exe():
    return sys.executable

