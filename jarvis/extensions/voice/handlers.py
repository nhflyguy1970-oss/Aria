# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''P1 voice handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.response import ok
voice_smoke_test = (lambda assistant = None, params = None, message = register_action('voice_smoke_test', info = True, module = 'audio', description = 'Hello ARIA voice smoke test'): run_voice_smoke = run_voice_smokeimport jarvis.voice_smokeresult = run_voice_smoke(assistant = assistant)lines = [
f'''**Voice smoke test:** {result['passed']}/{result['total']} passed''']if not result.get('checks'):
result.get('checks')# WARNING: Decompyle incomplete
)()
chat_session_list = (lambda assistant = None, params = None, message = register_action('chat_session_list', info = True, module = 'general', description = 'List chat sessions'): list_sessions = list_sessionsimport jarvis.chat_sessionssessions = list_sessions()if not sessions:
ok('No saved chat sessions.', module = 'general', type = 'sessions')lines = Nonefor s in sessions[:15]:
pin = '📌 ' if s.get('pinned') else ''lines.append(f'''- {pin}**{s.get('title')}** (`{s.get('id')}`)''')ok('**Chat sessions:**\n' + '\n'.join(lines), module = 'general', type = 'sessions'))()
