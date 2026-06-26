# Source Generated with Decompyle++
# File: self_upgrade_handlers.cpython-312.pyc (Python 3.12)

'''Self-upgrade pipeline handlers — branch, test, merge on approval.'''
from __future__ import annotations
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
self_upgrade_run = (lambda assistant = None, params = None, message = register_action('self_upgrade_run', module = 'coding', description = 'Semi-auto self-upgrade: branch, change, test, report', queue = 'background'): parse_self_upgrade_task = parse_self_upgrade_taskrun_pipeline = run_pipelineimport jarvis.self_upgradeif not params.get('task'):
params.get('task')if not parse_self_upgrade_task(message):
parse_self_upgrade_task(message)task = ''.strip()if not params.get('max_steps'):
params.get('max_steps')max_steps = int(4)result = run_pipeline(assistant, task, max_steps = max_steps)# WARNING: Decompyle incomplete
)()
self_upgrade_merge = (lambda assistant = None, params = None, message = register_action('self_upgrade_merge', module = 'coding', description = 'Merge approved self-upgrade branch'): merge_force = merge_forcemerge_pipeline = merge_pipelineimport jarvis.self_upgradeif not params.get('force'):
params.get('force')if not ''.lower() in ('1', 'true', 'yes'):
''.lower() in ('1', 'true', 'yes')force = merge_force(message)result = merge_pipeline(assistant, force = force)# WARNING: Decompyle incomplete
)()
self_upgrade_abort = (lambda assistant = None, params = None, message = register_action('self_upgrade_abort', module = 'coding', description = 'Abort self-upgrade branch'): abort_pipeline = abort_pipelineimport jarvis.self_upgraderesult = abort_pipeline(assistant)if result.get('ok'):
ok(result['message'], module = 'coding')None(result.get('message', 'Abort failed.'), module = 'coding'))()
upgrade_apply_handler = (lambda assistant = None, params = None, message = register_action('upgrade_apply', module = 'coding', description = 'Apply verified self-upgrade proposal'): assistant._upgrade_apply(params, message))()
apply_proposal_handler = (lambda assistant = None, params = None, message = register_action('apply_proposal', module = 'coding', description = 'Apply pending code proposal'): assistant._apply_proposal_nl(params, message))()
