# Source Generated with Decompyle++
# File: test_profile_name.cpython-312-pytest-9.0.3.pyc (Python 3.12)

"""Profile name parsing — avoid false positives like 'I am still…'."""
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from datetime import datetime
from jarvis.profile_questionnaire import is_plausible_first_name, maybe_apply_name_message, update_profile_name
store = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
1,
0]))
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    return MemoryStore(path = data_dir / 'memory.json')
)()
journal = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.modules.journal.JOURNAL_FILE', data_dir / 'journal' / 'bullet_journal.json')monkeypatch.setattr('jarvis.modules.journal.JOURNAL_DIR', data_dir / 'journal')(data_dir / 'journal').mkdir(parents = True, exist_ok = True)BulletJournal = BulletJournalimport jarvis.modules.journalBulletJournal(path = data_dir / 'journal' / 'bullet_journal.json'))()

def test_is_plausible_first_name_rejects_still():
    @py_assert1 = 'still'
    @py_assert3 = is_plausible_first_name(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_plausible_first_name) if 'is_plausible_first_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_plausible_first_name) else 'is_plausible_first_name',
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
    @py_assert1 = 'Jeff'
    @py_assert3 = is_plausible_first_name(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_plausible_first_name) if 'is_plausible_first_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_plausible_first_name) else 'is_plausible_first_name',
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


def test_maybe_apply_name_message_ignores_i_am_still(store):
    @py_assert2 = 'i am still getting you set up and configured.'
    @py_assert4 = maybe_apply_name_message(store, @py_assert2)
    @py_assert7 = False
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py1)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(maybe_apply_name_message) if 'maybe_apply_name_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(maybe_apply_name_message) else 'maybe_apply_name_message',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
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
    @py_assert2 = profile_name(store)
    @py_assert5 = None
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(profile_name) if 'profile_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(profile_name) else 'profile_name',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_maybe_apply_name_message_accepts_my_name_is(store):
    @py_assert2 = 'my name is Jeff'
    @py_assert4 = maybe_apply_name_message(store, @py_assert2)
    @py_assert7 = True
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py1)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(maybe_apply_name_message) if 'maybe_apply_name_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(maybe_apply_name_message) else 'maybe_apply_name_message',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
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
    @py_assert2 = profile_name(store)
    @py_assert5 = 'Jeff'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(profile_name) if 'profile_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(profile_name) else 'profile_name',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_maybe_apply_name_message_accepts_capitalized_i_am(store):
    @py_assert2 = "I'm Jeff"
    @py_assert4 = maybe_apply_name_message(store, @py_assert2)
    @py_assert7 = True
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py1)s, %(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(maybe_apply_name_message) if 'maybe_apply_name_message' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(maybe_apply_name_message) else 'maybe_apply_name_message',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
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
    @py_assert2 = profile_name(store)
    @py_assert5 = 'Jeff'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(profile_name) if 'profile_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(profile_name) else 'profile_name',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_build_briefing_prefers_env_over_bad_memory(journal, store, monkeypatch):
    monkeypatch.setattr('jarvis.modules.journal._today', (lambda : '2026-06-22'))
    monkeypatch.setattr('jarvis.morning_briefing.weather_for_day', (lambda day: { }))
    store.add('fact', "User's name is still.", tags = [
        'profile',
        'name'], namespace = 'profile')
    monkeypatch.setenv('JARVIS_USER_NAME', 'Jeff')
    build_briefing = build_briefing
    import jarvis.morning_briefing
    briefing = build_briefing(journal = journal, memory_store = store, day = '2026-06-22', reference = datetime(2026, 6, 22, 9, 0), include_news = False)
    @py_assert0 = briefing['salutation']
    @py_assert3 = 'Good morning, Jeff.'
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


def profile_name(store):
    profile_first_name = profile_first_name
    import jarvis.morning_briefing
    return profile_first_name(store)

