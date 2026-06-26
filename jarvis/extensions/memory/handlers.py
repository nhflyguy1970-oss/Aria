# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Memory action handlers.'''
from __future__ import annotations
import re
from pathlib import Path
from jarvis import llm
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _project_namespace(assistant = None):
    load_auto_namespace = load_auto_namespace
    load_memory_namespace = load_memory_namespace
    import jarvis.config
    resolve_project_namespace = resolve_project_namespace
    import jarvis.memory_context
    if load_auto_namespace():
        return resolve_project_namespace()
    ns = None.session.memory_namespace
    if ns and ns != 'default':
        return ns
    return load_memory_namespace()

teach = (lambda assistant = None, params = None, message = register_action('teach', module = 'memory', extension = 'memory', description = 'Explicitly teach ARIA a lesson'): load_memory_namespace = load_memory_namespaceimport jarvis.configapply_explicit_teaching = apply_explicit_teachingparse_teach_message = parse_teach_messageimport jarvis.explicit_teachingif not params.get('text'):
params.get('text')raw = message.strip()intent = parse_teach_message(raw)if not intent:
err('What should I learn? Examples:\n• **teach ARIA that** I prefer bullet answers\n• **teach rule:** never suggest cloud APIs\n• **teach procedure:** to deploy, run ./scripts/launch-jarvis.sh\n• **teach relationship:** Jeff works on Jarvis')if not None.get('namespace'):
None.get('namespace')ns = load_memory_namespace()if ns == 'default':
ns = Nonetry:
result = apply_explicit_teaching(assistant.memory, intent, namespace = ns)assistant.session.note_module('memory')assistant.refresh_system_prompt()mirror = ''if result.mirrors:
mirror = f'''\n\n_Also stored as: {', '.join(result.mirrors)}._'''ok(f'''Taught **[{result.kind}]** in `{result.namespace}`:\n\n{result.content}{mirror}''', module = 'memory', taught = result.content, kind = result.kind)except ValueError:
e = Nonedel eNoneNone = del e)()
teach_recall = (lambda assistant = None, params = None, message = register_action('teach_recall', module = 'memory', extension = 'memory', description = 'Recall explicit teachings'): format_teachings_markdown = format_teachings_markdownlist_teachings = list_teachingsparse_teach_recall_query = parse_teach_recall_queryteaching_stats = teaching_statsimport jarvis.explicit_teachingif not params.get('query'):
params.get('query')if not parse_teach_recall_query(message):
parse_teach_recall_query(message)query = ''.strip()if not params.get('kind'):
params.get('kind')if not ''.strip().lower():
''.strip().lower()kind = Noneentries = list_teachings(assistant.memory, query = query, kind = kind)stats = teaching_stats(assistant.memory)if not entries:
ok('No explicit teachings yet. Say **teach ARIA that …** or **teach rule: …**', module = 'memory')title = f'''Teachings about **{query}**''' if None else 'Explicit teachings'footer = None + f'''{(lambda .0: pass# WARNING: Decompyle incomplete
)(stats.get('by_kind', { }).items()())}''' if stats.get('by_kind') else '' + '_'
    return ok(f'''{title}:\n\n{format_teachings_markdown(entries)}{footer}''', module = 'memory')
)()
remember = (lambda assistant = None, params = None, message = register_action('remember', module = 'memory', extension = 'memory', description = 'Store a fact in memory'): load_memory_namespace = load_memory_namespaceimport jarvis.configMemoryStore = MemoryStoreimport jarvis.modules.memoryparse_strategy_remember = parse_strategy_rememberrecord_strategy = record_strategyimport jarvis.trust_memoryparse_experience_remember = parse_experience_rememberrecord_experience = record_experienceimport jarvis.experience_memoryRELATIONSHIP_NAMESPACE = RELATIONSHIP_NAMESPACEformat_triples_markdown = format_triples_markdownparse_relationship_link = parse_relationship_linkrecord_links = record_linksimport jarvis.relationship_memoryif not params.get('text'):
params.get('text')raw = messagelinks = parse_relationship_link(raw)if links:
stored = record_links(links, namespace = RELATIONSHIP_NAMESPACE)assistant.session.note_module('memory')assistant.refresh_system_prompt()ok(f'''Linked **{len(stored)}** relationship(s):\n\n{format_triples_markdown(stored)}''', module = 'memory')experience = parse_experience_remember(raw)if experience:
(outcome, detail) = experienceif not assistant.session.memory_namespace:
assistant.session.memory_namespacenamespace = load_memory_namespace()entry = record_experience(assistant.memory, outcome = outcome, detail = detail, module = 'user')if not entry:
ok('That experience is already stored.', module = 'memory')None.session.note_module('memory')assistant.refresh_system_prompt()ok(f'''Stored as **{outcome}** experience:\n\n{entry['content']}''', module = 'memory', remembered = entry['content'])strategy = parse_strategy_remember(raw)if strategy:
if not assistant.session.memory_namespace:
assistant.session.memory_namespacenamespace = load_memory_namespace()entry = record_strategy(assistant.memory, strategy, namespace = namespace)assistant.session.note_module('memory')assistant.refresh_system_prompt()ok(f'''Got it — stored as **strategy** rule in `{namespace}`.\n\n{entry['content']}''', module = 'memory', remembered = entry['content'])(content, entry_type, parsed_ns) = None.parse_remember(raw)if not params.get('namespace'):
params.get('namespace')if not parsed_ns:
parsed_nsif not assistant.session.memory_namespace:
assistant.session.memory_namespacenamespace = load_memory_namespace()if not content:
err('What should I remember?')facts = None.split_remember_facts(content)stored = []try:
for fact in facts:
if assistant.memory.similar_exists(fact):
continueassistant.memory.add(entry_type, fact, namespace = namespace)stored.append(fact)if not stored:
ok('Those facts are already stored.', module = 'memory')None.session.note_module('memory')assistant.refresh_system_prompt()ok(f'''Stored **{len(stored)}** {entry_type}{'s' if len(stored) != 1 else ''} in `{namespace}`:\n\n{body}''', module = 'memory', remembered = stored[0] if len(stored) == 1 else body, remembered_count = len(stored))except ValueError:
e = Nonedel eNoneNone = del e)()
recall = (lambda assistant = None, params = None, message = register_action('recall', module = 'memory', extension = 'memory', description = 'List stored memories'): filter_entry_list = filter_entry_listimport jarvis.trust_memoryprofile = assistant.memory.list_entries(namespace = 'profile')ns = assistant.session.memory_namespaceother = assistant.memory.list_entries(namespace = ns if ns and ns != 'default' else None)# WARNING: Decompyle incomplete
)()
memory_about_user = (lambda assistant = None, params = None, message = register_action('memory_about_user', module = 'memory', extension = 'memory', description = 'Answer from profile memory'): import randomfilter_entry_list = filter_entry_listimport jarvis.trust_memoryif not params.get('question'):
params.get('question')lower = message.lower()profile = assistant.memory.list_entries(namespace = 'profile')if not profile:
hits = filter_entry_list(assistant.memory.search(message, limit = 5))if hits:
lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(hits())
            return ok(f'''From memory:\n\n{lines}''', module = 'memory')
        return None("I don't have a profile yet. Complete the **About you** questionnaire when it appears, or say **Remember that I enjoy …**", module = 'memory')
    _profile_name_line = _profile_name_line
    import jarvis.memory_context
    interests = (lambda .0: pass# WARNING: Decompyle incomplete
)(profile(), None)
    name_line = _profile_name_line(profile)
    canonical_name = ''
    if name_line:
        m = re.match("User's name is (.+?)\\.?$", name_line, re.I)
        if m:
            canonical_name = m.group(1).strip()
# WARNING: Decompyle incomplete
)()
experience_recall = (lambda assistant = None, params = None, message = register_action('experience_recall', module = 'memory', extension = 'memory', description = 'Recall past successes and failures'): parse_experience_recall_query = parse_experience_recall_queryrecall_experiences = recall_experiencesimport jarvis.experience_memoryif not params.get('query'):
params.get('query')if not parse_experience_recall_query(message):
parse_experience_recall_query(message)query = message.strip()query = re.sub('^(?:please\\s+)?(?:what worked|what failed|past failures|past successes|experiences?)\\s*(?:for|with|on)?\\s*', '', query, flags = re.I).strip()results = recall_experiences(assistant.memory, query, limit = 10)if not results:
ok('No matching experiences yet. Say **remember that worked: …** or **remember that failed: …** after you try something — coding fixes are logged automatically.', module = 'memory')lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(results())
    title = f'''Experiences for **{query}**''' if query else 'Recent experiences'
    return ok(f'''{title}:\n\n{lines}''', module = 'memory')
)()
relationship_recall = (lambda assistant = None, params = None, message = register_action('relationship_recall', module = 'memory', extension = 'memory', description = 'Recall entity connections'): format_triples_markdown = format_triples_markdownparse_relationship_recall_query = parse_relationship_recall_queryrecall_relationships = recall_relationshipsimport jarvis.relationship_memoryif not params.get('query'):
params.get('query')if not parse_relationship_recall_query(message):
parse_relationship_recall_query(message)query = message.strip()query = re.sub('^(?:please\\s+)?(?:show\\s+)?(?:connections?|relationships?|graph)\\s*(?:for|of|about)?\\s*', '', query, flags = re.I).strip()result = recall_relationships(query)if not result.get('triples'):
result.get('triples')triples = []if not triples:
ok('No relationship graph entries yet. Say **link User → WORKS_ON → Jarvis** or **remember User works on Jarvis** — facts with prefers/uses/works on sync automatically.', module = 'memory')title = f'''Connections for **{query}**''' if None else 'Relationship graph'backend = result.get('backend', 'sqlite')if not result.get('stats'):
result.get('stats')stats = { }footer = f'''\n\n_Graph: {backend} · {stats.get('nodes', 0)} nodes · {stats.get('edges', 0)} edges_'''ok(f'''{title}:\n\n{format_triples_markdown(triples)}{footer}''', module = 'memory'))()
memory_search = (lambda assistant = None, params = None, message = register_action('memory_search', module = 'memory', extension = 'memory', description = 'Search memories'): filter_entry_list = filter_entry_listimport jarvis.trust_memoryif not params.get('query'):
params.get('query')query = messagens = assistant.session.memory_namespaceresults = filter_entry_list(assistant.memory.search(query, namespace = ns if ns and ns != 'default' else None))if results and ns and ns != 'default':
results = filter_entry_list(assistant.memory.search(query))if not results:
ok('No matching memories found.', module = 'memory')lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(results())
    return ok(f'''Found these memories:\n\n{lines}''', module = 'memory')
)()
memory_forget = (lambda assistant = None, params = None, message = register_action('memory_forget', module = 'memory', extension = 'memory', description = 'Delete matching memories'): if not params.get('query'):
params.get('query')query = messagequery = re.sub('^(please\\s+)?(forget|delete|remove)\\s+(that|about|the memory)?\\s*', '', query, flags = re.I).strip()if not query:
err('What should I forget? Give me a phrase to search for.')results = None.memory.search(query, limit = 5)if not results:
ok('No matching memories to delete.', module = 'memory')removed_lines = Nonefor e in results[:3]:
if not assistant.memory.delete_id(e['id']):
continueremoved_lines.append(e['content'][:120])assistant.refresh_system_prompt()if not removed_lines:
ok('No matching memories to delete.', module = 'memory')lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(removed_lines())
    return ok(f'''Removed **{len(removed_lines)}** memor{'y' if len(removed_lines) == 1 else 'ies'}:\n\n{lines}''', module = 'memory')
)()
memory_correct = (lambda assistant = None, params = None, message = register_action('memory_correct', module = 'memory', extension = 'memory', description = 'Correct a stored fact'): CorrectionIntent = CorrectionIntentapply_correction = apply_correctioninfer_correction_kind = infer_correction_kindparse_correction = parse_correctionimport jarvis.correction_learningif not params.get('new_fact'):
params.get('new_fact')new_fact = ''.strip()if not params.get('search_hint'):
params.get('search_hint')search_hint = ''.strip()intent = parse_correction(message) if not new_fact else Noneif intent:
if not search_hint:
search_hintsearch_hint = intent.wrong_hintif not new_fact:
new_factnew_fact = intent.correctionif not new_fact:
err("What should I correct? Try: `correct that mom's birthday is June 9`")if not None:
intent = CorrectionIntent(correction = new_fact, wrong_hint = search_hint, kind = infer_correction_kind(new_fact), raw = message)result = apply_correction(assistant.memory, intent, assistant_msg = _last_assistant_message(assistant), module = assistant.session.last_module)if not result.ok:
err(result.message, module = 'memory')None.refresh_system_prompt()msg = f'''Updated memory — stored:\n\n**{result.correction}**'''if result.wrong_claim:
msg = f'''**Wrong:** {result.wrong_claim}\n\n**Correct:** {result.correction}'''if result.removed:
msg = f'''Replaced **{result.removed}** old entr{'y' if result.removed == 1 else 'ies'}. ''' + msgif result.mirrors:
msg += f'''\n\n_Also: {', '.join(result.mirrors)}._'''ok(msg, module = 'memory', remembered = result.correction, strategy_created = 'strategy' in str(result.mirrors)))()

