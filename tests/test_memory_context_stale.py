# Source Generated with Decompyle++
# File: test_memory_context_stale.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Stale journal memory and resume-context gating.'''
import builtins as @py_builtins

rewrite
from datetime import date
import _pytest.assertion.rewrite, assertion
from jarvis.memory_context import contextualize_memory_for_chat, normalize_journal_memory_text, should_inject_resume_context
from jarvis.router import is_meta_self_question
from jarvis.session import SessionContext

def test_meta_self_skips_resume_context():
    msg = 'how hard would it be for you to fix or upgrade yourself'
    @py_assert2 = is_meta_self_question(msg)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_meta_self_question) if 'is_meta_self_question' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_meta_self_question) else 'is_meta_self_question',
            'py1': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    @py_assert3 = SessionContext()
    @py_assert5 = should_inject_resume_context(msg, @py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py0)s(%(py1)s, %(py4)s\n{%(py4)s = %(py2)s()\n})\n}' % {
            'py0': @pytest_ar._saferepr(should_inject_resume_context) if 'should_inject_resume_context' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_inject_resume_context) else 'should_inject_resume_context',
            'py1': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
            'py2': @pytest_ar._saferepr(SessionContext) if 'SessionContext' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(SessionContext) else 'SessionContext',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_resume_context_for_coding_followup():
    session = SessionContext(last_module = 'coding')
    @py_assert1 = 'hello'
    @py_assert4 = should_inject_resume_context(@py_assert1, session)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(should_inject_resume_context) if 'should_inject_resume_context' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_inject_resume_context) else 'should_inject_resume_context',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(session) if 'session' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(session) else 'session',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert1 = 'debug until tests pass for foo.py'
    @py_assert4 = SessionContext()
    @py_assert6 = should_inject_resume_context(@py_assert1, @py_assert4)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py0)s(%(py2)s, %(py5)s\n{%(py5)s = %(py3)s()\n})\n}' % {
            'py0': @pytest_ar._saferepr(should_inject_resume_context) if 'should_inject_resume_context' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_inject_resume_context) else 'should_inject_resume_context',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(SessionContext) if 'SessionContext' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(SessionContext) else 'SessionContext',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None


def test_normalize_birthday_journal_memory():
    raw = "From bullet journal (daily:2026-06-09): — Today is mom's birthday."
    @py_assert2 = normalize_journal_memory_text(raw)
    @py_assert5 = "Mom's birthday is June 9."
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(normalize_journal_memory_text) if 'normalize_journal_memory_text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_journal_memory_text) else 'normalize_journal_memory_text',
            'py1': @pytest_ar._saferepr(raw) if 'raw' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(raw) else 'raw',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_contextualize_stale_birthday_as_permanent_fact():
    raw = "From bullet journal (daily:2026-06-09): — Today is mom's birthday."
    out = contextualize_memory_for_chat(raw, today = date(2026, 6, 13))
    @py_assert2 = "Mom's birthday is June 9."
    @py_assert1 = out == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (out, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_contextualize_stale_today_note_dropped():
    raw = 'From bullet journal (daily:2026-06-08): — Today I need to call the bank.'
    @py_assert3 = 2026
    @py_assert5 = 6
    @py_assert7 = 13
    @py_assert9 = date(@py_assert3, @py_assert5, @py_assert7)
    @py_assert11 = contextualize_memory_for_chat(raw, today = @py_assert9)
    @py_assert14 = None
    @py_assert13 = @py_assert11 is @py_assert14
    if not @py_assert13:
        @py_format16 = @pytest_ar._call_reprcompare(('is',), (@py_assert13,), ('%(py12)s\n{%(py12)s = %(py0)s(%(py1)s, today=%(py10)s\n{%(py10)s = %(py2)s(%(py4)s, %(py6)s, %(py8)s)\n})\n} is %(py15)s',), (@py_assert11, @py_assert14)) % {
            'py0': @pytest_ar._saferepr(contextualize_memory_for_chat) if 'contextualize_memory_for_chat' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(contextualize_memory_for_chat) else 'contextualize_memory_for_chat',
            'py1': @pytest_ar._saferepr(raw) if 'raw' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(raw) else 'raw',
            'py2': @pytest_ar._saferepr(date) if 'date' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(date) else 'date',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11),
            'py15': @pytest_ar._saferepr(@py_assert14) }
        @py_format18 = 'assert %(py17)s' % {
            'py17': @py_format16 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format18))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert13 = None
    @py_assert14 = None

