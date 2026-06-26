# Source Generated with Decompyle++
# File: observation_learning_handlers.cpython-312.pyc (Python 3.12)

'''Observation learning action handlers.'''
from __future__ import annotations
from pathlib import Path
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
from jarvis.vision_media import IMAGE_EXTENSIONS

def _format_result(result = None):
    format_observations_markdown = format_observations_markdown
    import jarvis.observation_learning
    body = result.message
# WARNING: Decompyle incomplete

observe = (lambda assistant = None, params = None, message = register_action('observe', module = 'memory', extension = 'memory', description = 'Observe text and create notes'): observe_text = observe_textparse_terminal_text = parse_terminal_textimport jarvis.observation_learningif not params.get('text'):
params.get('text')if not parse_terminal_text(message):
parse_terminal_text(message)text = ''.strip()if not params.get('source_type'):
params.get('source_type')source_type = 'terminal'.strip().lower()if not params.get('title'):
params.get('title')title = source_type.strip()if not text:
err('Paste output to observe, e.g. **observe terminal:**\n```\n$ pytest -q\n...\n```', module = 'memory')result = observe_text(assistant.memory, text, source_type = source_type, title = title)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()_format_result(result))()
observe_log_action = (lambda assistant = None, params = None, message = register_action('observe_log', module = 'memory', extension = 'memory', description = 'Observe log file tail'): observe_log = observe_logimport jarvis.observation_learninglines = params.get('lines')try:
result = observe_log(assistant.memory, message = message, lines = int(lines) if lines else None)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()_format_result(result)except FileNotFoundError:
exc = Nonedel excNoneNone = del exc)()
observe_terminal_action = (lambda assistant = None, params = None, message = register_action('observe_terminal', module = 'memory', extension = 'memory', description = 'Observe terminal output'): observe_terminal = observe_terminalparse_terminal_text = parse_terminal_textimport jarvis.observation_learningif not params.get('text'):
params.get('text')if not parse_terminal_text(message):
parse_terminal_text(message)text = assistant.session.last_terminal_output.strip()if not text:
err('No terminal output. Run a command first or paste output after **observe terminal:**', module = 'memory')if not None.get('title'):
None.get('title')title = 'terminal'.strip()result = observe_terminal(assistant.memory, text, title = title)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()_format_result(result))()
observe_screenshot_action = (lambda assistant = None, params = None, message = register_action('observe_screenshot', module = 'memory', extension = 'memory', description = 'Observe screenshot/image'): observe_screenshot = observe_screenshotimport jarvis.observation_learningif not params.get('path'):
params.get('path')if not assistant.session.resolve_image(''):
assistant.session.resolve_image('')path = ''.strip()if not path:
err('Attach a screenshot or image to observe.', module = 'memory')if None(path).suffix.lower() not in IMAGE_EXTENSIONS:
err('Observation needs an image file (png, jpg, webp, …).', module = 'memory')result = observe_screenshot(assistant.memory, assistant.vision, path)if not result.ok:
err(result.message, module = 'memory')None.session.note_image(path)assistant.refresh_system_prompt()_format_result(result))()
observe_camera_action = (lambda assistant = None, params = None, message = register_action('observe_camera', module = 'memory', extension = 'memory', description = 'Capture camera and observe'): observe_camera = observe_cameraimport jarvis.observation_learningif not params.get('device'):
params.get('device')if not ''.strip():
''.strip()device = Noneresult = observe_camera(assistant.memory, assistant.vision, device = device)if not result.ok:
err(result.message, module = 'memory')if None.path:
assistant.session.note_image(result.path)assistant.refresh_system_prompt()_format_result(result))()
observe_action_log_action = (lambda assistant = None, params = None, message = register_action('observe_action_log', module = 'memory', extension = 'memory', description = 'Observe recent actions'): observe_action_log = observe_action_logimport jarvis.observation_learningif not params.get('limit'):
params.get('limit')limit = int(50)result = observe_action_log(assistant.memory, limit = limit)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()_format_result(result))()
observation_recall = (lambda assistant = None, params = None, message = register_action('observation_recall', module = 'memory', extension = 'memory', description = 'Recall observation notes'): format_observations_markdown = format_observations_markdownlist_observation_sources = list_observation_sourceslist_observations = list_observationsobservation_stats = observation_statsparse_observation_recall_query = parse_observation_recall_queryimport jarvis.observation_learningif not params.get('query'):
params.get('query')if not parse_observation_recall_query(message):
parse_observation_recall_query(message)query = ''.strip()if not params.get('source_type'):
params.get('source_type')if not ''.strip().lower():
''.strip().lower()source_type = Noneentries = list_observations(assistant.memory, query = query, source_type = source_type)stats = observation_stats()sources = list_observation_sources(limit = 12)if not entries and sources:
ok('No observations yet. Try **observe the log**, **observe this screenshot**, or **observe terminal:** with pasted output.', module = 'memory')title = f'''Observations about **{query}**''' if None else 'Observation notes'footer = f'''\n\n_{stats['total_sources']} source(s), {stats['total_notes']} note(s) in `{stats['namespace']}`._'''ok(title + '\n\n' + format_observations_markdown(entries, sources = sources) + footer, module = 'memory'))()
