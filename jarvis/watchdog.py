# Source Generated with Decompyle++
# File: watchdog.cpython-312.pyc (Python 3.12)

import logging
import socket
import subprocess
import threading
import urllib.request as urllib
logger = logging.getLogger('jarvis.watchdog')

def _media_work_active():
    '''True while a GPU image/video job is running or queued.'''
    
    try:
        busy_state = busy_state
        has_active_work = has_active_work
        has_active_work_persisted = has_active_work_persisted
        import jarvis.media_jobs
        controlled_restart_active = controlled_restart_active
        import jarvis.restart_flag
        chat_active = active
        import jarvis.request_activity
        heavy_active = heavy_active
        import jarvis.request_activity
        if controlled_restart_active():
            return True
            
            try:
                if chat_active() or heavy_active():
                    return True
                
                try:
                    coding_active = has_active_work
                    import jarvis.coding_jobs
                    if coding_active():
                        return True
                        
                        try:
                            if has_active_work_persisted():
                                return True
                                
                                try:
                                    if has_active_work():
                                        return True
                                        
                                        try:
                                            st = busy_state()
                                            if not st.get('busy'):
                                                st.get('busy')
                                            return bool(st.get('pending'))
                                            except Exception:
                                                
                                                try:
                                                    continue
                                                    
                                                    try:
                                                        pass
                                                    except Exception:
                                                        exc = None
                                                        logger.debug('Media work check failed: %s', exc)
                                                        exc = None
                                                        del exc
                                                        return False
                                                        exc = None
                                                        del exc










class ServerWatchdog:
    '''Monitor Jarvis health and restart the server process if it dies.'''
    
    def __init__(self, health_url = None, interval = None, on_restart = None, failures_before_restart = ('http://127.0.0.1:8765/api/ping', 15, None, 4, 10), timeout = ('health_url', str, 'interval', int, 'failures_before_restart', int, 'timeout', float)):
        self.health_url = health_url
        self.interval = interval
        self.on_restart = on_restart
        self.failures_before_restart = max(1, failures_before_restart)
        self.timeout = timeout
        self._stop = threading.Event()
        self._thread = None
        self._server_proc = None
        self._restart_count = 0
        self._consecutive_failures = 0

    
    def set_server_process(self = None, proc = None):
        self._server_proc = proc
        self._consecutive_failures = 0

    
    def _healthy(self = None):
        
        try:
            resp = urllib.request.urlopen(self.health_url, timeout = self.timeout)
            
            try:
                None(None, None)
                return 
                with None:
                    if not None, resp.status == 200:
                        pass
                
                try:
                    return None
                    
                    try:
                        pass
                    except Exception:
                        logger.debug('Health check failed: %s', exc)
                        None = None
                        del exc
                        return False
                        exc = None
                        del exc





    
    def _port_open(self = None):
        
        try:
            urlparse = urlparse
            import urllib.parse
            parsed = urlparse(self.health_url)
            if not parsed.hostname:
                parsed.hostname
            host = '127.0.0.1'
            if not parsed.port:
                parsed.port
            port = 8765
            socket.create_connection((host, port), timeout = self.timeout)
            
            try:
                None(None, None)
                return True
                with None:
                    if not None:
                        pass
                
                try:
                    return None
                    
                    try:
                        pass
                    except OSError:
                        return False





    
    def _restart_server(self = None):
        self._consecutive_failures = self, self._restart_count += 1, ._restart_count
        self._consecutive_failures = 0
    # WARNING: Decompyle incomplete

    
    def _loop(self = None):
        pass
    # WARNING: Decompyle incomplete

    
    def start(self = None):
        if self._thread and self._thread.is_alive():
            return None
        self._stop.clear()
        self._thread = threading.Thread(target = self._loop, daemon = True, name = 'jarvis-watchdog')
        self._thread.start()
        logger.info('Watchdog started (interval=%ds)', self.interval)

    
    def stop(self = None):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout = 3)
            return None


