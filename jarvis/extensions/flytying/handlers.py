# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Fly-tying chat action handlers.'''
from __future__ import annotations
import re
from jarvis.flytying import bridge
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _gold_unavailable():
    return err('Fly-tying gold library missing. Set `JARVIS_FLYTYING_ROOT` to your Blackfly project (e.g. `/media/jeff/C/fly_fishing_project`) and ensure `gold_recipes.jsonl` exists.', module = 'flytying')

fly_status = (lambda _assistant = None, _params = None, _message = register_action('fly_status', info = True, module = 'flytying', extension = 'flytying', description = 'Fly-tying dataset and index status'): st = bridge.status()if not st.get('index_note'):
st.get('index_note')lines = [
f'''**Fly tying:** {'ready' if st.get('ok') else 'not ready'}''',
f'''- Root: `{st.get('root')}`''',
f'''- Gold recipes: {st.get('gold_count', 0)}''',
f'''- Search: {'keyword'}''',
f'''- Semantic index: {'yes' if st.get('index_built') else 'no'}''']if not st.get('types'):
st.get('types')types = { }if types:
summary = (lambda .0: pass# WARNING: Decompyle incomplete
)(sorted(types.items(), key = (lambda x: -x[1]))[:6]())
        lines.append(f'''- Types: {summary}''')
    if not st.get('gold_exists'):
        lines.append('- Run `blackfly_cli gold` in the Blackfly project to build the gold dataset.')
# WARNING: Decompyle incomplete
)()
fly_search = (lambda _assistant = None, params = None, message = register_action('fly_search', module = 'flytying', extension = 'flytying', description = 'Search fly-tying patterns'): if not bridge.gold_available():
_gold_unavailable()if not None.get('query'):
None.get('query')if not params.get('q'):
params.get('q')query = ''.strip()if not query:
query = re.sub('^(search|find|list)\\s+(fly|flies|patterns?|recipes?)\\s*(for|about)?\\s*', '', message, flags = re.I).strip()if not query:
query = re.sub('^(fly|flies)\\s+', '', message, flags = re.I).strip()if not params.get('fly_type'):
params.get('fly_type')if not params.get('type'):
params.get('type')if not ''.strip():
''.strip()fly_type = Noneif not params.get('limit'):
params.get('limit')limit = int(8)hits = bridge.search_recipes(query, fly_type = fly_type, limit = limit)if not hits:
if not query:
queryok(f'''No patterns found for **{'your query'}**.''', module = 'flytying')lines = [
f'''{len(hits)}):**\n''']for i, h in enumerate(hits, 1):
if not h.get('materials'):
h.get('materials')mats = ', '.join([])[:80]extra = f''' — {mats}''' if mats else ''if not h.get('type'):
h.get('type')lines.append(f'''{i}. **{h.get('name')}** ({'?'}) — {h.get('steps_count', 0)} steps{extra}''')ok('\n'.join(lines), module = 'flytying', type = 'fly_search', results = hits, open_tab = 'flytying'))()
fly_recipe = (lambda _assistant = None, params = None, message = register_action('fly_recipe', module = 'flytying', extension = 'flytying', description = 'Show a fly-tying recipe'): if not bridge.gold_available():
_gold_unavailable()if not None.get('name'):
None.get('name')if not params.get('pattern'):
params.get('pattern')name = ''.strip()if not name:
name = re.sub('^(show|get|give me|what is|how (?:do i|to) tie)\\s+(the\\s+)?(recipe|pattern|fly)?\\s*(for\\s+)?', '', message, flags = re.I).strip()if not name:
err('Which pattern? e.g. `show me the Adams recipe`', module = 'flytying')row = None.get_recipe(name)if not row:
err(f'''No recipe found for **{name}**.''', module = 'flytying')# WARNING: Decompyle incomplete
)()
fly_ask = (lambda _assistant = None, params = None, message = register_action('fly_ask', module = 'flytying', extension = 'flytying', description = 'Ask the fly-tying assistant (RAG)'): if not bridge.gold_available():
_gold_unavailable()if not None.get('question'):
None.get('question')if not params.get('query'):
params.get('query')question = ''.strip()if not question:
if not re.sub('^(ask|fly tying|fly-tying)[:\\s]+', '', message, flags = re.I).strip():
re.sub('^(ask|fly tying|fly-tying)[:\\s]+', '', message, flags = re.I).strip()question = message.strip()if not params.get('fly_type'):
params.get('fly_type')if not params.get('type'):
params.get('type')if not ''.strip():
''.strip()fly_type = Noneresult = bridge.ask_fly_tying(question, fly_type = fly_type)if not result.get('ok'):
if not result.get('message'):
result.get('message')err('Fly-tying Q&A failed', module = 'flytying')if not None.get('answer'):
None.get('answer')answer = ''if not result.get('recipes'):
result.get('recipes')sources = []if sources:
cite = (lambda .0: pass# WARNING: Decompyle incomplete
)(sources())
        answer = f'''{answer}\n\n**Sources:**\n{cite}'''
    return ok(answer, module = 'flytying', type = 'fly_ask', recipes = sources, open_tab = 'flytying')
)()
fly_seasonal = (lambda _assistant = None, params = None, _message = register_action('fly_seasonal', module = 'flytying', extension = 'flytying', description = 'Seasonal fly-tying pattern suggestions'): if not bridge.gold_available():
_gold_unavailable()if not params.get('month'):
params.get('month')if not None(0):
None(0)month = Noneif not params.get('limit'):
params.get('limit')result = bridge.seasonal_suggestions(month = month, limit = int(6))if not result.get('hatch'):
result.get('hatch')hatch = { }if not result.get('results'):
result.get('results')hits = []if not hatch.get('hatches'):
hatch.get('hatches')lines = [
f'''**Seasonal patterns** ({hatch.get('region', '?')}, month {hatch.get('month', '?')})''',
f'''Hatches: {', '.join([])}''',
'']for i, h in enumerate(hits, 1):
if not h.get('type'):
h.get('type')lines.append(f'''{i}. **{h.get('name')}** ({'?'})''')ok('\n'.join(lines), module = 'flytying', type = 'fly_seasonal', results = hits, hatch = hatch, open_tab = 'flytying'))()
fly_gold_build = (lambda _assistant = None, params = None, _message = register_action('fly_gold_build', module = 'flytying', extension = 'flytying', description = 'Rebuild gold fly-tying dataset and index'): if not bridge.available():
err('Blackfly import unavailable for gold rebuild. Set `JARVIS_FLYTYING_ROOT` and install Blackfly.', module = 'flytying')if not params.get('min_quality'):
params.get('min_quality')result = None.build_gold(min_quality = float(70), build_index = bool(params.get('build_index', True)))if not result.get('ok'):
if not result.get('message'):
result.get('message')err('Gold build failed', module = 'flytying')if not None.get('stats'):
None.get('stats')stats = { }if not result.get('index'):
result.get('index')idx = { }msg = f'''Gold dataset rebuilt: **{stats.get('gold_count', 0)}** recipes (from {stats.get('source_count', 0)} source rows).'''if idx.get('ok'):
msg += f''' Indexed **{idx.get('count', 0)}** for semantic search.'''elif idx.get('message'):
msg += f''' Index: {idx['message']}.'''# WARNING: Decompyle incomplete
)()
