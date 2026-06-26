# Source Generated with Decompyle++
# File: test_journal.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Bullet journal store, routing, and handlers.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.modules.journal import BulletJournal, _format_bullet, _month_key, _today
from jarvis.router import route
from jarvis.session import SessionContext
journal = (lambda data_dir: BulletJournal(path = data_dir / 'journal' / 'bullet_journal.json'))()
session = (lambda : SessionContext())()

def test_daily_add_and_complete(journal):
    b = journal.daily_add('Write tests', 'task')
    @py_assert0 = b['type']
    @py_assert3 = 'task'
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
    page = journal.daily_get()
    @py_assert1 = page['bullets']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    done = journal.bullet_complete(b['id'])
    @py_assert1 = []
    @py_assert0 = done
    if done:
        @py_assert4 = done['status']
        @py_assert7 = 'done'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_parse_rapid_log(journal):
    text = '• task one\n○ meeting\n— note line'
    created = journal.parse_rapid_log(text)
    @py_assert2 = len(created)
    @py_assert5 = 3
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(created) if 'created' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(created) else 'created',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
# WARNING: Decompyle incomplete


def test_parse_rapid_log_default_type(journal):
    created = journal.parse_rapid_log('Dentist at 3pm', default_type = 'event')
    @py_assert2 = len(created)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(created) if 'created' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(created) else 'created',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = created[0]['type']
    @py_assert3 = 'event'
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


def test_parse_rapid_log_text_prefixes(journal):
    created = journal.parse_rapid_log('e: team standup\nt: pytest journal scratch\nn: idea')
# WARNING: Decompyle incomplete


def test_monthly_calendar(journal):
    journal.daily_add('Day entry', 'task', day = '2026-06-08')
    journal.monthly_calendar_note(8, 'Fly fishing')
    cal = journal.monthly_calendar('2026-06')
    @py_assert1 = cal['weeks']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 4
    @py_assert5 = @py_assert3 >= @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('>=',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} >= %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    @py_assert0 = cal['days']['8']['count']
    @py_assert3 = 1
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
    @py_assert0 = cal['calendar_notes']['8']
    @py_assert3 = 'Fly fishing'
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
    @py_assert0 = '2026-06-19'
    @py_assert3 = cal['holidays']
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
    @py_assert0 = cal['holidays']['2026-06-19'][0]['name']
    @py_assert3 = 'Juneteenth'
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


def test_journal_holidays_observed_weekend(monkeypatch):
    holidays_for_month = holidays_for_month
    import jarvis.journal_holidays
    monkeypatch.delenv('JARVIS_HOLIDAY_STATE', raising = False)
    monkeypatch.delenv('JARVIS_WEATHER_LOCATION', raising = False)
    july = holidays_for_month('2026-07', state = None)
    @py_assert0 = '2026-07-03'
    @py_assert2 = @py_assert0 in july
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, july)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(july) if 'july' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(july) else 'july' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = july['2026-07-03'][0]['name']
    @py_assert3 = 'Independence Day'
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


def test_journal_holidays_observances(monkeypatch):
    holidays_for_month = holidays_for_month
    import jarvis.journal_holidays
    monkeypatch.setenv('JARVIS_HOLIDAY_OBSERVANCES', '1')
    may = holidays_for_month('2026-05', state = None)
    @py_assert0 = '2026-05-10'
    @py_assert2 = @py_assert0 in may
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, may)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(may) if 'may' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(may) else 'may' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = may['2026-05-10']()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    june = holidays_for_month('2026-06', state = None)
    @py_assert0 = '2026-06-21'
    @py_assert2 = @py_assert0 in june
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, june)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(june) if 'june' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(june) else 'june' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = june['2026-06-21']()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_open_tasks(journal):
    journal.daily_add('Open task', 'task')
    journal.daily_add('Done task', 'task')
    journal.bullet_complete(journal.daily_get()['bullets'][1]['id'])
    journal.monthly_add('Monthly task', 'task')
    open_tasks = journal.open_tasks()
    @py_assert2 = len(open_tasks)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(open_tasks) if 'open_tasks' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(open_tasks) else 'open_tasks',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_migrate_month(journal):
    mk = _month_key()
    journal.monthly_add('Carry forward', 'task', month = mk)
    (y, m) = map(int, mk.split('-'))
    nm = f'''{y:04d}-{m + 1:02d}''' if m < 12 else f'''{y + 1:04d}-01'''
    r = journal.migrate_month(mk, nm, dest = 'monthly')
    @py_assert0 = r['migrated']
    @py_assert3 = 1
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
    src = journal.monthly_get(mk)['bullets']
    @py_assert1 = []
    @py_assert4 = len(src)
    @py_assert7 = 1
    @py_assert6 = @py_assert4 == @py_assert7
    @py_assert0 = @py_assert6
    if @py_assert6:
        @py_assert12 = src[0]['status']
        @py_assert15 = 'migrated'
        @py_assert14 = @py_assert12 == @py_assert15
        @py_assert0 = @py_assert14
