# Source Generated with Decompyle++
# File: test_explicit_teaching.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Explicit teaching tests.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.explicit_teaching import TEACHING_NAMESPACE, apply_explicit_teaching, explicit_teaching_context_for_chat, explicit_teaching_system_block, infer_teaching_kind, list_teachings, parse_teach_message, parse_teach_recall_query, TeachIntent
from jarvis.modules.memory import MemoryStore
store = (lambda data_dir, monkeypatch: monkeypatch.delenv('JARVIS_GRAPH_BACKEND', raising = False)monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
0.1,
0.2]))
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_parse_teach_typed_and_bare():
    p = parse_teach_message('teach rule: always use bullet points')
    @py_assert1 = []
    @py_assert0 = p
    if p:
        @py_assert5 = p.kind
        @py_assert8 = 'rule'
        @py_assert7 = @py_assert5 == @py_assert8
        @py_assert0 = @py_assert7
# WARNING: Decompyle incomplete


def test_infer_kind():
    @py_assert1 = 'First pull the model, then run ollama serve'
    @py_assert3 = infer_teaching_kind(@py_assert1)
    @py_assert6 = 'procedure'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(infer_teaching_kind) if 'infer_teaching_kind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(infer_teaching_kind) else 'infer_teaching_kind',
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
    @py_assert1 = 'Never suggest cloud APIs'
    @py_assert3 = infer_teaching_kind(@py_assert1)
    @py_assert6 = 'rule'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(infer_teaching_kind) if 'infer_teaching_kind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(infer_teaching_kind) else 'infer_teaching_kind',
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


def test_apply_explicit_teaching_fact(store):
    result = apply_explicit_teaching(store, TeachIntent(kind = 'fact', content = 'Jarvis lives at /media/jeff/AI/jarvis'))
    @py_assert0 = result.entry['type']
    @py_assert3 = 'teaching'
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
    @py_assert0 = result.entry['namespace']
    @py_assert2 = @py_assert0 == TEACHING_NAMESPACE
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py3)s',), (@py_assert0, TEACHING_NAMESPACE)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(TEACHING_NAMESPACE) if 'TEACHING_NAMESPACE' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(TEACHING_NAMESPACE) else 'TEACHING_NAMESPACE' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    EXPLICIT_TEACH_TAG = 'explicit-teach'
    @py_assert0 = EXPLICIT_TEACH_TAG in result.entry['tags'] if 'explicit-teach' else True
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    @py_assert3 = list_teachings(store)
    @py_assert5 = len(@py_assert3)
    @py_assert8 = 1
    @py_assert7 = @py_assert5 >= @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('>=',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py4)s\n{%(py4)s = %(py1)s(%(py2)s)\n})\n} >= %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(list_teachings) if 'list_teachings' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_teachings) else 'list_teachings',
            'py2': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None


def test_apply_explicit_teaching_rule(store):
    result = apply_explicit_teaching(store, TeachIntent(kind = 'rule', content = 'Keep answers concise'))
    @py_assert1 = result.kind
    @py_assert4 = 'rule'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.kind\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = store.list_entries
    @py_assert3 = 'strategy'
    @py_assert5 = @py_assert1(entry_type = @py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.list_entries\n}(entry_type=%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_teach_recall_query():
    @py_assert0 = 'tabs'
    @py_assert4 = 'what did I teach you about tabs'
    @py_assert6 = parse_teach_recall_query(@py_assert4)
    @py_assert2 = @py_assert0 in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(parse_teach_recall_query) if 'parse_teach_recall_query' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_teach_recall_query) else 'parse_teach_recall_query',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_system_and_chat_context(store):
    apply_explicit_teaching(store, TeachIntent(kind = 'rule', content = 'Never use cloud APIs'))
    block = explicit_teaching_system_block(store)
    @py_assert0 = 'Explicit teachings'
    @py_assert2 = @py_assert0 in block
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, block)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(block) if 'block' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(block) else 'block' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    ctx = explicit_teaching_context_for_chat(store, 'should I use a cloud API?')
    @py_assert1 = []
    @py_assert2 = 'cloud'
    @py_assert6 = ctx.lower
    @py_assert8 = @py_assert6()
    @py_assert4 = @py_assert2 in @py_assert8
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert13 = 'Explicit'
        @py_assert15 = @py_assert13 in ctx
        @py_assert0 = @py_assert15
        if not @py_assert15:
            @py_assert20 = 'teachings'
            @py_assert24 = ctx.lower
            @py_assert26 = @py_assert24()
            @py_assert22 = @py_assert20 in @py_assert26
            @py_assert0 = @py_assert22
# WARNING: Decompyle incomplete

