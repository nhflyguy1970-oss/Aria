# Source Generated with Decompyle++
# File: test_morning_briefing.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Morning briefing — weather, tasks, launch gating.'''
import builtins as @py_builtins

rewrite
from datetime import datetime
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.modules.journal import BulletJournal
from jarvis.morning_briefing import briefing_visible, build_briefing, mark_briefing_shown, personalized_greeting, profile_first_name, should_show_launch_briefing, time_greeting
from jarvis.router import route
from jarvis.session import SessionContext
journal = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.modules.journal.JOURNAL_FILE', data_dir / 'journal' / 'bullet_journal.json')monkeypatch.setattr('jarvis.modules.journal.JOURNAL_DIR', data_dir / 'journal')(data_dir / 'journal').mkdir(parents = True, exist_ok = True)BulletJournal(path = data_dir / 'journal' / 'bullet_journal.json'))()
store = (lambda data_dir, monkeypatch: monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
1,
0]))
    MemoryStore = MemoryStore
    import jarvis.modules.memory
    return MemoryStore(path = data_dir / 'memory.json')
)()

def test_time_greeting():
    @py_assert2 = 2026
    @py_assert4 = 6
    @py_assert6 = 8
    @py_assert8 = 9
    @py_assert10 = 0
    @py_assert12 = datetime(@py_assert2, @py_assert4, @py_assert6, @py_assert8, @py_assert10)
    @py_assert14 = time_greeting(when = @py_assert12)
    @py_assert17 = 'Good morning'
    @py_assert16 = @py_assert14 == @py_assert17
    if not @py_assert16:
        @py_format19 = @pytest_ar._call_reprcompare(('==',), (@py_assert16,), ('%(py15)s\n{%(py15)s = %(py0)s(when=%(py13)s\n{%(py13)s = %(py1)s(%(py3)s, %(py5)s, %(py7)s, %(py9)s, %(py11)s)\n})\n} == %(py18)s',), (@py_assert14, @py_assert17)) % {
            'py0': @pytest_ar._saferepr(time_greeting) if 'time_greeting' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(time_greeting) else 'time_greeting',
            'py1': @pytest_ar._saferepr(datetime) if 'datetime' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(datetime) else 'datetime',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10),
            'py13': @pytest_ar._saferepr(@py_assert12),
            'py15': @pytest_ar._saferepr(@py_assert14),
            'py18': @pytest_ar._saferepr(@py_assert17) }
        @py_format21 = 'assert %(py20)s' % {
            'py20': @py_format19 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format21))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert12 = None
    @py_assert14 = None
    @py_assert16 = None
    @py_assert17 = None
    @py_assert2 = 2026
    @py_assert4 = 6
    @py_assert6 = 8
    @py_assert8 = 14
    @py_assert10 = 0
    @py_assert12 = datetime(@py_assert2, @py_assert4, @py_assert6, @py_assert8, @py_assert10)
    @py_assert14 = time_greeting(when = @py_assert12)
    @py_assert17 = 'Good afternoon'
    @py_assert16 = @py_assert14 == @py_assert17
    if not @py_assert16:
        @py_format19 = @pytest_ar._call_reprcompare(('==',), (@py_assert16,), ('%(py15)s\n{%(py15)s = %(py0)s(when=%(py13)s\n{%(py13)s = %(py1)s(%(py3)s, %(py5)s, %(py7)s, %(py9)s, %(py11)s)\n})\n} == %(py18)s',), (@py_assert14, @py_assert17)) % {
            'py0': @pytest_ar._saferepr(time_greeting) if 'time_greeting' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(time_greeting) else 'time_greeting',
            'py1': @pytest_ar._saferepr(datetime) if 'datetime' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(datetime) else 'datetime',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10),
            'py13': @pytest_ar._saferepr(@py_assert12),
            'py15': @pytest_ar._saferepr(@py_assert14),
            'py18': @pytest_ar._saferepr(@py_assert17) }
        @py_format21 = 'assert %(py20)s' % {
            'py20': @py_format19 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format21))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert12 = None
    @py_assert14 = None
    @py_assert16 = None
    @py_assert17 = None
    @py_assert2 = 2026
    @py_assert4 = 6
    @py_assert6 = 8
    @py_assert8 = 19
    @py_assert10 = 0
    @py_assert12 = datetime(@py_assert2, @py_assert4, @py_assert6, @py_assert8, @py_assert10)
    @py_assert14 = time_greeting(when = @py_assert12)
    @py_assert17 = 'Good evening'
    @py_assert16 = @py_assert14 == @py_assert17
    if not @py_assert16:
        @py_format19 = @pytest_ar._call_reprcompare(('==',), (@py_assert16,), ('%(py15)s\n{%(py15)s = %(py0)s(when=%(py13)s\n{%(py13)s = %(py1)s(%(py3)s, %(py5)s, %(py7)s, %(py9)s, %(py11)s)\n})\n} == %(py18)s',), (@py_assert14, @py_assert17)) % {
            'py0': @pytest_ar._saferepr(time_greeting) if 'time_greeting' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(time_greeting) else 'time_greeting',
            'py1': @pytest_ar._saferepr(datetime) if 'datetime' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(datetime) else 'datetime',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10),
            'py13': @pytest_ar._saferepr(@py_assert12),
            'py15': @pytest_ar._saferepr(@py_assert14),
            'py18': @pytest_ar._saferepr(@py_assert17) }
        @py_format21 = 'assert %(py20)s' % {
            'py20': @py_format19 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format21))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert12 = None
    @py_assert14 = None
    @py_assert16 = None
    @py_assert17 = None