# WARNING: Decompyle incomplete


def test_migrate_month_to_future(journal):
    mk = _month_key()
    journal.monthly_add('Future bound', 'task', month = mk)
    (y, m) = map(int, mk.split('-'))
    nm = f'''{y:04d}-{m + 1:02d}''' if m < 12 else f'''{y + 1:04d}-01'''
    r = journal.migrate_month(mk, nm, dest = 'future')
    @py_assert0 = r['migrated']
    @py_assert3 = 1
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
    @py_assert2 = journal.future_list
    @py_assert5 = @py_assert2(nm)
    @py_assert7 = len(@py_assert5)
    @py_assert10 = 1
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py0)s(%(py6)s\n{%(py6)s = %(py3)s\n{%(py3)s = %(py1)s.future_list\n}(%(py4)s)\n})\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(journal) if 'journal' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(journal) else 'journal',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(nm) if 'nm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(nm) else 'nm',
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert2 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None


def test_search(journal):
    journal.daily_add('Unique zebra keyword', 'note')
    hits = journal.search('zebra')
    @py_assert1 = []
    @py_assert0 = hits
    if hits:
        @py_assert4 = 'zebra'
        @py_assert7 = hits[0]['content']
        @py_assert9 = @py_assert7.lower
        @py_assert11 = @py_assert9()
        @py_assert6 = @py_assert4 in @py_assert11
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_stats(journal):
    journal.daily_add('One', 'task')
    s = journal.stats()
    @py_assert0 = s['open_tasks']
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
    @py_assert0 = s['today']
    @py_assert4 = _today()
    @py_assert2 = @py_assert0 == @py_assert4
    if not @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py5)s\n{%(py5)s = %(py3)s()\n}',), (@py_assert0, @py_assert4)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(_today) if '_today' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_today) else '_today',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None


def test_journal_today_route(session):
    @py_assert0 = route('journal today', session)['action']
    @py_assert3 = 'journal_today'
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


def test_journal_open_tasks_route(session):
    @py_assert0 = route('what are my open tasks', session)['action']
    @py_assert3 = 'journal_open_tasks'
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


def test_journal_log_handler(assistant, data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: [
1]))
    @py_assert1 = assistant.journal
    @py_assert3 = @py_assert1.path
    @py_assert7 = 'journal'
    @py_assert9 = data_dir / @py_assert7
    @py_assert10 = 'bullet_journal.json'
    @py_assert12 = @py_assert9 / @py_assert10
    @py_assert5 = @py_assert3 == @py_assert12
    if not @py_assert5:
        @py_format13 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.journal\n}.path\n} == ((%(py6)s / %(py8)s) / %(py11)s)',), (@py_assert3, @py_assert12)) % {
            'py0': @pytest_ar._saferepr(assistant) if 'assistant' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(assistant) else 'assistant',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(data_dir) if 'data_dir' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data_dir) else 'data_dir',
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None
    @py_assert12 = None
    result = assistant.process('Log: • pytest journal scratch')
    @py_assert0 = result['ok']
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
    @py_assert0 = result['module']
    @py_assert3 = 'journal'
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
    @py_assert0 = assistant.journal.daily_get()['bullets']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_format_bullet():
    b = {
        'type': 'task',
        'status': 'open',
        'content': 'hello',
        'signifiers': [
            'important'] }
    @py_assert0 = 'hello'
    @py_assert5 = _format_bullet(b)
    @py_assert2 = @py_assert0 in @py_assert5
    if not @py_assert2:
        @py_format7 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py6)s\n{%(py6)s = %(py3)s(%(py4)s)\n}',), (@py_assert0, @py_assert5)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(_format_bullet) if '_format_bullet' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_format_bullet) else '_format_bullet',
            'py4': @pytest_ar._saferepr(b) if 'b' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(b) else 'b',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert5 = None


