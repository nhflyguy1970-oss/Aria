# Source Generated with Decompyle++
# File: skill_handlers.cpython-312.pyc (Python 3.12)

'''Skill database handlers — save, list, show, and run reusable procedures.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok
skill_list = (lambda assistant = None, params = None, message = register_action('skill_list', module = 'general', description = 'List saved procedure skills', info = True): ensure_default_skills = ensure_default_skillslist_skills = list_skillsimport jarvis.skill_databaseensure_default_skills()if not params.get('query'):
params.get('query')query = ''.strip()items = list_skills(query = query)if not items:
ok('No skills yet. Say **save skill install docker:** with numbered steps, or bundled defaults load on first list.', module = 'general')# WARNING: Decompyle incomplete
)()
skill_show = (lambda assistant = None, params = None, message = register_action('skill_show', module = 'general', description = 'Show a procedure skill', info = True): format_skill_markdown = format_skill_markdownresolve_skill = resolve_skillimport jarvis.skill_databaseif not params.get('slug'):
params.get('slug')if not params.get('skill'):
params.get('skill')slug = ''.strip()if not slug:
m = re.search('\\bshow\\s+skill[:\\s]+(.+)', message, re.I)if re.search('\\bshow\\s+skill[:\\s]+(.+)', message, re.I):
slug = m.group(1).strip()else:
m = re.search('\\bskill\\s+show[:\\s]+(.+)', message, re.I)if re.search('\\bskill\\s+show[:\\s]+(.+)', message, re.I):
slug = m.group(1).strip()skill = resolve_skill(slug) if slug else Noneif not skill:
err('Which skill? Example: **show skill install docker**', module = 'general')None(format_skill_markdown(skill), module = 'general', slug = skill['slug']))()
skill_save = (lambda assistant = None, params = None, message = register_action('skill_save', module = 'general', description = 'Save a reusable procedure skill'): parse_skill_save_message = parse_skill_save_messagesave_skill = save_skillimport jarvis.skill_databaseif not params.get('name'):
params.get('name')name = ''.strip()if not params.get('description'):
params.get('description')description = ''.strip()steps = params.get('steps')if not params.get('tags'):
params.get('tags')tags = []if not params.get('slug'):
params.get('slug')slug = ''.strip()if not name:
parsed = parse_skill_save_message(message)if parsed:
if not parsed.get('name'):
parsed.get('name')name = ''if not description:
descriptionif not parsed.get('description'):
parsed.get('description')description = ''if not steps:
steps = parsed.get('steps')if not name:
err('Define a skill like:\n**save skill install docker:**\n1. sudo apt-get update\n2. sudo apt-get install -y docker.io', module = 'general')# WARNING: Decompyle incomplete
)()
skill_run = (lambda assistant = None, params = None, message = register_action('skill_run', module = 'general', description = 'Run a saved procedure skill'): parse_skill_run_query = parse_skill_run_queryrun_skill = run_skillimport jarvis.skill_databaseif not params.get('slug'):
params.get('slug')if not params.get('skill'):
params.get('skill')slug = ''.strip()if not params.get('confirm'):
params.get('confirm')if not params.get('exec'):
params.get('exec')confirm = ''.lower() in ('1', 'true', 'yes')dry_run = params.get('dry_run')# WARNING: Decompyle incomplete
)()
skill_delete = (lambda assistant = None, params = None, message = register_action('skill_delete', module = 'general', description = 'Delete a saved skill'): delete_skill = delete_skillresolve_skill = resolve_skillslugify = slugifyimport jarvis.skill_databaseif not params.get('slug'):
params.get('slug')slug = ''.strip()if not slug:
m = re.search('\\bdelete\\s+skill[:\\s]+(.+)', message, re.I)if re.search('\\bdelete\\s+skill[:\\s]+(.+)', message, re.I):
slug = m.group(1).strip()skill = resolve_skill(slug) if slug else Noneif not skill:
err('Skill not found.', module = 'general')delete_skill(skill['slug'])ok(f'''Deleted skill **{skill['name']}** (`{skill['slug']}`).''', module = 'general'))()
