# Source Generated with Decompyle++
# File: workflow_handlers.cpython-312.pyc (Python 3.12)

'''Workflow learning handlers — scan, list, run learned action sequences.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
workflow_list = (lambda assistant = None, params = None, message = register_action('workflow_list', module = 'general', description = 'List learned workflows', info = True): list_workflows = list_workflowsimport jarvis.workflow_learningif not params.get('query'):
params.get('query')query = ''.strip()items = list_workflows(query = query)if not items:
ok('No learned workflows yet. Repeat the same action sequence a few times, or say **scan workflows** to mine the action log.', module = 'general')# WARNING: Decompyle incomplete
)()
workflow_show = (lambda assistant = None, params = None, message = register_action('workflow_show', module = 'general', description = 'Show a learned workflow', info = True): format_workflow_markdown = format_workflow_markdownresolve_workflow = resolve_workflowimport jarvis.workflow_learningif not params.get('slug'):
params.get('slug')slug = ''.strip()if not slug:
m = re.search('\\bshow\\s+workflow[:\\s]+(.+)', message, re.I)if re.search('\\bshow\\s+workflow[:\\s]+(.+)', message, re.I):
slug = m.group(1).strip()wf = resolve_workflow(slug) if slug else Noneif not wf:
err('Which workflow? Example: **show workflow morning routine**', module = 'general')None(format_workflow_markdown(wf), module = 'general', slug = wf['slug']))()
workflow_scan = (lambda assistant = None, params = None, message = register_action('workflow_scan', module = 'general', description = 'Scan action log for repeated workflows'): auto_remember = auto_rememberremember_workflow = remember_workflowscan_action_log = scan_action_logimport jarvis.workflow_learningif not params.get('min_repeats'):
params.get('min_repeats')if not int(0):
int(0)min_rep = Nonefound = scan_action_log(min_repeats_count = min_rep)if not found:
if not min_rep:
min_repok(f'''No repeated action sequences found yet. Need at least {3} matching runs in the action log.''', module = 'general')remembered = Noneif auto_remember():
for wf in found:
remembered += len(remember_workflow(assistant.memory, wf))if remembered:
assistant.refresh_system_prompt()# WARNING: Decompyle incomplete
)()
workflow_learn = (lambda assistant = None, params = None, message = register_action('workflow_learn', module = 'general', description = 'Alias for workflow scan'): workflow_scan(assistant, params, message))()
workflow_run = (lambda assistant = None, params = None, message = register_action('workflow_run', module = 'general', description = 'Run a learned workflow'): autonomy_decision = autonomy_decisionrecord_outcome = record_outcomeimport jarvis.action_confidencecreate_pending = create_pendingneeds_confirmation = needs_confirmationimport jarvis.tool_permissionsparse_workflow_run_query = parse_workflow_run_queryrun_workflow = run_workflowimport jarvis.workflow_learningif not params.get('slug'):
params.get('slug')slug = ''.strip()if not params.get('confirm'):
params.get('confirm')confirm = ''.lower() in ('1', 'true', 'yes')if not slug:
(slug, parsed_confirm) = parse_workflow_run_query(message)if parsed_confirm:
confirm = Trueif not slug:
err('Which workflow? Example: **run morning routine workflow** or **run workflow NAME confirm**', module = 'general')auto = autonomy_decision('workflow_run')if confirm and auto['needs_confirm'] and needs_confirmation('workflow_run'):
confirm_id = create_pending('workflow_run', 'workflow_run', {
'slug': slug }, message)ok(f'''Confirm run workflow **{slug}**?''', module = 'general', type = 'confirm_required', confirm_id = confirm_id, tool = 'workflow_run')result = run_workflow(slug, assistant = None if not confirm else assistant, dry_run = not confirm)if not result.get('ok'):
result.get('ok')ok_flag = bool(result.get('results'))record_outcome('workflow_run', ok = ok_flag)if not result.get('results') and result.get('ok'):
err(result.get('message', 'Workflow not found.'), module = 'general')msg = None['message']if not ok_flag and auto.get('explain') and result.get('dry_run'):
msg = f'''{msg}\n\n_(Confidence {auto.get('confidence', '?')} — similar runs usually succeed.)_'''ok(msg, module = 'general', slug = result.get('slug'), dry_run = result.get('dry_run')))()
workflow_to_skill = (lambda assistant = None, params = None, message = register_action('workflow_to_skill', module = 'general', description = 'Convert workflow to skill'): parse_workflow_to_skill_query = parse_workflow_to_skill_queryconvert = workflow_to_skillimport jarvis.workflow_learningif not params.get('slug'):
params.get('slug')slug = ''.strip()if not slug:
slug = parse_workflow_to_skill_query(message)if not slug:
err('Example: **save workflow morning routine as skill**', module = 'general')result = convert(slug)if not result.get('ok'):
err(result.get('message', 'Could not convert.'), module = 'general')None(result['message'], module = 'general', skill = result.get('skill')))()
workflow_recall = (lambda assistant = None, params = None, message = register_action('workflow_recall', module = 'general', description = 'Recall learned workflows', info = True): workflow_list(assistant, params, message))()