def test_collection_presets(journal):
    list_presets = list_presets
    preset_by_id = preset_by_id
    import jarvis.journal_presets
    presets = list_presets([])
    @py_assert2 = len(presets)
    @py_assert5 = 8
    @py_assert4 = @py_assert2 >= @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('>=',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} >= %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(presets) if 'presets' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(presets) else 'presets',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = presets[0]['active']
    @py_assert2 = not @py_assert0
    if not @py_assert2:
        @py_format3 = 'assert not %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert0 = None
    @py_assert2 = None
    p = preset_by_id('books')
    @py_assert1 = []
    @py_assert0 = p
    if p:
        @py_assert4 = p['name']
        @py_assert7 = 'Books to Read'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_daily_quote(journal):
    page = journal.daily_get('2026-06-08')
    if not page.get('quote'):
        page.get('quote')
    q = { }
    @py_assert1 = q.get
    @py_assert3 = 'text'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = q.get
    @py_assert3 = 'tradition'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = ('stoic', 'native_american', 'tai_chi')
    @py_assert7 = @py_assert5 in @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('in',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} in %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
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


def test_daily_weather(journal, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_weather_module(monkeypatch):
    format_weather_line = format_weather_line
    weather_for_day = weather_for_day
    import jarvis.journal_weather
    
    def fake_json(url, timeout = (12,)):
        if 'ip-api.com' in url:
            return {
                'status': 'success',
                'lat': 43,
                'lon': -77,
                'city': 'Rochester',
                'regionName': 'NY',
                'countryCode': 'US' }
        if None in url:
            return {
                'daily': {
                    'time': [
                        '2026-06-10'],
                    'temperature_2m_max': [
                        75.2],
                    'temperature_2m_min': [
                        58.1],
                    'weathercode': [
                        2] } }

    monkeypatch.setattr('jarvis.journal_weather._http_json', fake_json)
    monkeypatch.setenv('JARVIS_WEATHER_IP_LOOKUP', '1')
    monkeypatch.delenv('JARVIS_WEATHER_CITY', raising = False)
    monkeypatch.delenv('JARVIS_WEATHER_LAT', raising = False)
    w = weather_for_day('2026-06-10')
    @py_assert1 = []
    @py_assert0 = w
    if w:
        @py_assert4 = w['high']
        @py_assert7 = 75.2
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_daily_prompts(journal):
    page = journal.daily_get('2026-06-08')
    if not page.get('prompts'):
        page.get('prompts')
    prompts = { }
    @py_assert1 = prompts.get
    @py_assert3 = 'morning_question'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(prompts) if 'prompts' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(prompts) else 'prompts',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = prompts.get
    @py_assert3 = 'evening_question'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(prompts) if 'prompts' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(prompts) else 'prompts',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    journal.daily_set_prompts('2026-06-08', morning = 'Ready', evening = 'Tired')
    updated = journal.daily_get('2026-06-08')
    @py_assert0 = updated['prompts']['morning']
    @py_assert3 = 'Ready'
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


def test_weekly_log(journal):
    _week_key = _week_key
    import jarvis.modules.journal
    b = journal.weekly_add('Weekly task', 'task')
    @py_assert0 = b['location']
    @py_assert2 = @py_assert0.startswith
    @py_assert4 = 'weekly:'
    @py_assert6 = @py_assert2(@py_assert4)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.startswith\n}(%(py5)s)\n}' % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    page = journal.weekly_get(_week_key())
    @py_assert1 = page['bullets']()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_habit_tracker(journal):
    journal.habit_toggle('meditation', '2026-06-08')
    tracker = journal.habit_tracker('2026-06')
    med = (lambda .0: pass# WARNING: Decompyle incomplete
)(tracker['habits']())
    @py_assert0 = med['days']['2026-06-08']
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


