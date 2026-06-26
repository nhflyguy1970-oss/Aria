# Source Generated with Decompyle++
# File: server_shutdown.cpython-312.pyc (Python 3.12)

'''Request full Jarvis shutdown from the GUI (handled by tray parent).'''
from __future__ import annotations
import logging
import os
import signal
import threading
import time
from pathlib import Path
from jarvis.config import DATA_DIR
logger = logging.getLogger('jarvis.server_shutdown')
SHUTDOWN_FLAG = DATA_DIR / 'shutdown_jarvis.request'
_shutdown_watcher_started = False

def is_tray_managed():
    return os.getenv('JARVIS_SERVICES_MANAGED') == '1'


def _signal_tray_shutdown():
    """Ask serve's parent (tray) to quit via SIGUSR2."""
    
    try:
        parent = os.getppid()
        if parent <= 1:
            return False
            
            try:
                os.kill(parent, signal.SIGUSR2)
                return True
            except OSError:
                exc = None
                logger.warning('Could not signal tray for shutdown: %s', exc)
                exc = None
                del exc
                return False
                exc = None
                del exc




def _free_vram_best_effort():
    
    try:
        stop_all_for_gaming = stop_all_for_gaming
        import jarvis.gaming_shutdown
        return stop_all_for_gaming()
    except Exception:
        exc = None
        logger.debug('Gaming shutdown skipped: %s', exc)
        free_vram = free_vram
        import jarvis.vram_guard
        del exc
        return None
        except Exception:
            None, free_vram()
            del exc
            return None
        None = None
        del exc



def _exit_serve_process(delay = None):
    pass
# WARNING: Decompyle incomplete


def request_shutdown(*, source, detail, free_vram, stop_everything):
    '''Stop Jarvis completely — tray + server + GPU services for gaming.'''
    log_restart_event = log_restart_event
    import jarvis.restart_audit
    if not detail:
        detail
    log_restart_event(source, detail = 'request_shutdown')
    gaming_result = { }
    if free_vram or stop_everything:
        gaming_result = _free_vram_best_effort()
# WARNING: Decompyle incomplete


def consume_shutdown_request():
    '''True if shutdown was requested (flag cleared). Tray process only.'''
    if not SHUTDOWN_FLAG.is_file():
        return False
    
    try:
        SHUTDOWN_FLAG.unlink()
        return True
    except OSError:
        return True



def start_shutdown_watcher(on_shutdown = None):
    '''Poll for GUI shutdown requests (tray process only).'''
    pass
# WARNING: Decompyle incomplete

