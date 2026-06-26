# Source Generated with Decompyle++
# File: test_knowledge_research_daily.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Nightly knowledge research tests.'''
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.knowledge_research_daily import RESEARCH_DIR, _all_categories, _categories_for_run, _intel_categories, append_research_digest, build_daily_digest, get_category, research_category, run_nightly_research
research_env = (lambda data_dir, monkeypatch: knowledge = data_dir / 'knowledge'research = knowledge / 'research'research.mkdir(parents = True, exist_ok = True)monkeypatch.setattr('jarvis.knowledge.KNOWLEDGE_DIR', knowledge)monkeypatch.setattr('jarvis.knowledge_research_daily.KNOWLEDGE_DIR', knowledge)monkeypatch.setattr('jarvis.knowledge_research_daily.RESEARCH_DIR', research)monkeypatch.setattr('jarvis.knowledge_research_daily.STATE_FILE', research / '_state.json')monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_DAILY', '1')monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_REMEMBER', '0')research)()

def test_get_category():
    cat = get_category('ai_news')
    @py_assert2 = None
    @py_assert1 = cat is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (cat, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(cat) if 'cat' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cat) else 'cat',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = cat['slug']
    @py_assert3 = 'ai-news'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = cat['kind']
    @py_assert3 = 'stack'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = get_category('comfyui')['slug']
    @py_assert3 = 'comfyui-image'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = get_category('security')['slug']
    @py_assert3 = 'security-selfhost'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_get_intel_category():
    cat = get_category('science_discoveries')
    @py_assert2 = None
    @py_assert1 = cat is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (cat, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(cat) if 'cat' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cat) else 'cat',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = cat['slug']
    @py_assert3 = 'science-discoveries'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = cat['kind']
    @py_assert3 = 'intel'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = get_category('world_briefing')['kind']
    @py_assert3 = 'intel'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_research_category_count():
    list_research_categories = list_research_categories
    import jarvis.knowledge_research_daily
    cats = list_research_categories()
    @py_assert2 = len(cats)
    @py_assert5 = 16
    @py_assert4 = @py_assert2 >= @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('>=',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} >= %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(cats) if 'cats' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cats) else 'cats',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
# WARNING: Decompyle incomplete


def test_append_research_digest(research_env):
    saved = append_research_digest('ai-news', 'AI news', '2026-06-17', '## 2026-06-17\n\n### Summary\n\nTest digest.\n', [
        {
            'title': 'T',
            'url': 'http://x' }])
    path = research_env / 'ai-news.md'
    @py_assert1 = path.is_file
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(path) if 'path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(path) else 'path',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert0 = 'Test digest'
    @py_assert4 = path.read_text
    @py_assert6 = 'utf-8'
    @py_assert8 = @py_assert4(encoding = @py_assert6)
    @py_assert2 = @py_assert0 in @py_assert8
    if not @py_assert2:
        @py_format10 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py9)s\n{%(py9)s = %(py5)s\n{%(py5)s = %(py3)s.read_text\n}(encoding=%(py7)s)\n}',), (@py_assert0, @py_assert8)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(path) if 'path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(path) else 'path',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert0 = saved['slug']
    @py_assert3 = 'ai-news'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_list_research_briefs_kind(research_env):
    list_research_briefs = list_research_briefs
    import jarvis.knowledge_research_daily
    append_research_digest('science-discoveries', 'Science & discoveries', '2026-06-17', '## 2026-06-17\n\n### Summary\n\nScience.\n', [])
    append_research_digest('ai-news', 'AI news', '2026-06-17', '## 2026-06-17\n\n### Summary\n\nAI.\n', [])
# WARNING: Decompyle incomplete


