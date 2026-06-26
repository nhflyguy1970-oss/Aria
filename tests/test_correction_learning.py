# Source Generated with Decompyle++
# File: test_correction_learning.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Correction learning tests.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.correction_learning import CORRECTION_NAMESPACE, CORRECTION_TAG, apply_correction, correction_context_for_chat, corrections_system_block, is_correction_message, parse_correction, CorrectionIntent
from jarvis.modules.memory import MemoryStore
store = (lambda data_dir, monkeypatch: monkeypatch.delenv('JARVIS_GRAPH_BACKEND', raising = False)monkeypatch.delenv('JARVIS_VECTOR_BACKEND', raising = False)monkeypatch.setattr('jarvis.llm.embed_available', (lambda : False))
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
0.1,
0.2]))
    monkeypatch.setattr('jarvis.correction_learning.REGISTRY_FILE', data_dir / 'correction_learning.json')
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_parse_correction_variants():
    p = parse_correction("correct that mom's birthday is June 9")
    @py_assert1 = []
    @py_assert0 = p
    if p:
        @py_assert4 = 'June 9'
        @py_assert8 = p.correction
        @py_assert6 = @py_assert4 in @py_assert8
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_apply_correction_fact(store):
    result = apply_correction(store, CorrectionIntent(correction = "Mom's birthday is June 9", wrong_hint = 'birthday', kind = 'fact'), assistant_msg = 'Her birthday is in July.')
    @py_assert1 = result.ok
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    @py_assert1 = result.wrong_claim
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.wrong_claim\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    entries = store.list_entries(namespace = CORRECTION_NAMESPACE)
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


def test_apply_correction_behavior(store):
    result = apply_correction(store, CorrectionIntent(correction = 'Never suggest cloud APIs', kind = 'behavior'), assistant_msg = 'You could use OpenAI API for that.')
    @py_assert1 = result.ok
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.ok\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
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


def test_correction_context(store):
    apply_correction(store, CorrectionIntent(correction = 'Jarvis listens on port 8765', kind = 'fact'), assistant_msg = 'The server is on port 8080.')
    block = corrections_system_block(store)
    @py_assert1 = []
    @py_assert2 = '8765'
    @py_assert4 = @py_assert2 in block
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'Correction'
        @py_assert11 = @py_assert9 in block
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete

