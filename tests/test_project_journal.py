# Source Generated with Decompyle++
# File: test_project_journal.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Project journal and journal learning tests.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.journal_learning import JOURNAL_LEARN_TAG, extract_journal_learnings, learn_from_project_journal
from jarvis.modules.memory import MemoryStore
from jarvis.project_journal import ProjectJournal, list_projects, resolve_project
journal_env = (lambda data_dir, monkeypatch: projects = data_dir / 'journal' / 'projects'projects.mkdir(parents = True, exist_ok = True)monkeypatch.setattr('jarvis.project_journal.PROJECTS_DIR', projects)monkeypatch.setattr('jarvis.project_journal.INDEX_FILE', projects / 'index.json')projects)()
store = (lambda data_dir, monkeypatch: monkeypatch.delenv('JARVIS_GRAPH_BACKEND', raising = False)monkeypatch.delenv('JARVIS_VECTOR_BACKEND', raising = False)monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
0.1,
0.2]))
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_resolve_project():
    @py_assert1 = 'log to jarvis project journal: test'
    @py_assert3 = resolve_project(@py_assert1)
    @py_assert6 = 'jarvis'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_project) if 'resolve_project' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_project) else 'resolve_project',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'learn from aria project journal'
    @py_assert3 = resolve_project(@py_assert1)
    @py_assert6 = 'aria'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_project) if 'resolve_project' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_project) else 'resolve_project',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_project_journal_daily(journal_env):
    j = ProjectJournal('jarvis')
    j.ensure(title = 'Jarvis')
    b = j.daily_add('Shipped memory graph integration')
    @py_assert0 = b['content']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    @py_assert0 = 'Shipped'
    @py_assert4 = j.format_daily
    @py_assert6 = @py_assert4()
    @py_assert2 = @py_assert0 in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s.format_daily\n}()\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(j) if 'j' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(j) else 'j',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert1 = list_projects()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(list_projects) if 'list_projects' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_projects) else 'list_projects',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None


def test_learn_from_project_journal(monkeypatch, store, journal_env):
    monkeypatch.setattr('jarvis.llm.ask', (lambda : '{"facts": ["Jarvis memory graph uses Memgraph on port 7687."]}'))
    j = ProjectJournal('jarvis')
    j.daily_add('Memgraph running on 7687 for relationship graph')
    result = learn_from_project_journal(store, 'jarvis', namespace = 'jarvis')
    @py_assert0 = result['ok']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    entries = store.list_entries(namespace = 'jarvis')
    @py_assert1 = entries()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
# WARNING: Decompyle incomplete


def test_extract_journal_learnings(monkeypatch):
    monkeypatch.setattr('jarvis.llm.ask', (lambda : '{"facts": ["Decided to use Chroma for vectors."]}'))
    facts = extract_journal_learnings('Today we picked ChromaDB.', project = 'jarvis', day = '2026-06-17')
    @py_assert2 = len(facts)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(facts) if 'facts' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(facts) else 'facts',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_extract_journal_learnings_malformed_json(monkeypatch):
    monkeypatch.setattr('jarvis.llm.ask', (lambda : 'Here you go:\n{"facts": ["Shipped sunlight scene caching."]}\nThanks!'))
    facts = extract_journal_learnings('Sunlight work today.', project = 'jarvis', day = '2026-06-25')
    @py_assert2 = [
        'Shipped sunlight scene caching.']
    @py_assert1 = facts == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (facts, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(facts) if 'facts' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(facts) else 'facts',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None

