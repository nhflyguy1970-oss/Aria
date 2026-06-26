# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Security handlers.'''
from __future__ import annotations
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
security_lock = (lambda assistant = None, params = None, message = register_action('security_lock', module = 'security', description = 'Lock GUI session'): revoke_all_sessions = revoke_all_sessionsimport jarvis.security.pin_lockrevoked = revoke_all_sessions()ok('GUI locked.', module = 'security', type = 'lock', lock = True, sessions_revoked = revoked))()
security_status = (lambda assistant = None, params = None, message = register_action('security_status', info = True, module = 'security', description = 'Security and brain mode status'): brain_mode_status = brain_mode_statusimport jarvis.security.brain_modeface_status = face_statusimport jarvis.security.face_authlock_status = lock_statusimport jarvis.security.pin_lockls = lock_status()fs = face_status()bm = brain_mode_status()ok(f'''Lock: {'capable' if ls.get('lock_capable') else 'off'} · Face: {'enrolled' if fs.get('enrolled') else 'no'} · Brain: {bm.get('label')}''', module = 'security', lock = ls, face = fs, brain = bm))()
