# Source Generated with Decompyle++
# File: electron_shell.cpython-312.pyc (Python 3.12)

'''Electron desktop shell for ARIA (P4 #88).'''
from __future__ import annotations
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from jarvis.desktop_shell import InstanceLock, PROJECT_ROOT, acquire_gui_shell_lock, app_url, default_url, focus_existing_window, gui_shell_running, release_gui_shell_lock, spawn_detached, wait_for_server, window_title
logger = logging.getLogger('jarvis.electron_shell')
ELECTRON_DIR = PROJECT_ROOT / 'scripts' / 'electron-shell'
LOCK = InstanceLock('electron_shell')

def electron_dir():
    return ELECTRON_DIR


def electron_binary():
    candidates = [
        ELECTRON_DIR / 'node_modules' / 'electron' / 'dist' / 'electron',
        ELECTRON_DIR / 'node_modules' / '.bin' / 'electron']
    for path in candidates:
        if not path.is_file():
            continue
        
        return candidates, path


def is_installed():
    return electron_binary() is not None


def is_available():
    if not is_installed():
        return False
    if not shutil.which('node'):
        shutil.which('node')
    return bool(shutil.which('nodejs'))


def missing_dependency_hint():
    if not shutil.which('node') and shutil.which('nodejs'):
        return 'Node.js is required for the Electron shell.\nInstall Node 18+, then run: ./scripts/install-electron-shell.sh'
    if not is_installed():
        return 'Electron shell is not installed.\nRun: ./scripts/install-electron-shell.sh'
    return ''


def _shell_env(url = None):
    env = os.environ.copy()
    env['JARVIS_URL'] = app_url(url)
    env['JARVIS_WINDOW_TITLE'] = window_title()
    env['JARVIS_SHELL'] = 'electron'
    return env


def launch_electron_shell(url = None):
    '''Spawn Electron shell detached (single instance).'''
    if not is_available():
        return False
    if gui_shell_running() or LOCK.another_running():
        focus_existing_window()
        return True
    binary = electron_binary()
    if not binary:
        return False
    return spawn_detached([
        str(binary),
        str(ELECTRON_DIR)], env = _shell_env(url))


def run_electron_blocking(url = None, *, wait_for_ready):
    if not is_available():
        sys.stderr.write(missing_dependency_hint() + '\n')
        return 1
    if gui_shell_running():
        focus_existing_window()
        return 0
    if not acquire_gui_shell_lock('electron'):
        focus_existing_window()
        return 0
# WARNING: Decompyle incomplete


def install_shell():
    if not shutil.which('npm'):
        return {
            'ok': False,
            'error': 'npm not found — install Node.js 18+' }
    
    try:
        proc = subprocess.run([
            'npm',
            'install'], cwd = str(ELECTRON_DIR), capture_output = True, text = True, timeout = 600, check = False)
        if proc.returncode != 0:
            if not proc.stderr:
                proc.stderr
                if not proc.stdout:
                    proc.stdout
            return {
                'ok': False,
                'error': 'npm install failed'[:500] }
        if not electron_binary():
            electron_binary()
        return {
            'ok': None,
            'path': str(ELECTRON_DIR),
            'binary': str('') }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def status():
    if not electron_binary():
        electron_binary()
    if not gui_shell_running():
        gui_shell_running()
    return {
        'available': is_available(),
        'installed': is_installed(),
        'path': str(ELECTRON_DIR),
        'binary': str(''),
        'running': LOCK.another_running() }


def main(argv = None):
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    load_jarvis_env()
# WARNING: Decompyle incomplete

if __name__ == '__main__':
    raise SystemExit(main())