def test_build_daily_digest_mocked(monkeypatch):
    monkeypatch.setattr('jarvis.llm.ask', (lambda : '### Summary\n\nOllama 0.6 released.\n\n### Key updates\n- New models\n'))
    body = build_daily_digest('Ollama updates', [
        {
            'title': 'Release',
            'url': 'http://x',
            'snippet': 'Ollama 0.6' }], day = '2026-06-17', local_context = 'Installed Ollama: 0.5.0')
    @py_assert0 = '2026-06-17'
    @py_assert2 = @py_assert0 in body
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, body)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(body) if 'body' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(body) else 'body' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Ollama'
    @py_assert2 = @py_assert0 in body
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, body)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(body) if 'body' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(body) else 'body' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_build_daily_digest_intel_kind(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_research_category_mocked(research_env, monkeypatch):
    monkeypatch.setattr('jarvis.knowledge_research_daily._collect_results', (lambda queries: [
{
'title': 'AI',
'url': 'http://a',
'snippet': 'news' }]))
    monkeypatch.setattr('jarvis.knowledge_research_daily.build_daily_digest', (lambda : '## 2026-06-17\n\n### Summary\n\nAI news today.\n'))
    result = research_category('ai_news', day = '2026-06-17', force = True)
    @py_assert0 = result['ok']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    @py_assert1 = 'ai-news.md'
    @py_assert3 = research_env / @py_assert1
    @py_assert4 = @py_assert3.is_file
    @py_assert6 = @py_assert4()
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = (%(py0)s / %(py2)s).is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(research_env) if 'research_env' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(research_env) else 'research_env',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert6 = None
    state = json.loads((research_env / '_state.json').read_text(encoding = 'utf-8'))
    @py_assert1 = state.get
    @py_assert3 = 'last_run_day'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = '2026-06-17'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(state) if 'state' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(state) else 'state',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert0 = state['days']['2026-06-17']['ai-news']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_research_category_sets_last_run_day(research_env, monkeypatch):
    monkeypatch.setattr('jarvis.knowledge_research_daily._collect_results', (lambda queries: [
{
'title': 'AI',
'url': 'http://a',
'snippet': 'news' }]))
    monkeypatch.setattr('jarvis.knowledge_research_daily.build_daily_digest', (lambda : '## 2026-06-18\n\n### Summary\n\nSingle category.\n'))
    research_category('ollama', day = '2026-06-18', force = True)
    state = json.loads((research_env / '_state.json').read_text(encoding = 'utf-8'))
    @py_assert0 = state['last_run_day']
    @py_assert3 = '2026-06-18'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = 'ollama-updates'
    @py_assert3 = state['days']['2026-06-18']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = state['days']['2026-06-18']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'completed'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = True
    @py_assert8 = @py_assert6 is not @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('is not',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} is not %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None


def test_run_nightly_research_all_categories(research_env, monkeypatch):
    monkeypatch.setattr('jarvis.knowledge_research_daily._collect_results', (lambda queries: [
{
'title': 'X',
'url': 'http://x',
'snippet': 'fact' }]))
    monkeypatch.setattr('jarvis.knowledge_research_daily.build_daily_digest', (lambda : '## 2026-06-17\n\n### Summary\n\nUpdate.\n'))
    monkeypatch.setattr('jarvis.flytying.nightly.run_nightly_flytying_learning', (lambda : {
'ok': True,
'id': 'flytying',
'message': 'fly tying ok' }))
    day = '2026-06-17'
    expected = _categories_for_run(day = day)
    results = run_nightly_research(day = day, force = True)
    @py_assert2 = len(results)
    @py_assert7 = len(expected)
    @py_assert9 = 1
    @py_assert11 = @py_assert7 + @py_assert9
    @py_assert4 = @py_assert2 == @py_assert11
    if not @py_assert4:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == (%(py8)s\n{%(py8)s = %(py5)s(%(py6)s)\n} + %(py10)s)',), (@py_assert2, @py_assert11)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(results) if 'results' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(results) else 'results',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py6': @pytest_ar._saferepr(expected) if 'expected' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(expected) else 'expected',
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert0 = results[-1]
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'id'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = 'flytying'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    @py_assert1 = results()
    @py_assert3 = all(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(all) if 'all' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(all) else 'all',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = '_state.json'
    @py_assert3 = research_env / @py_assert1
    @py_assert4 = @py_assert3.is_file
    @py_assert6 = @py_assert4()
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = (%(py0)s / %(py2)s).is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(research_env) if 'research_env' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(research_env) else 'research_env',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert6 = None


def test_intel_rotation(monkeypatch):
    monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_STACK', '0')
    monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_CUSTOM', '0')
    monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_INTEL_PER_NIGHT', '2')
    @py_assert2 = _intel_categories()
    @py_assert4 = len(@py_assert2)
    @py_assert7 = 6
    @py_assert6 = @py_assert4 == @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('==',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n})\n} == %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(_intel_categories) if '_intel_categories' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_intel_categories) else '_intel_categories',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    day = '2026-06-17'
    run_once = _categories_for_run(day = day)
    run_again = _categories_for_run(day = day)
    @py_assert2 = len(run_once)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(run_once) if 'run_once' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(run_once) else 'run_once',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert1 = run_once()
    @py_assert3 = all(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(all) if 'all' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(all) else 'all',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
# WARNING: Decompyle incomplete


def test_custom_topics_from_env(monkeypatch):
    monkeypatch.setenv('JARVIS_KNOWLEDGE_RESEARCH_TOPICS', 'quantum computing, woodworking')
    cats = _all_categories()
# WARNING: Decompyle incomplete


def test_interests_from_profile_uses_interests_field(data_dir):
    _custom_categories = _custom_categories
    _interests_from_profile = _interests_from_profile
    import jarvis.knowledge_research_daily
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    store = MemoryStore(path = data_dir / 'memory.json')
    store.add('fact', 'User often works on: hiking, fly fishing, reading.', tags = [
        'profile',
        'onboarding',
        'interests'], namespace = 'profile')
    store.add('fact', 'User profile (onboarding): Jeff; Brief — bullets, no fluff; Coding & debugging; hiking, fly fishing, reading.', tags = [
        'profile',
        'onboarding',
        'summary'], namespace = 'profile')
    topics = _interests_from_profile(store)
    @py_assert2 = [
        'hiking',
        'fly fishing',
        'reading']
    @py_assert1 = topics == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (topics, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(topics) if 'topics' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(topics) else 'topics',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
# WARNING: Decompyle incomplete


def test_interests_from_profile_includes_notes(data_dir):
    _interests_from_profile = _interests_from_profile
    import jarvis.knowledge_research_daily
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    store = MemoryStore(path = data_dir / 'memory.json')
    store.add('fact', 'User often works on: woodworking.', tags = [
        'profile',
        'onboarding',
        'interests'], namespace = 'profile')
    store.add('preference', 'User notes for Jarvis: astronomy, chess.', tags = [
        'profile',
        'onboarding',
        'notes'], namespace = 'profile')
    topics = _interests_from_profile(store)
    @py_assert2 = [
        'woodworking',
        'astronomy',
        'chess']
    @py_assert1 = topics == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (topics, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(topics) if 'topics' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(topics) else 'topics',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_interests_from_profile_learning_and_expertise(data_dir):
    _custom_categories = _custom_categories
    _interests_from_profile = _interests_from_profile
    import jarvis.knowledge_research_daily
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    store = MemoryStore(path = data_dir / 'memory.json')
    store.add('fact', 'User wants to learn about: quantum computing, Rust.', tags = [
        'profile',
        'onboarding',
        'learning_goals'], namespace = 'profile')
    store.add('fact', 'User already knows: Python, Linux admin.', tags = [
        'profile',
        'onboarding',
        'expertise_areas'], namespace = 'profile')
    store.add('fact', 'User profile (onboarding): Alex; Brief — bullets, no fluff.', tags = [
        'profile',
        'onboarding',
        'summary'], namespace = 'profile')
    topics = _interests_from_profile(store)
    @py_assert0 = 'quantum computing'
    @py_assert2 = @py_assert0 in topics
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, topics)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(topics) if 'topics' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(topics) else 'topics' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Rust'
    @py_assert2 = @py_assert0 in topics
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, topics)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(topics) if 'topics' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(topics) else 'topics' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Python'
    @py_assert2 = @py_assert0 in topics
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, topics)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(topics) if 'topics' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(topics) else 'topics' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
# WARNING: Decompyle incomplete


