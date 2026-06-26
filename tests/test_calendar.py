# Source Generated with Decompyle++
# File: test_calendar.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Calendar store and tab tests.'''
import builtins as @py_builtins

rewrite
from datetime import date
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.calendar_store import load_work_schedule, save_work_schedule, work_blocks_for_day

def test_work_schedule_roundtrip(data_dir, monkeypatch):
    path = data_dir / 'calendar_work_schedule.json'
    monkeypatch.setattr('jarvis.calendar_store.SCHEDULE_FILE', path)
    saved = save_work_schedule({
        'enabled': True,
        'days': {
            'mon': [
                {
                    'start': '08:00',
                    'end': '16:00',
                    'label': 'Office' }],
            'sat': [] } })
    @py_assert0 = saved['days']['mon'][0]['label']
    @py_assert3 = 'Office'
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
    loaded = load_work_schedule()
    @py_assert0 = loaded['days']['mon'][0]['start']
    @py_assert3 = '08:00'
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


def test_work_blocks_for_day(data_dir, monkeypatch):
    path = data_dir / 'calendar_work_schedule.json'
    monkeypatch.setattr('jarvis.calendar_store.SCHEDULE_FILE', path)
    save_work_schedule({
        'enabled': True,
        'days': {
            'fri': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }] } })
    blocks = work_blocks_for_day(date(2026, 6, 19))
    @py_assert2 = len(blocks)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(blocks) if 'blocks' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(blocks) else 'blocks',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = blocks[0]['label']
    @py_assert3 = 'Work'
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


def test_fetch_events_for_month_parses():
    _parse_ics_event_block = _parse_ics_event_block
    import jarvis.calendar_ics
    chunk = 'SUMMARY:Team standup\nDTSTART:20260621T090000\n'
    (d, summary, time_str) = _parse_ics_event_block(chunk)
    @py_assert3 = 2026
    @py_assert5 = 6
    @py_assert7 = 21
    @py_assert9 = date(@py_assert3, @py_assert5, @py_assert7)
    @py_assert1 = d == @py_assert9
    if not @py_assert1:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py10)s\n{%(py10)s = %(py2)s(%(py4)s, %(py6)s, %(py8)s)\n}',), (d, @py_assert9)) % {
            'py0': @pytest_ar._saferepr(d) if 'd' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(d) else 'd',
            'py2': @pytest_ar._saferepr(date) if 'date' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(date) else 'date',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert2 = 'Team standup'
    @py_assert1 = summary == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (summary, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(summary) if 'summary' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(summary) else 'summary',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert2 = '09:00'
    @py_assert1 = time_str == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (time_str, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(time_str) if 'time_str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(time_str) else 'time_str',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None