def test_profile_first_name(store):
    store.add('fact', "User's name is Jeff.", tags = [
        'profile',
        'name'], namespace = 'profile')
    @py_assert2 = profile_first_name(store)
    @py_assert5 = 'Jeff'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(profile_first_name) if 'profile_first_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(profile_first_name) else 'profile_first_name',
            'py1': @pytest_ar._saferepr(store) if 'store' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(store) else 'store',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_personalized_greeting(store, monkeypatch):
    monkeypatch.setenv('JARVIS_USER_NAME', '')
    when = datetime(2026, 6, 8, 9, 30)
    bare = personalized_greeting(when = when)
    @py_assert0 = bare['greeting_short']
    @py_assert3 = 'Good morning'
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
    @py_assert0 = bare['welcome']
    @py_assert3 = 'Welcome back'
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
    store.add('fact', "User's name is Jeff.", tags = [
        'profile',
        'name'], namespace = 'profile')
    named = personalized_greeting(when = when, memory_store = store)
    @py_assert0 = named['greeting']
    @py_assert3 = 'Good morning, Jeff'
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
    @py_assert0 = named['welcome']
    @py_assert3 = 'Welcome back, Jeff'
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
    @py_assert0 = named['date_label']
    @py_assert3 = 'Monday, June 08'
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


def test_build_briefing_includes_tasks(journal, store, monkeypatch):
    monkeypatch.setattr('jarvis.modules.journal._today', (lambda : '2026-06-08'))
    monkeypatch.setattr('jarvis.morning_briefing.weather_for_day', (lambda day: {
'date': day,
'condition': 'Clear',
'high': 72,
'low': 58,
'unit': '°F',
'location': 'Charlestown, NH',
'icon': '☀️' }))
    journal.daily_add('Team standup', 'event', day = '2026-06-08')
    journal.daily_add('finish taxes', 'task', day = '2026-06-08')
    briefing = build_briefing(journal = journal, memory_store = store, day = '2026-06-08', reference = datetime(2026, 6, 8, 8, 30))
    @py_assert0 = 'Good morning'
    @py_assert3 = briefing['salutation']
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
    @py_assert0 = 'finish taxes'
    @py_assert3 = briefing['markdown']
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
    @py_assert0 = 'Team standup'
    @py_assert3 = briefing['markdown']
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
    @py_assert0 = briefing['open_task_count']
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


def test_launch_briefing_once_per_day(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.morning_briefing._load_chat_settings', (lambda : { }))
    monkeypatch.setattr('jarvis.morning_briefing._write_chat_settings', (lambda data: pass))
    @py_assert1 = '2026-06-08'
    @py_assert3 = should_show_launch_briefing(day = @py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(day=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(should_show_launch_briefing) if 'should_show_launch_briefing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_show_launch_briefing) else 'should_show_launch_briefing',
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
    mark_briefing_shown('2026-06-08')
    monkeypatch.setattr('jarvis.morning_briefing._load_chat_settings', (lambda : {
'morning_briefing': {
'last_shown': '2026-06-08' } }))
    @py_assert1 = '2026-06-08'
    @py_assert3 = should_show_launch_briefing(day = @py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(day=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(should_show_launch_briefing) if 'should_show_launch_briefing' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_show_launch_briefing) else 'should_show_launch_briefing',
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


def test_briefing_visible_respects_dismiss(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.morning_briefing._load_chat_settings', (lambda : { }))
    @py_assert1 = '2026-06-08'
    @py_assert3 = briefing_visible(day = @py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(day=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(briefing_visible) if 'briefing_visible' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_visible) else 'briefing_visible',
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
    mark_briefing_shown('2026-06-08')
    monkeypatch.setattr('jarvis.morning_briefing._load_chat_settings', (lambda : {
'morning_briefing': {
'last_shown': '2026-06-08' } }))
    @py_assert1 = '2026-06-08'
    @py_assert3 = briefing_visible(day = @py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(day=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(briefing_visible) if 'briefing_visible' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_visible) else 'briefing_visible',
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
    @py_assert1 = True
    @py_assert3 = '2026-06-08'
    @py_assert5 = briefing_visible(force = @py_assert1, day = @py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(force=%(py2)s, day=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(briefing_visible) if 'briefing_visible' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(briefing_visible) else 'briefing_visible',
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


def test_morning_briefing_route():
    intent = route('morning briefing', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'morning_briefing'
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


def test_good_morning_routes_to_briefing(monkeypatch):
    monkeypatch.setenv('JARVIS_BRIEFING', '1')
    intent = route('good morning', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'morning_briefing'
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