def _last_assistant_message(assistant = None):
    for msg in reversed(assistant.conversation.messages):
        if not msg.get('role') == 'assistant':
            continue
        if not msg.get('content'):
            msg.get('content')
        
        return reversed(assistant.conversation.messages), ''[:2000]
    return ''

memory_prune = (lambda assistant = None, params = None, message = register_action('memory_prune', module = 'memory', extension = 'memory', description = 'Prune stale auto memories'): removed = assistant.memory.prune()ok(f'''Pruned **{removed}** stale auto-extracted memories.''', module = 'memory'))()
memory_summarize = (lambda assistant = None, params = None, message = register_action('memory_summarize', module = 'memory', extension = 'memory', description = 'Summarize chat into memory'): load_memory_namespace = load_memory_namespaceimport jarvis.config# WARNING: Decompyle incomplete
)()
memory_namespace = (lambda assistant = None, params = None, message = register_action('memory_namespace', module = 'memory', extension = 'memory', description = 'Set active memory namespace'): save_memory_namespace = save_memory_namespaceimport jarvis.configif not params.get('namespace'):
params.get('namespace')ns = ''if not ns:
m = re.search('\\b(?:namespace|project)\\s+[`\'\\"]?(\\w[\\w-]*)[`\'\\"]?', message, re.I)ns = m.group(1) if m else ''if not ns:
err('Which namespace? Example: `set memory namespace work`')save_memory_namespace(ns)assistant.session.note_memory_namespace(ns)assistant.refresh_system_prompt()ok(f'''Memory namespace set to **{ns}**. New memories go there until changed.''', module = 'memory'))()
project_checkpoint = (lambda assistant = None, params = None, message = register_action('project_checkpoint', module = 'memory', extension = 'memory', description = 'Save project checkpoint'): PROJECT_ROOT = PROJECT_ROOTimport jarvis.configif not params.get('namespace'):
params.get('namespace')ns = _project_namespace(assistant)# WARNING: Decompyle incomplete
)()
project_resume = (lambda assistant = None, params = None, message = register_action('project_resume', module = 'memory', extension = 'memory', description = 'Resume from checkpoint'): if not params.get('namespace'):
params.get('namespace')ns = _project_namespace(assistant)if not assistant.memory.latest_checkpoint(ns):
assistant.memory.latest_checkpoint(ns)cp = assistant.memory.latest_checkpoint()if not cp:
ok('No project checkpoint saved yet. Say **save where I left off** before shutting down.', module = 'memory')extra = Noneif assistant.session.last_file:
extra = f'''\n\nSession still has **last file**: `{assistant.session.last_file}`'''elif cp.get('namespace'):
extra = f'''\n\nCheckpoint namespace: `{cp.get('namespace')}`'''ok(f'''Here\'s where you left off:\n\n{cp['content']}{extra}''', module = 'memory'))()
cheatsheet_list = (lambda assistant = None, params = None, message = register_action('cheatsheet_list', module = 'memory', extension = 'memory', description = 'List memory cheatsheets'): CHEATSHEET_NAMESPACE = CHEATSHEET_NAMESPACElist_cheatsheets = list_cheatsheetsseed_cheatsheets = seed_cheatsheetsimport jarvis.cheatsheetsif not list_cheatsheets(assistant.memory):
seed_cheatsheets(assistant.memory)items = list_cheatsheets(assistant.memory)lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(items())
    return ok(f'''Cheatsheets in memory (`{CHEATSHEET_NAMESPACE}` namespace):\n\n{lines}\n\nSay **memory cheatsheet** or **cheatsheet for coding**. Edit in Memory tab → Cheatsheets.''', module = 'memory')
)()
cheatsheet_show = (lambda assistant = None, params = None, message = register_action('cheatsheet_show', module = 'memory', extension = 'memory', description = 'Show a cheatsheet'): default_keys = default_keysfind_by_key = find_by_keynormalize_key = normalize_keyresolve_key_from_message = resolve_key_from_messageseed_cheatsheets = seed_cheatsheetsimport jarvis.cheatsheetsif not normalize_key(params.get('key', '')):
normalize_key(params.get('key', ''))key = resolve_key_from_message(message)if not key:
cheatsheet_list(assistant, params, message)if not find_by_key(assistant.memory, key):
seed_cheatsheets(assistant.memory, keys = [
key])entry = find_by_key(assistant.memory, key)if not entry:
err(f'''Unknown cheatsheet `{key}`. Available: {', '.join(default_keys())}''')None(entry['content'], module = 'memory'))()
cheatsheet_reset = (lambda assistant = None, params = None, message = register_action('cheatsheet_reset', module = 'memory', extension = 'memory', description = 'Reset cheatsheet to default'): normalize_key = normalize_keyreset_cheatsheet = reset_cheatsheetresolve_key_from_message = resolve_key_from_messageimport jarvis.cheatsheetsif not normalize_key(params.get('key', '')):
normalize_key(params.get('key', ''))key = resolve_key_from_message(message)if not key:
err('Which cheatsheet? Example: **reset memory cheatsheet**')updated = reset_cheatsheet(assistant.memory, key)if not updated:
err(f'''No default cheatsheet for `{key}`.''')None(f'''Restored **{key}** cheatsheet to default.''', module = 'memory'))()
remember_image = (lambda assistant = None, params = None, message = register_action('remember_image', module = 'memory', extension = 'memory', description = 'Remember image content in memory'): path = assistant.session.resolve_image(params.get('path', ''))if not path:
err('Attach an image to remember.')if not None.get('hint'):
None.get('hint')if not message:
messagehint = ''.strip()ocr = assistant.vision.ocr(path)if ocr.startswith('ERROR:'):
summary = assistant.vision.analyze('Summarize this image in one paragraph.', path)if summary.startswith('ERROR:'):
err(summary)content = Noneelse:
content = ocrlabel = re.sub("^(please\\s+)?(remember|don't forget|note that|keep in mind)\\s*(that\\s+)?", '', hint, flags = re.I).strip()fact = f'''{label}: {content}''' if label else f'''From image {Path(path).name}: {content}'''load_memory_namespace = load_memory_namespaceimport jarvis.configif not assistant.session.memory_namespace:
assistant.session.memory_namespacenamespace = load_memory_namespace()assistant.memory.add('fact', fact[:4000], namespace = namespace)ok(f'''Stored image content in memory.\n\n{fact[:500]}…''', module = 'memory', remembered = fact[:200]))()
