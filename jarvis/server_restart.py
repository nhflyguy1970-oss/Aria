# Source Generated with Decompyle++
# File: server_restart.cpython-312.pyc (Python 3.12)

'''Request Jarvis HTTP server restart from the GUI (handled by tray parent).'''
from __future__ import annotations
import logging
import os
import signal
import time
from pathlib import Path
from jarvis.config import DATA_DIR
logger = logging.getLogger('jarvis.server_restart')
RESTART_FLAG = DATA_DIR / 'restart_server.request'
_restart_watcher_started = False

def is_tray_managed():
    return os.getenv('JARVIS_SERVICES_MANAGED') == '1'


def _signal_tray_restart():
    """Ask serve's parent (tray) to restart via SIGUSR1."""
    
    try:
        parent = os.getppid()
        if parent <= 1:
            return False
            
            try:
                os.kill(parent, signal.SIGUSR1)
                return True
            except OSError:
                exc = None
                logger.warning('Could not signal tray for restart: %s', exc)
                exc = None
                del exc
                return False
                exc = None
                del exc




def request_restart(*, source, detail):
    '''Ask the tray/daemon parent to restart the serve subprocess.'''
    log_restart_event = log_restart_event
    import jarvis.restart_audit
    if not detail:
        detail
    log_restart_event(source, detail = 'request_restart')
    if not is_tray_managed():
        return {
            'ok': False,
            'message': 'Server restart needs the tray launcher. Run `./scripts/stop-jarvis.sh` then `./scripts/launch-jarvis.sh`, or `./scripts/restart-jarvis-server.sh` from a terminal.' }
    if None():
        logger.info('Server restart requested — signaled tray (SIGUSR1)')
        return {
            'ok': True,
            'message': 'Jarvis server restarting…' }
    
    try:
        DATA_DIR.mkdir(parents = True, exist_ok = True)
        RESTART_FLAG.write_text(str(time.time()), encoding = 'utf-8')
        logger.info('Server restart requested — flag file (tray watcher)')
        return {
            'ok': True,
            'message': 'Jarvis server restarting…' }
    except OSError:
        exc = None
        del exc
        return None
        None = 
        del exc



def consume_restart_request():
    '''True if a restart was requested (flag cleared). Called from tray process only.'''
    if not RESTART_FLAG.is_file():
        return False
    
    try:
        RESTART_FLAG.unlink()
        return True
    except OSError:
        return True



def start_restart_watcher(on_restart = None):
    '''Poll for GUI restart requests (tray process only). Backup if SIGUSR1 missed.'''
    pass
# WARNING: Decompyle incomplete

