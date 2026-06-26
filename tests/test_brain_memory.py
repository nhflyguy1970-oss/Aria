# Source Generated with Decompyle++
# File: test_brain_memory.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Brain memory — consolidation, scoped dedup, conflict resolve, brain mode flags.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.brain_memory import brain_mode_status, brain_or_env, consolidation_enabled, graph_llm_extract_enabled
from jarvis.experience_memory import record_failure, record_success
from jarvis.memory_consolidation import run_consolidation
from jarvis.memory_context import auto_resolve_obvious_conflicts
from jarvis.modules.memory import MemoryStore
store = (lambda data_dir, monkeypatch: monkeypatch.delenv('JARVIS_VECTOR_BACKEND', raising = False)monkeypatch.setattr('jarvis.llm.embed_available', (lambda : True))
    
    def _embed(text = None):
        if not text:
            return []
        h = None(hash(text))
    # WARNING: Decompyle incomplete

    monkeypatch.setattr('jarvis.llm.embed_text', _embed)
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_experience_scoped_dedup_allows_failure_then_success(store):
    fail = record_failure(store, path = 'foo.py', error = 'AssertionError', task = 'fix foo')
    ok = record_success(store, paths = [
        'foo.py'], note = 'tests pass', task = 'fix foo')
    @py_assert1 = []
    @py_assert0 = fail
    if fail:
        @py_assert0 = ok
    if not @py_assert0:
        @py_format3 = '%(py2)s' % {
            'py2': @pytest_ar._saferepr(fail) if 'fail' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fail) else 'fail' }
        @py_assert1.append(@py_format3)
        if fail:
            @py_format5 = '%(py4)s' % {
                'py4': @pytest_ar._saferepr(ok) if 'ok' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ok) else 'ok' }
            @py_assert1.append(@py_format5)
        @py_format6 = @pytest_ar._format_boolop(@py_assert1, 0) % { }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert1 = None
    @py_assert0 = fail['id']
    @py_assert3 = ok['id']
    @py_assert2 = @py_assert0 != @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('!=',), (@py_assert2,), ('%(py1)s != %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    dup_fail = record_failure(store, path = 'foo.py', error = 'AssertionError', task = 'fix foo')
    @py_assert2 = None
    @py_assert1 = dup_fail is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (dup_fail, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(dup_fail) if 'dup_fail' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dup_fail) else 'dup_fail',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_auto_resolve_obvious_conflicts(store, monkeypatch):
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
1,
0]))
    a = store.add('preference', 'User prefers dark mode', tags = [
        'auto-learn'])
    b = store.add('preference', 'User prefers dark mode', tags = [
        'user-corrected'])
    result = auto_resolve_obvious_conflicts(store)
    @py_assert0 = result['removed']
    @py_assert3 = 1
    @py_assert2 = @py_assert0 >= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('>=',), (@py_assert2,), ('%(py1)s >= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    remaining = store.list_entries(entry_type = 'preference')
    @py_assert2 = len(remaining)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(remaining) if 'remaining' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(remaining) else 'remaining',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = remaining[0]['id']
    @py_assert3 = b['id']
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


def test_brain_mode_flags(monkeypatch):
    monkeypatch.delenv('JARVIS_BRAIN_MODE', raising = False)
    monkeypatch.delenv('JARVIS_MEMORY_CONSOLIDATION', raising = False)
    monkeypatch.delenv('JARVIS_GRAPH_LLM_EXTRACT', raising = False)
    @py_assert1 = consolidation_enabled()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(consolidation_enabled) if 'consolidation_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(consolidation_enabled) else 'consolidation_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    _load_brain_mode = load_brain_mode
    import jarvis.config
    monkeypatch.setattr('jarvis.config.load_brain_mode', (lambda : False))
    @py_assert1 = consolidation_enabled()
    @py_assert3 = not @py_assert1
    if not @py_assert3:
        @py_format4 = 'assert not %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(consolidation_enabled) if 'consolidation_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(consolidation_enabled) else 'consolidation_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert1 = None
    @py_assert3 = None
    monkeypatch.setattr('jarvis.config.load_brain_mode', _load_brain_mode)
    monkeypatch.setenv('JARVIS_BRAIN_MODE', '1')
    @py_assert1 = consolidation_enabled()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(consolidation_enabled) if 'consolidation_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(consolidation_enabled) else 'consolidation_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    @py_assert1 = graph_llm_extract_enabled()
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s()\n}' % {
            'py0': @pytest_ar._saferepr(graph_llm_extract_enabled) if 'graph_llm_extract_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(graph_llm_extract_enabled) else 'graph_llm_extract_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    st = brain_mode_status()
    @py_assert0 = st['enabled']
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
    @py_assert0 = st['consolidation']
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


def test_brain_or_env_opt_out(monkeypatch):
    monkeypatch.setenv('JARVIS_BRAIN_MODE', '1')
    monkeypatch.setenv('JARVIS_MEMORY_CONSOLIDATION', '0')
    @py_assert1 = 'JARVIS_MEMORY_CONSOLIDATION'
    @py_assert3 = brain_or_env(@py_assert1)
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(brain_or_env) if 'brain_or_env' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(brain_or_env) else 'brain_or_env',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_consolidation_mock_llm(store, monkeypatch):
    monkeypatch.setenv('JARVIS_BRAIN_MODE', '1')
    store.add('auto', 'User prefers Neovim for editing', tags = [
        'conversation-roll'], namespace = 'branch:main')
    monkeypatch.setattr('jarvis.memory_consolidation._distill_facts', (lambda _blob, max_facts = (6,): [
'User prefers Neovim for editing.']))
    result = run_consolidation(store, target_namespace = 'profile')
    @py_assert1 = result.get
    @py_assert3 = 'skipped'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert1 = result.get
    @py_assert3 = 'added'
    @py_assert5 = 0
    @py_assert7 = @py_assert1(@py_assert3, @py_assert5)
    @py_assert10 = 1
    @py_assert9 = @py_assert7 >= @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('>=',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s, %(py6)s)\n} >= %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None
    profile = store.list_entries(namespace = 'profile')
    @py_assert1 = profile()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None