def test_daily_photo(journal, tmp_path, monkeypatch):
    journal_mod = journal
    import jarvis.modules
    monkeypatch.setattr(journal_mod, 'JOURNAL_PHOTOS_DIR', tmp_path / 'photos')
    entry = journal.daily_add_photo('2026-06-08', 'test.png', b'\x89PNG\r\n', 'Sunset')
    @py_assert0 = entry['caption']
    @py_assert3 = 'Sunset'
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
    page = journal.daily_get('2026-06-08')
    @py_assert1 = page['photos']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    @py_assert1 = journal.daily_delete_photo
    @py_assert3 = '2026-06-08'
    @py_assert5 = entry['id']
    @py_assert7 = @py_assert1(@py_assert3, @py_assert5)
    if not @py_assert7:
        @py_format9 = 'assert %(py8)s\n{%(py8)s = %(py2)s\n{%(py2)s = %(py0)s.daily_delete_photo\n}(%(py4)s, %(py6)s)\n}' % {
            'py0': @pytest_ar._saferepr(journal) if 'journal' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(journal) else 'journal',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_bullet_remember_text(journal):
    b = journal.daily_add('Remember me', 'note')
    text = journal.bullet_remember_text(b['id'])
    @py_assert1 = []
    @py_assert0 = text
    if text:
        @py_assert4 = 'Remember me'
        @py_assert6 = @py_assert4 in text
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_journal_remember_route(session):
    @py_assert0 = route('remember journal entry', session)['action']
    @py_assert3 = 'journal_remember'
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


def test_auto_index_daily(journal):
    journal.daily_add('Indexed day', 'task', day = '2026-06-08')
    entries = journal.index_list()
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


def test_auto_index_important_bullet(journal):
    pass
# WARNING: Decompyle incomplete


def test_rebuild_auto_index(journal):
    journal.daily_add('One', 'task', day = '2026-06-01')
    journal.weekly_add('Week task', 'task')
    journal.collection_create('Test Col', 'desc')
    r = journal.rebuild_auto_index()
    @py_assert0 = r['total']
    @py_assert3 = 3
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
    @py_assert0 = r['auto']
    @py_assert3 = 3
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


def test_bullet_add_child(journal):
    parent = journal.daily_add('Parent task', 'task')
    child = journal.bullet_add_child(parent['id'], 'Sub step', 'task')
    @py_assert1 = []
    @py_assert0 = child
    if child:
        @py_assert4 = child['content']
        @py_assert7 = 'Sub step'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_bullet_schedule(journal):
    b = journal.monthly_add('Schedule me', 'task')
    scheduled = journal.bullet_schedule(b['id'], '2026-12')
    if not scheduled:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(scheduled) if 'scheduled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(scheduled) else 'scheduled' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    found = journal._find_bullet(b['id'])
    @py_assert1 = []
    @py_assert0 = found
    if found:
        @py_assert4 = found[0]['status']
        @py_assert7 = 'scheduled'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_thread_to_daily(journal):
    b = journal.monthly_add('Thread me', 'task')
    threaded = journal.bullet_thread_to_daily(b['id'], '2026-06-10')
    if not threaded:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(threaded) if 'threaded' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(threaded) else 'threaded' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    src = journal._find_bullet(b['id'])
    @py_assert1 = []
    @py_assert0 = src
    if src:
        @py_assert4 = src[0]['status']
        @py_assert7 = 'migrated'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_transfer_future_to_month(journal):
    journal.future_add('2026-12', 'Future task', 'task')
    r = journal.transfer_future_to_month('2026-12', '2026-06')
    @py_assert0 = r['migrated']
    @py_assert3 = 1
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
    @py_assert0 = journal.monthly_get('2026-06')['bullets']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_page_numbers(journal):
    page = journal.daily_get('2026-06-08', enrich = False)
    @py_assert1 = page.get
    @py_assert3 = 'page_number'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(page) if 'page' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(page) else 'page',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_wellness(journal):
    journal.daily_set_wellness('2026-06-08', mood = 4, gratitude = [
        'Sun',
        'Coffee'])
    overview = journal.wellness_overview('2026-06')
    @py_assert0 = overview['mood_average']
    @py_assert3 = 4
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
    @py_assert1 = overview['gratitude_stream']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 2
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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


def test_monthly_review(journal):
    r = journal.monthly_review_toggle('scan_monthly', '2026-06')
    @py_assert0 = r['review']['scan_monthly']
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


def test_undo(journal):
    journal.daily_add('Before undo', 'note')
    journal.daily_add('After undo', 'note')
    result = journal.undo()
    @py_assert1 = result.get
    @py_assert3 = 'ok'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    page = journal.daily_get(enrich = False)
    @py_assert1 = page['bullets']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    @py_assert0 = page['bullets'][0]['content']
    @py_assert3 = 'Before undo'
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


def test_event_time_parse(journal):
    b = journal.daily_add('14:30 Team standup', 'event', day = '2026-06-08')
    @py_assert1 = b.get
    @py_assert3 = 'time'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = '14:30'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(b) if 'b' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(b) else 'b',
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
    @py_assert0 = 'standup'
    @py_assert4 = b.get
    @py_assert6 = 'content'
    @py_assert8 = ''
    @py_assert10 = @py_assert4(@py_assert6, @py_assert8)
    @py_assert12 = @py_assert10.lower
    @py_assert14 = @py_assert12()
    @py_assert2 = @py_assert0 in @py_assert14
    if not @py_assert2:
        @py_format16 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py15)s\n{%(py15)s = %(py13)s\n{%(py13)s = %(py11)s\n{%(py11)s = %(py5)s\n{%(py5)s = %(py3)s.get\n}(%(py7)s, %(py9)s)\n}.lower\n}()\n}',), (@py_assert0, @py_assert14)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(b) if 'b' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(b) else 'b',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10),
            'py13': @pytest_ar._saferepr(@py_assert12),
            'py15': @pytest_ar._saferepr(@py_assert14) }
        @py_format18 = 'assert %(py17)s' % {
            'py17': @py_format16 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format18))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert12 = None
    @py_assert14 = None


def test_search_nested(journal):
    parent = journal.daily_add('Parent', 'task', day = '2026-06-08')
    journal.bullet_add_child(parent['id'], 'Nested zebra', 'note')
    hits = journal.search('zebra')
    @py_assert1 = hits()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_rapid_log_indent(journal):
    created = journal.parse_rapid_log('Main task\n  sub note', day = '2026-06-08')
    @py_assert2 = len(created)
    @py_assert5 = 2
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(created) if 'created' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(created) else 'created',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    page = journal.daily_get('2026-06-08', enrich = False)
    @py_assert0 = page['bullets'][0]
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'children'
    @py_assert6 = @py_assert2(@py_assert4)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n}' % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_redo(journal):
    journal.daily_add('One', 'note')
    journal.daily_add('Two', 'note')
    journal.undo()
    @py_assert1 = journal.daily_get(enrich = False)['bullets']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    journal.redo()
    @py_assert1 = journal.daily_get(enrich = False)['bullets']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 2
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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


def test_migrate_daily_open(journal):
    journal.daily_add('Carry', 'task', day = '2026-06-08')
    r = journal.migrate_daily_open('2026-06-08', '2026-06-09')
    @py_assert0 = r['migrated']
    @py_assert3 = 1
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
    src = journal.daily_get('2026-06-08', enrich = False)['bullets']
    @py_assert1 = []
    @py_assert4 = len(src)
    @py_assert7 = 1
    @py_assert6 = @py_assert4 == @py_assert7
    @py_assert0 = @py_assert6
    if @py_assert6:
        @py_assert12 = src[0]['status']
        @py_assert15 = 'migrated'
        @py_assert14 = @py_assert12 == @py_assert15
        @py_assert0 = @py_assert14
# WARNING: Decompyle incomplete


def test_weekly_review(journal):
    wk = '2026-W23'
    journal.weekly_review_toggle('scan_weekly', wk)
    r = journal.weekly_review_get(wk)
    @py_assert0 = r['review']['scan_weekly']
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
    journal.weekly_review_set_notes('Good week', wk)
    @py_assert0 = journal.weekly_review_get(wk)['review_notes']
    @py_assert3 = 'Good week'
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


def test_daily_timeline(journal):
    journal.daily_add('Team standup', 'event', day = '2026-06-08', time = '09:30')
    t = journal.daily_timeline('2026-06-08')
    @py_assert1 = t['events']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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
    @py_assert0 = t['events'][0]['time']
    @py_assert3 = '09:30'
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


def test_gratitude_prefix(journal):
    page = journal.daily_add_gratitude('2026-06-08', 'my health')
    @py_assert0 = page['gratitude'][-1]
    @py_assert3 = 'I am grateful for my health'
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
    page = journal.daily_add_gratitude('2026-06-08', 'I am grateful for coffee')
    @py_assert0 = page['gratitude'][-1]
    @py_assert3 = 'I am grateful for coffee'
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