def test_extract_profile_field_value():
    _extract_profile_field_value = _extract_profile_field_value
    import jarvis.knowledge_research_daily
    @py_assert1 = 'User often works on: hiking, fly fishing, reading.'
    @py_assert3 = 'interests'
    @py_assert5 = _extract_profile_field_value(@py_assert1, @py_assert3)
    @py_assert8 = 'hiking, fly fishing, reading'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_extract_profile_field_value) if '_extract_profile_field_value' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_extract_profile_field_value) else '_extract_profile_field_value',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert1 = 'User wants to learn about: Rust, sourdough.'
    @py_assert3 = 'learning_goals'
    @py_assert5 = _extract_profile_field_value(@py_assert1, @py_assert3)
    @py_assert8 = 'Rust, sourdough'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_extract_profile_field_value) if '_extract_profile_field_value' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_extract_profile_field_value) else '_extract_profile_field_value',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert1 = 'User already knows: Python, Linux.'
    @py_assert3 = 'expertise_areas'
    @py_assert5 = _extract_profile_field_value(@py_assert1, @py_assert3)
    @py_assert8 = 'Python, Linux'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_extract_profile_field_value) if '_extract_profile_field_value' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_extract_profile_field_value) else '_extract_profile_field_value',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert1 = 'User notes for Jarvis: prefers metric units.'
    @py_assert3 = 'notes'
    @py_assert5 = _extract_profile_field_value(@py_assert1, @py_assert3)
    @py_assert8 = 'prefers metric units'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_extract_profile_field_value) if '_extract_profile_field_value' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_extract_profile_field_value) else '_extract_profile_field_value',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert1 = 'User profile (onboarding): Jeff; Brief.'
    @py_assert3 = 'interests'
    @py_assert5 = _extract_profile_field_value(@py_assert1, @py_assert3)
    @py_assert8 = ''
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(_extract_profile_field_value) if '_extract_profile_field_value' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_extract_profile_field_value) else '_extract_profile_field_value',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None


