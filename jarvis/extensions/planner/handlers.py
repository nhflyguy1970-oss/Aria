# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Planner action handlers.'''
from __future__ import annotations
import re
from jarvis.feature_flags import planner_enabled
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _disabled():
    return err('Planner is disabled (JARVIS_PLANNER=0).', module = 'planner')

planner_add_task = (lambda assistant = None, params = None, message = register_action('planner_add_task', module = 'planner', description = 'Add life to-do'): if not planner_enabled():
_disabled()add_task = add_taskimport jarvis.planner_storeif not params.get('text'):
params.get('text')text = ''.strip()if not text:
m = re.search('(?:add|create)\\s+(?:a\\s+)?task\\s+(.+)', message, re.I)text = m.group(1) if m else message.strip()try:
task = add_task(text)ok(f'''Added task: **{task['text']}**''', module = 'planner', type = 'planner')except ValueError:
exc = Nonedel excNoneNone = del exc)()
planner_list_tasks = (lambda assistant = None, params = None, message = register_action('planner_list_tasks', info = True, module = 'planner', description = 'List planner tasks'): if not planner_enabled():
_disabled()list_tasks = list_tasksimport jarvis.planner_storetasks = list_tasks()if not tasks:
ok('No open planner tasks.', module = 'planner', type = 'planner')lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(tasks())
    return ok(f'''**Planner tasks:**\n{lines}''', module = 'planner', type = 'planner')
)()
planner_set_timer = (lambda assistant = None, params = None, message = register_action('planner_set_timer', module = 'planner', description = 'Set countdown timer'): if not planner_enabled():
_disabled()set_timer = set_timerimport jarvis.planner_storeif not params.get('duration'):
params.get('duration')duration = ''.strip()if not params.get('label'):
params.get('label')if not ''.strip():
''.strip()label = Noneif not duration:
m = re.search('timer\\s+(?:for\\s+)?(.+)', message, re.I)duration = m.group(1).strip() if m else ''try:
t = set_timer(duration, label)ok(f'''Timer **{t['label']}** set for {t['remaining_seconds'] // 60}m {t['remaining_seconds'] % 60}s.''', module = 'planner', type = 'planner')except ValueError:
exc = Nonedel excNoneNone = del exc)()
planner_set_alarm = (lambda assistant = None, params = None, message = register_action('planner_set_alarm', module = 'planner', description = 'Set alarm'): if not planner_enabled():
_disabled()set_alarm = set_alarmimport jarvis.planner_storeif not params.get('time'):
params.get('time')time_str = ''.strip()if not params.get('label'):
params.get('label')if not ''.strip():
''.strip()label = Noneif not time_str:
m = re.search('alarm\\s+(?:for\\s+)?(.+)', message, re.I)time_str = m.group(1).strip() if m else ''try:
a = set_alarm(time_str, label)if not a['fire_at']:
a['fire_at']ok(f'''Alarm **{a['label']}** set for {''[11:16]}.''', module = 'planner', type = 'planner')except ValueError:
exc = Nonedel excNoneNone = del exc)()
planner_today = (lambda assistant = None, params = None, message = register_action('planner_today', info = True, module = 'planner', description = "Today's planner schedule"): if not planner_enabled():
_disabled()format_planner_lines = format_planner_linesimport jarvis.planner_storeblock = format_planner_lines()if not block:
ok('Planner is clear for today.', module = 'planner', type = 'planner')None(block, module = 'planner', type = 'planner'))()
planner_add_event = (lambda assistant = None, params = None, message = register_action('planner_add_event', module = 'planner', description = 'Add calendar event'): if not planner_enabled():
_disabled()add_event = add_eventimport jarvis.planner_storeif not params.get('title'):
params.get('title')title = ''.strip()if not params.get('date'):
params.get('date')if not params.get('when'):
params.get('when')if not ''.strip():
''.strip()when = Noneif not params.get('time'):
params.get('time')if not ''.strip():
''.strip()time_str = Noneif not title:
m = re.search('(?:schedule|event|meeting)\\s+(.+)', message, re.I)title = m.group(1).strip() if m else message.strip()try:
ev = add_event(title, when = when, time_str = time_str)if not ev['start_time']:
ev['start_time']ok(f'''Scheduled **{ev['title']}** at {''[11:16]}.''', module = 'planner', type = 'planner')except ValueError:
exc = Nonedel excNoneNone = del exc)()
system_info = (lambda assistant = None, params = None, message = register_action('system_info', info = True, module = 'general', description = 'Unified status snapshot'): format_system_info_markdown = format_system_info_markdownimport jarvis.system_infook(format_system_info_markdown(assistant = assistant), module = 'general', type = 'system_info'))()
audio_stop = (lambda assistant = None, params = None, message = register_action('audio_stop', module = 'audio', description = 'Stop TTS playback'): stop_playback = stop_playbackimport jarvis.audio_devicestopped = stop_playback()if stopped:
assistant.conversation.truncate_last_assistant()assistant.branches.persist(session = assistant.session)msg = 'Playback stopped.' if stopped else 'Nothing was playing.'ok(msg, module = 'audio', type = 'audio'))()
audio_pause = (lambda assistant = None, params = None, message = register_action('audio_pause', module = 'audio', description = 'Pause or resume TTS playback'): pause_playback = pause_playbackresume_playback = resume_playbackimport jarvis.audio_deviceif not message:
messagelower = ''.lower()if 'resume' in lower or params.get('resume'):
ok_resume = resume_playback()ok('Resumed playback.' if ok_resume else 'Nothing to resume.', module = 'audio', type = 'audio')paused = pause_playback()ok('Playback paused.' if paused else 'Nothing was playing.', module = 'audio', type = 'audio'))()
curated_briefing = (lambda assistant = None, params = None, message = register_action('curated_briefing', info = True, module = 'general', description = 'AI-curated news briefing'): format_curated_markdown = format_curated_markdownimport jarvis.curated_newsuse_ai = params.get('use_ai', True) is not Falseok(format_curated_markdown(use_ai = use_ai), module = 'general', type = 'briefing'))()
