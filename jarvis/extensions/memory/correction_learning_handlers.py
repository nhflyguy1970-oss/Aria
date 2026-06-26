# Source Generated with Decompyle++
# File: correction_learning_handlers.cpython-312.pyc (Python 3.12)

'''Correction learning action handlers.'''
from __future__ import annotations
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _last_assistant_message(assistant = None):
    for msg in reversed(assistant.conversation.messages):
        if not msg.get('role') == 'assistant':
            continue
        if not msg.get('content'):
            msg.get('content')
        
        return reversed(assistant.conversation.messages), ''[:2000]
    return ''

correction_learn = (lambda assistant = None, params = None, message = register_action('correction_learn', module = 'memory', extension = 'memory', description = 'Learn from user correction'): apply_correction = apply_correctionparse_correction = parse_correctionimport jarvis.correction_learningif not params.get('text'):
params.get('text')raw = message.strip()intent = parse_correction(raw)if not intent:
err("What should I correct? Examples:\n• **No, that's wrong — mom's birthday is June 9**\n• **You're wrong about the port; it's 8765**\n• **correct that the repo is at /media/jeff/AI/jarvis**", module = 'memory')if not None.get('assistant_msg'):
None.get('assistant_msg')assistant_msg = _last_assistant_message(assistant).strip()if not params.get('module'):
params.get('module')if not assistant.session.last_module:
assistant.session.last_modulemodule = ''.strip()result = apply_correction(assistant.memory, intent, assistant_msg = assistant_msg, module = module)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()mirror = ''if result.mirrors:
mirror = f'''\n\n_Also: {', '.join(result.mirrors)}._'''body = f'''**Correct:** {result.correction}{mirror}'''if result.wrong_claim:
body = f'''**Wrong:** {result.wrong_claim}\n\n**Correct:** {result.correction}{mirror}'''ok(f'''Got it — I\'ll remember this correction ({result.kind}).\n\n{body}''', module = 'memory', correction = result.correction, kind = result.kind))()
correction_recall = (lambda assistant = None, params = None, message = register_action('correction_recall', module = 'memory', extension = 'memory', description = 'Recall user corrections'): correction_stats = correction_statsformat_corrections_markdown = format_corrections_markdownlist_corrections = list_correctionsparse_correction_recall_query = parse_correction_recall_queryimport jarvis.correction_learningif not params.get('query'):
params.get('query')if not parse_correction_recall_query(message):
parse_correction_recall_query(message)query = ''.strip()entries = list_corrections(assistant.memory, query = query)stats = correction_stats()if not entries:
ok("No corrections yet. When I get something wrong, say **no, that's wrong — …** or **correct that …**", module = 'memory')title = f'''Corrections about **{query}**''' if None else 'Your corrections'footer = f'''\n\n_{stats['total']} correction(s) in `{stats['namespace']}`._'''ok(title + '\n\n' + format_corrections_markdown(entries) + footer, module = 'memory'))()