def test_match_open_task(journal):
    journal.monthly_add('Finish taxes', 'task')
    journal.monthly_add('Buy groceries', 'task')
    (task, candidates, hint) = journal.match_open_task('schedule finish taxes to 2026-08')
    @py_assert1 = []
    @py_assert0 = task
    if task:
        @py_assert4 = 'taxes'
        @py_assert7 = task['content']
        @py_assert9 = @py_assert7.lower
        @py_assert11 = @py_assert9()
        @py_assert6 = @py_assert4 in @py_assert11
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_month_print_html_sections(journal):
    month_print_html = month_print_html
    import jarvis.journal_export
    journal.monthly_add('Monthly item', 'task')
    journal.daily_add('Daily item', 'note', day = '2026-06-08')
    html = month_print_html(journal, '2026-06')
    @py_assert0 = 'Calendar'
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Future log'
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Habit tracker'
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Weekly ·'
    @py_assert2 = @py_assert0 in html
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, html)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(html) if 'html' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(html) else 'html' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert2 = 'status-'
    @py_assert4 = @py_assert2 in html
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'Daily item'
        @py_assert11 = @py_assert9 in html
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete


def test_concurrent_daily_adds_persist(tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_habit_streak(journal, monkeypatch):
    monkeypatch.setattr('jarvis.modules.journal._today', (lambda : '2026-06-08'))
    journal.habit_toggle('meditation', '2026-06-06')
    journal.habit_toggle('meditation', '2026-06-07')
    journal.habit_toggle('meditation', '2026-06-08')
    tracker = journal.habit_tracker('2026-06')
    med = (lambda .0: pass# WARNING: Decompyle incomplete
)(tracker['habits']())
    @py_assert0 = med['streak']
    @py_assert3 = 3
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


def test_collection_preset_created_flag(journal):
    preset_by_id = preset_by_id
    import jarvis.journal_presets
    preset = preset_by_id('books')
    if not preset:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(preset) if 'preset' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(preset) else 'preset' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    journal.collection_create(preset['name'], preset['description'])
    existed = preset['name'] in journal.collection_list()
    if not existed:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(existed) if 'existed' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(existed) else 'existed' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    col = journal.collection_create(preset['name'], preset['description'])
    @py_assert0 = col['name']
    @py_assert3 = preset['name']
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


def test_bullet_id_is_full_uuid(journal):
    b = journal.daily_add('Unique id test', 'note')
    @py_assert1 = b['id']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 32
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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


def test_journal_export_pdf_smoke(chat_app, journal, monkeypatch, tmp_path):
    DATA_DIR = DATA_DIR
    import jarvis.config
    monkeypatch.setattr('jarvis.extensions.journal.api.DATA_DIR', tmp_path)
    (tmp_path / 'exports').mkdir(parents = True, exist_ok = True)
    journal.daily_add('PDF smoke', 'task', day = '2026-06-08')
    
    def fake_pdf(j, dest, month):
        dest.parent.mkdir(parents = True, exist_ok = True)
        dest.write_bytes(b'%PDF-1.4\n% journal test')

    monkeypatch.setattr('jarvis.journal_export.export_month_pdf', fake_pdf)
    res = chat_app.get('/api/journal/export/pdf?month=2026-06')
    @py_assert1 = res.status_code
    @py_assert4 = 200
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert0 = res.content[:4]
    @py_assert3 = b'%PDF'
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


def test_journal_brain_feed_extract_and_store(assistant, monkeypatch):
    extract_and_store = extract_and_store
    import jarvis.journal_learning
    monkeypatch.setattr('jarvis.journal_learning.extract_journal_learnings', (lambda : [
'User decided to ship the journal brain feed feature today.']))
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: [
1]))
    result = extract_and_store(assistant.memory, 'Shipped journal brain feed after completing migrate wizard and habit streaks.', project = 'main', day = '2026-06-08')
    @py_assert0 = result['ok']
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
    @py_assert1 = result['facts']
    @py_assert3 = len(@py_assert1)
    @py_assert6 = 1
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
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


def test_journal_merge_preserves_both_writes(tmp_path):
    BulletJournal = BulletJournal
    import jarvis.modules.journal
    path = tmp_path / 'bullet_journal.json'
    a = BulletJournal(path = path)
    a.daily_add('From A', 'task', day = '2026-06-08')
    b = BulletJournal(path = path)
    b._data = b._load()
    b.daily_add('From B', 'task', day = '2026-06-08')
    final = BulletJournal(path = path)
    page = final.daily_get('2026-06-08', enrich = False)
# WARNING: Decompyle incomplete

