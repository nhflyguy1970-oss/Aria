# Source Generated with Decompyle++
# File: remote_control.cpython-312.pyc (Python 3.12)

'''Safe remote actions from LAN automation webhooks.'''
from __future__ import annotations
import logging
import os
import subprocess
from pathlib import Path
from jarvis.config import DATA_DIR, PROJECT_ROOT
log = logging.getLogger('jarvis')
SCRIPTS_DIR = DATA_DIR / 'scripts'

def run_whitelisted_script(name = None, *, timeout):
    '''Run an executable script from data/scripts/ only.'''
    if not name:
        name
    raw = ''.strip()
    if not raw:
        return (False, 'Script name required.')
    base = Path(raw).name
    if base != raw and '..' in raw and '/' in raw or '\\' in raw:
        return (False, 'Use a simple script filename only (no paths).')
    script = (SCRIPTS_DIR / base).resolve()
    
    try:
        script.relative_to(SCRIPTS_DIR.resolve())
        if not script.is_file():
            return (False, f'''Not found: data/scripts/{base}''')
        if not None.access(script, os.X_OK):
            return (False, f'''Not executable: data/scripts/{base} — chmod +x first.''')
        
        try:
            proc = subprocess.run([
                str(script)], cwd = str(PROJECT_ROOT), capture_output = True, text = True, timeout = timeout, check = False)
            if not proc.stdout:
                proc.stdout
            if not proc.stderr:
                proc.stderr
            out = ('' + '\n' + '').strip()
            if proc.returncode != 0:
                if not out[:2000]:
                    out[:2000]
                return (False, f'''Exit code {proc.returncode}''')
            if not out[:2000]:
                out[:2000]
            return (None, 'OK')
            except ValueError:
                return (False, 'Script must live in data/scripts/.')
        except subprocess.TimeoutExpired:
            return 




def wake_on_lan(mac = None):
    '''Send magic packet if JARVIS_WOL_MAC or mac arg is set.'''
    if not mac:
        mac
        if not os.getenv('JARVIS_WOL_MAC'):
            os.getenv('JARVIS_WOL_MAC')
    target = ''.strip()
    if not target:
        return (False, 'Set JARVIS_WOL_MAC or pass mac in webhook body.')
    
    try:
        send_magic_packet = send_magic_packet
        import wakeonlan
        send_magic_packet(target)
        return (True, f'''Wake-on-LAN sent to {target}.''')
    except ImportError:
        pass

    wake = subprocess.run([
        'which',
        'etherwake'], capture_output = True, text = True)
    if wake.returncode == 0:
        proc = subprocess.run([
            'sudo',
            'etherwake',
            target], capture_output = True, text = True, timeout = 10)
        if proc.returncode == 0:
            return (True, f'''etherwake sent to {target}.''')
        if not proc.stderr:
            proc.stderr
            if not proc.stdout:
                proc.stdout
        return (None, 'etherwake failed'[:500])

