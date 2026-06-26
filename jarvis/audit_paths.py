# Source Generated with Decompyle++
# File: audit_paths.cpython-312.pyc (Python 3.12)

'''Resolve Jarvis install paths for system audit (any disk / layout).'''
from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
from jarvis.config import DATA_DIR, PROJECT_ROOT

def _env_files():
    '''jarvis.env locations without calling jarvis_root() (avoids circular imports).'''
    pass
# WARNING: Decompyle incomplete


def read_env_file_var(name = None):
    for env_path in _env_files():
        if not env_path.is_file():
            continue
        text = env_path.read_text(encoding = 'utf-8', errors = 'replace')
        for line in text.splitlines():
            line = line.strip()
            if line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[7:].strip()
            if not line.startswith(f'''{name}='''):
                continue
            val = line.split('=', 1)[1].strip()
            if (val.startswith('"') or val.endswith('"') or val.startswith("'")) and val.endswith("'"):
                val = val[1:-1]
            val = val.replace('$HOME', str(Path.home())).replace('${HOME}', str(Path.home()))
            if not val:
                continue
            
            
            return _env_files(), text.splitlines(), val
    return ''
    except OSError:
        continue


def jarvis_root():
    '''Active Jarvis tree — env override, jarvis.env, else package location.'''
    for raw in (os.environ.get('JARVIS_ROOT', ''), os.environ.get('ARIA_ROOT', ''), read_env_file_var('JARVIS_ROOT'), read_env_file_var('ARIA_ROOT')):
        if not raw.strip():
            continue
        root = Path(raw.strip()).expanduser().resolve()
        if not (root / 'jarvis' / 'config.py').is_file() and (root / 'scripts').is_dir():
            continue
        
        return (os.environ.get('JARVIS_ROOT', ''), os.environ.get('ARIA_ROOT', ''), read_env_file_var('JARVIS_ROOT'), read_env_file_var('ARIA_ROOT')), root
    return PROJECT_ROOT.resolve()


def _read_env_file_paths():
    extra = []
    files = list(_env_files())
    root_env = jarvis_root() / 'data' / 'jarvis.env'
    if root_env not in files:
        files.append(root_env)
    for env_path in files:
        if not env_path.is_file():
            continue
        text = env_path.read_text(encoding = 'utf-8', errors = 'replace')
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('#') or 'PATH=' not in line:
                continue
            m = re.search('PATH=(?:"([^"]*)"|\\\'([^\\\']*)\\\'|([^;\\s]+))', line)
            if not m:
                continue
            if not m.group(1):
                m.group(1)
                if not m.group(2):
                    m.group(2)
                    if not m.group(3):
                        m.group(3)
            val = ''
            for part in val.split(':'):
                part = part.strip().replace('$HOME', str(Path.home()))
                part = part.replace('${HOME}', str(Path.home()))
                if not part:
                    continue
                extra.append(part)
    return extra
    except OSError:
        continue


def _login_shell_path():
    
    try:
        proc = subprocess.run([
            'bash',
            '-lc',
            'echo $PATH'], capture_output = True, text = True, timeout = 8, check = False)
        if proc.returncode == 0:
            if not proc.stdout:
                proc.stdout
            if ''.strip():
                return proc.stdout.strip()
            except Exception:
                return ''



def _standard_tool_dirs():
    home = Path.home()
    dirs = [
        home / '.cargo' / 'bin',
        home / '.local' / 'bin',
        Path('/usr/local/bin'),
        Path('/usr/bin'),
        Path('/snap/bin')]
    nvm = home / '.nvm' / 'versions' / 'node'
    if nvm.is_dir():
        for ver in sorted(nvm.iterdir(), reverse = True):
            b = ver / 'bin'
            if not b.is_dir():
                continue
            dirs.append(b)
            sorted(nvm.iterdir(), reverse = True)
    rustup = home / '.rustup' / 'toolchains'
    if rustup.is_dir():
        for tc in sorted(rustup.iterdir(), reverse = True):
            b = tc / 'bin'
            if not b.is_dir():
                continue
            dirs.append(b)
# WARNING: Decompyle incomplete


def audit_path_env():
    '''Full PATH for subprocess + shutil.which during audit.'''
    pass
# WARNING: Decompyle incomplete


def audit_path_string():
    return audit_path_env()['PATH']


def resolve_venv_python():
    '''Jarvis venv — may live on another disk via JARVIS_VENV.'''
    candidates = []
    for raw in (os.environ.get('JARVIS_VENV', ''), os.environ.get('VIRTUAL_ENV', ''), read_env_file_var('JARVIS_VENV')):
        if not raw.strip():
            continue
        p = Path(raw.strip()).expanduser()
        candidates.append(p / 'bin' / 'python' if p.is_dir() else p)
    root = jarvis_root()
    candidates.extend([
        root / 'venv' / 'bin' / 'python',
        root / '.venv' / 'bin' / 'python'])
    for c in candidates:
        if c.is_file() and os.access(c, os.X_OK):
            
            return candidates, Path(c)
    return None
    except OSError:
        continue


def resolve_script(rel = None):
    '''Resolve scripts/foo.sh under the active Jarvis root.'''
    rel = rel.removeprefix('/')
    if rel.startswith('scripts/'):
        return jarvis_root() / rel
    return None() / 'scripts' / rel


def install_command(rel = None, *, note):
    script = resolve_script(rel)
    cmd = f'''bash {script}'''
    if note:
        return f'''{cmd}  # {note}'''


def configured_gpu_preference():
    if not os.environ.get('JARVIS_GPU_PREFER', ''):
        os.environ.get('JARVIS_GPU_PREFER', '')
        if not read_env_file_var('JARVIS_GPU_PREFER'):
            read_env_file_var('JARVIS_GPU_PREFER')
    raw = 'auto'.strip().lower()
    if raw in ('nvidia', 'amd', 'both', 'hybrid', 'auto'):
        if raw in ('both', 'hybrid'):
            return 'both'
        return None


def nvidia_ai_hybrid_configured():
    '''AMD + NVIDIA present and Jarvis env routes AI to NVIDIA.'''
    if configured_gpu_preference() == 'nvidia':
        configured_gpu_preference() == 'nvidia'
        if not read_env_file_var('HIP_VISIBLE_DEVICES') == '-1':
            read_env_file_var('HIP_VISIBLE_DEVICES') == '-1'
    return os.environ.get('HIP_VISIBLE_DEVICES', '').strip() == '-1'


def audit_locations():
    root = jarvis_root()
    venv = resolve_venv_python()
    data = root / 'data'
    if not data.is_dir():
        data = DATA_DIR
    if venv:
        return {
            'jarvis_root': str(root),
            'data_dir': str(data),
            'venv_python': str(venv) }
    return {
        'jarvis_root': None,
        'data_dir': str(root),
        'venv_python': str(data) }

