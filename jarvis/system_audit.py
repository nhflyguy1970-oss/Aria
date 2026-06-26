# Source Generated with Decompyle++
# File: system_audit.cpython-312.pyc (Python 3.12)

'''System audit runner for CLI and ARIA API.'''
from __future__ import annotations
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any
from jarvis.audit_paths import audit_path_env, jarvis_root, resolve_script
from jarvis.system_audit_engine import run_engine
_CACHE_LOCK = threading.Lock()
_CACHE: 'dict[str, Any] | None' = None
_CACHE_AT: 'float' = 0
_RUNNING = False
_DEFAULT_TTL = float(os.getenv('JARVIS_AUDIT_CACHE_SEC', '30'))

def _askpass_script():
    return resolve_script('sudo-askpass-zenity.sh')


def _sudoers_install_script():
    return resolve_script('install-audit-sudoers.sh')


def _gui_sudo_available():
    askpass = _askpass_script()
    if not askpass.is_file() or os.access(askpass, os.X_OK):
        return False
    env = audit_path_env()
    if shutil.which('zenity', path = env['PATH']) or shutil.which('kdialog', path = env['PATH']):
        if not os.getenv('DISPLAY'):
            os.getenv('DISPLAY')
        return bool(os.getenv('WAYLAND_DISPLAY'))


def _sudo_askpass_env():
    env = audit_path_env()
    env['SUDO_ASKPASS'] = str(_askpass_script())
    return env


def sudo_audit_available():
    script = str(resolve_script('audit-system.sh'))
    
    try:
        proc = subprocess.run([
            'sudo',
            '-n',
            '-l'], capture_output = True, text = True, timeout = 5, check = False)
        if proc.returncode == 0:
            proc.returncode == 0
            if not proc.stdout:
                proc.stdout
        return script in ''
    except Exception:
        return False



def _try_install_passwordless_sudo(env = None):
    install = _sudoers_install_script()
    if not sudo_audit_available() or install.is_file():
        return None
    
    try:
        cmd = [
            'sudo',
            '-A',
            str(install)] if env else [
            'sudo',
            '-n',
            str(install)]
        subprocess.run(cmd, env = env, timeout = 120, check = False, cwd = str(jarvis_root()))
        return None
    except Exception:
        return None



def _elevated_for_smart():
    if os.geteuid() == 0:
        return True
    if sudo_audit_available():
        return True
    if _run_sudo_probe():
        return True
    return False


def _run_sudo_probe():
    
    try:
        if _gui_sudo_available():
            env = _sudo_askpass_env()
            proc = subprocess.run([
                'sudo',
                '-A',
                'true'], env = env, timeout = 30, check = False)
            if proc.returncode == 0:
                _try_install_passwordless_sudo(env)
                return True
                
                try:
                    return subprocess.run([
                        'sudo',
                        '-n',
                        'true'], timeout = 5, check = False).returncode == 0
                except Exception:
                    return False




def clear_audit_cache():
    global _CACHE, _CACHE_AT
    _CACHE_LOCK
    _CACHE = None
    _CACHE_AT = 0
    None(None, None)
    return None
    with None:
        if not None:
            pass


def run_audit(*, use_cache, cache_ttl):
    '''Run 12-phase system audit and return structured results.'''
    pass
# WARNING: Decompyle incomplete


def get_cached_audit():
    _CACHE_LOCK
    None(None, None)
    return 
    with None:
        if not None, dict(_CACHE) if _CACHE else None:
            pass


def cli_main():
    import sys
    data = run_audit(use_cache = False)
    print(json.dumps(data, indent = 2))
    if data.get('result') == 'fail':
        sys.exit(data.get('exit_code', 1))
        return None
    None(None(None, 0))

if __name__ == '__main__':
    cli_main()
    return None
