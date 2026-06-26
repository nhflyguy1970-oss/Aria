# Source Generated with Decompyle++
# File: system_audit_engine.cpython-312.pyc (Python 3.12)

'''14-phase whole-system audit engine for ARIA / CLI.'''
from __future__ import annotations
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jarvis.audit_paths import audit_locations, audit_path_env, audit_path_string, configured_gpu_preference, install_command, jarvis_root, nvidia_ai_hybrid_configured, read_env_file_var, resolve_script, resolve_venv_python
from jarvis.config import DATA_DIR
Item = dict[(str, str)]
PhaseResult = dict[(str, Any)]
_INSTALL_SCRIPTS: 'dict[str, str]' = {
    'audit_deps': 'scripts/install-system-audit-deps.sh',
    'dependencies': 'scripts/install-dependencies.sh',
    'ollama': 'scripts/install-ollama-latest.sh',
    'rocm_pytorch': 'scripts/install-rocm-pytorch.sh',
    'cuda_pytorch': 'scripts/install-cuda-pytorch.sh',
    'nvidia_gpu': 'scripts/enable-nvidia-gpu.sh',
    'docker': 'scripts/install-docker.sh',
    'audit_sudoers': 'scripts/install-audit-sudoers.sh',
    'lsp': 'scripts/install-lsp-servers.sh',
    'verify': 'scripts/verify-setup.sh',
    'harden': 'scripts/harden-security.sh',
    'comfyui': 'scripts/install-comfyui-deps.sh',
    'dev_tools': 'scripts/install-dev-tools.sh',
    'rust': 'scripts/install-rust.sh' }

def _fix_script(key = None, *, note):
    rel = _INSTALL_SCRIPTS.get(key, key)
    if rel.startswith(('curl ', 'sudo apt', 'http')):
        cmd = rel
    else:
        cmd = install_command(rel)
    if note:
        return f'''{cmd}  # {note}'''


def _audit_path():
    return audit_path_string()


def _audit_env():
    return audit_path_env()


def install_script_path(key = None):
    rel = _INSTALL_SCRIPTS.get(key)
    if rel or rel.startswith(('curl ', 'sudo apt', 'http')):
        return None
    path = resolve_script(rel)
    if path.is_file():
        return path


def _gui_sudo_for_install(env = None):
    askpass = env.get('SUDO_ASKPASS', '')
    if not askpass or Path(askpass).is_file():
        return False
    if env.get('DISPLAY') or env.get('WAYLAND_DISPLAY'):
        return True
    for display in (':0', ':1', ':2'):
        if not Path(f'''/tmp/.X11-unix/X{display.lstrip(':')}''').exists():
            continue
        env['DISPLAY'] = display
        (':0', ':1', ':2')
        return True
    return False


def _install_argv(script = None, env = None):
    '''Run install script; wrap sudo with -A when zenity askpass is available.'''
    script_q = shlex.quote(str(script))
    if _gui_sudo_for_install(env):
        askpass_q = shlex.quote(env['SUDO_ASKPASS'])
        inner = f'''export SUDO_ASKPASS={askpass_q}; sudo() {{ command sudo -A "$@"; }}; exec bash {script_q}'''
        return [
            'bash',
            '-c',
            inner]
    return [
        None,
        str(script)]


def run_install_script(key = None):
    '''Run a whitelisted Jarvis install script (from ARIA System tab).'''
    script = install_script_path(key)
    if not script:
        return {
            'ok': False,
            'error': f'''Unknown or missing install script: {key}''' }
    env = None()
    askpass = resolve_script('sudo-askpass-zenity.sh')
    if askpass.is_file() and os.access(askpass, os.X_OK):
        env['SUDO_ASKPASS'] = str(askpass)
    root = jarvis_root()
    
    try:
        proc = subprocess.run(_install_argv(script, env), capture_output = True, text = True, timeout = 900, cwd = str(root), env = env, check = False)
        if not proc.stdout:
            proc.stdout
        out = ''[-6000:]
        if not proc.stderr:
            proc.stderr
        err = ''[-3000:]
        ok = proc.returncode == 0
        error = ''
        if not ok:
            combined = f'''{err}\n{out}'''.lower()
            if 'password is required' in combined or 'askpass' in combined:
                error = f'''Install needs sudo. A password dialog should appear — if it did not, run in a terminal: bash {script}'''
            elif err.strip():
                error = err.strip().splitlines()[-1][:240]
            else:
                error = f'''Script exited with code {proc.returncode}'''
        if not ok:
            not ok
        if ok:
            return {
                'ok': ok,
                'install_key': key,
                'script': str(script),
                'exit_code': proc.returncode,
                'stdout': out,
                'stderr': err,
                'error': error,
                'needs_gui_sudo': 'password' in f'''{err}{out}'''.lower(),
                'message': 'Install finished' }
        if not 'password' in f'''{err}{out}'''.lower():
            'password' in f'''{err}{out}'''.lower()
        return {
            'ok': None,
            'install_key': ok,
            'script': key,
            'exit_code': str(script),
            'stdout': proc.returncode,
            'stderr': out,
            'error': err,
            'needs_gui_sudo': error,
            'message': 'Install failed — see output' }
    except subprocess.TimeoutExpired:
        return 
        except Exception:
            del exc
            return None
            None = 
            del exc



def _dev_install_fix(tool = None):
    if tool in ('git',):
        return _fix_script('dependencies', note = f'''installs {tool}''')
    if None in ('gcc', 'cmake', 'make', 'node', 'npm', 'java'):
        return _fix_script('dev_tools', note = f'''installs {tool}''')
    if None in ('cargo', 'rustc'):
        return _fix_script('rust', note = f'''installs {tool} via rustup''')
    return None('dev_tools')

Collector = <NODE:12>()

def _run(cmd = None, *, timeout, text):
    return subprocess.run(cmd, capture_output = True, text = text, timeout = timeout, check = False, env = _audit_env())


def _run_sudo(cmd = None, *, timeout):
