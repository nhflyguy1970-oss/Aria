# Source Generated with Decompyle++
# File: notify_util.cpython-312.pyc (Python 3.12)

'''Desktop notifications for ARIA.'''
from __future__ import annotations
import subprocess

def notify_jarvis(title = None, body = None, *, icon):
    assistant_name = assistant_name
    import jarvis.branding
    app = assistant_name()
    
    try:
        cmd = [
            'notify-send',
            '-a',
            app,
            title,
            body]
        if icon:
            cmd = [
                'notify-send',
                '-a',
                app,
                '-i',
                icon,
                title,
                body]
        subprocess.run(cmd, check = False, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, timeout = 5)
        return None
    except Exception:
        return None