def test_curated_news_skipped_when_ddgs_missing(monkeypatch):
    get_curated_headlines = get_curated_headlines
    import jarvis.curated_news
    monkeypatch.setattr('jarvis.curated_news._ddgs_available', (lambda : False))
    monkeypatch.setattr('jarvis.curated_news._fetch_raw_rss_fallback', (lambda : []))
    monkeypatch.setattr('jarvis.feature_flags.curated_news_enabled', (lambda : True))
    data = get_curated_headlines(use_ai = False, force_refresh = True)
    @py_assert0 = data['enabled']
    @py_assert3 = True
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = data['headlines']
    @py_assert3 = []
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = data['skipped']
    @py_assert3 = 'duckduckgo-search not installed'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_router_knowledge_research():
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    intent = route('run nightly knowledge research', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'knowledge_research_run'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_knowledge_research_handler_registered():
    ensure_handlers_loaded = ensure_handlers_loaded
    import jarvis.handlers
    get_spec = get_spec
    import jarvis.handlers.registry
    ensure_handlers_loaded()
    spec = get_spec('knowledge_research_run')
    @py_assert2 = None
    @py_assert1 = spec is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (spec, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(spec) if 'spec' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(spec) else 'spec',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = spec.handler
    @py_assert4 = None
    @py_assert3 = @py_assert1 is not @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is not',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.handler\n} is not %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(spec) if 'spec' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(spec) else 'spec',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = spec.queue
    @py_assert4 = 'background'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.queue\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(spec) if 'spec' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(spec) else 'spec',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

