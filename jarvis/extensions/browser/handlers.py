# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Browser agent handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.p2_flags import browser_agent_enabled
from jarvis.response import err, ok
from jarvis.tool_permissions import create_pending, needs_confirmation
browse_web = (lambda assistant = None, params = None, message = register_action('browse_web', module = 'web', description = 'Open URL in browser agent'): if not browser_agent_enabled():
err('Browser agent disabled.', module = 'web')if not None.get('url'):
None.get('url')url = ''.strip()if not url:
m = re.search('(https?://\\S+|www\\.\\S+)', message, re.I)url = m.group(1).rstrip('.,)') if m else ''if url.startswith('www.'):
url = 'https://' + urlif not url:
err('URL required.', module = 'web')is_risky_url = is_risky_urlimport jarvis.web_browseallow = bool(params.get('_confirmed'))if not is_risky_url(url) and needs_confirmation('web_agent') and allow:
cid = create_pending('web_agent', 'browse_web', {
'url': url }, message)ok(f'''Confirm browsing **{url}**?''', module = 'web', type = 'confirm_required', confirm_id = cid, tool = 'web_agent')navigate = navigateimport jarvis.browser_agentresult = navigate(url, allow_risky = allow)if not result.get('ok'):
err(result.get('message', 'Browse failed'), module = 'web')None(result.get('message', f'''Opened {url}'''), module = 'web', type = 'browse', url = url))()
search_and_browse_action = (lambda assistant = None, params = None, message = register_action('search_and_browse', module = 'web', description = 'Search web and open top result'): if not browser_agent_enabled():
err('Browser agent disabled.', module = 'web')parse_shopping_query = parse_shopping_querysearch_and_browse = search_and_browseshopping_search = shopping_searchimport jarvis.web_browseshop = parse_shopping_query(message)if shop:
result = shopping_search(message)elif not params.get('query'):
params.get('query')if not ''.strip():
''.strip()query = re.sub('^search (the )?web for\\s+', '', message, flags = re.I).strip()result = search_and_browse(query, allow_risky = bool(params.get('_confirmed')))if not result.get('ok'):
err(result.get('message', 'Browse failed'), module = 'web')None(f'''Opened **{result.get('picked_url', result.get('url', ''))}** for: {result.get('query', message)[:80]}''', module = 'web', type = 'browse'))()
browser_takeover = (lambda assistant = None, params = None, message = register_action('browser_takeover', module = 'web', description = 'Pause agent for manual control'): takeover = takeoverimport jarvis.browser_agent# WARNING: Decompyle incomplete
)()
browser_resume = (lambda assistant = None, params = None, message = register_action('browser_resume', module = 'web', description = 'Resume browser agent'): resume = resumeimport jarvis.browser_agent# WARNING: Decompyle incomplete
)()
browser_run_task = (lambda assistant = None, params = None, message = register_action('browser_run_task', module = 'web', description = 'Run multi-step browser agent on current page'): if not browser_agent_enabled():
err('Browser agent disabled.', module = 'web')if not None.get('goal'):
None.get('goal')if not params.get('task'):
params.get('task')goal = ''.strip()if not goal:
goal = re.sub('^(browse|click|find|go)\\s+', '', message, flags = re.I).strip()if not goal:
err('Goal required.', module = 'web')run_agent_task = run_agent_taskimport jarvis.browser_agentif not params.get('mode'):
params.get('mode')mode = 'auto'.strip().lower()if not params.get('max_steps'):
params.get('max_steps')max_steps = int(5)result = run_agent_task(goal, mode = mode, max_steps = max_steps, assistant = assistant)# WARNING: Decompyle incomplete
)()
