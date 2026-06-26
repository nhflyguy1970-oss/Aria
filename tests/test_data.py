# Source Generated with Decompyle++
# File: test_data.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Data module and routing tests.'''
import builtins as @py_builtins

rewrite
import csv = import _pytest.assertion.rewrite, assertion
from pathlib import Path
import pytest
from jarvis.modules.data import DataEngine, parse_chart_request
from jarvis.router import route
from jarvis.session import SessionContext
session = (lambda : SessionContext())()

def _write_csv(path = None, rows = None):
    path.parent.mkdir(parents = True, exist_ok = True)
    f = open(path, 'w', newline = '', encoding = 'utf-8')
    w = csv.DictWriter(f, fieldnames = list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_data_load_route(session):
    att = {
        'path': '/tmp/sales.csv',
        'kind': 'data' }
    intent = route('', session, att)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_load'
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


def test_data_query_follow_up(session):
    session.last_data_path = '/tmp/sales.csv'
    intent = route('How many rows are there?', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_query'
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


def test_data_export_route(session):
    session.last_data_path = 'data/sales.csv'
    intent = route('export results to csv', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_export'
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


def test_data_export_pdf_route(session):
    session.last_data_path = 'data/sales.csv'
    intent = route('export report to pdf', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_export'
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


def test_data_clean_route(session):
    session.last_data_path = 'data/sales.csv'
    intent = route('clean drop duplicates', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_clean'
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


def test_data_chart_route(session):
    session.last_data_path = 'data/sales.csv'
    intent = route('plot revenue pie chart', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'data_chart'
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


def test_parse_chart_request():
    spec = parse_chart_request('plot revenue as pie chart')
    @py_assert0 = spec['chart_type']
    @py_assert3 = 'pie'
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


def test_compute_row_count(assistant, data_dir):
    csv_path = data_dir / 'uploads' / 'nums.csv'
    _write_csv(csv_path, [
        {
            'a': '1',
            'b': '2' },
        {
            'a': '3',
            'b': '4' },
        {
            'a': '5',
            'b': '6' }])
    assistant.data.load_dataset(str(csv_path))
    answer = assistant.data.compute_answer('How many rows are there?')
    @py_assert1 = []
    @py_assert0 = answer
    if answer:
        @py_assert4 = '3'
        @py_assert6 = @py_assert4 in answer
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_data_load_handler(assistant, data_dir):
    csv_path = data_dir / 'uploads' / 'sales.csv'
    _write_csv(csv_path, [
        {
            'item': 'apple',
            'qty': '10' },
        {
            'item': 'pear',
            'qty': '5' }])
    result = assistant.process('', attachment = {
        'path': str(csv_path),
        'kind': 'data',
        'name': 'sales.csv' })
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
    @py_assert3 = 'data'
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
    @py_assert1 = result.get
    @py_assert3 = 'data_preview'
    @py_assert5 = { }
    @py_assert7 = @py_assert1(@py_assert3, @py_assert5)
    @py_assert9 = @py_assert7.get
    @py_assert11 = 'row_count'
    @py_assert13 = @py_assert9(@py_assert11)
    @py_assert16 = 2
    @py_assert15 = @py_assert13 == @py_assert16
    if not @py_assert15:
        @py_format18 = @pytest_ar._call_reprcompare(('==',), (@py_assert15,), ('%(py14)s\n{%(py14)s = %(py10)s\n{%(py10)s = %(py8)s\n{%(py8)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s, %(py6)s)\n}.get\n}(%(py12)s)\n} == %(py17)s',), (@py_assert13, @py_assert16)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11),
            'py14': @pytest_ar._saferepr(@py_assert13),
            'py17': @pytest_ar._saferepr(@py_assert16) }
        @py_format20 = 'assert %(py19)s' % {
            'py19': @py_format18 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format20))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert13 = None
    @py_assert15 = None
    @py_assert16 = None


def test_data_query_average(assistant, data_dir):
    csv_path = data_dir / 'uploads' / 'prices.csv'
    _write_csv(csv_path, [
        {
            'price': '10' },
        {
            'price': '20' },
        {
            'price': '30' }])
    assistant.data.load_dataset(str(csv_path))
    assistant.session.last_data_path = str(csv_path)
    result = assistant.process('What is the average price?')
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
    @py_assert0 = '20'
    @py_assert3 = result['message']
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


def test_data_export(assistant, data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.modules.data.EXPORT_DIR', data_dir / 'exports')
    csv_path = data_dir / 'uploads' / 'out.csv'
    _write_csv(csv_path, [
        {
            'x': '1' }])
    assistant.data.load_dataset(str(csv_path))
    session = assistant.session
    session.last_data_path = str(csv_path)
    result = assistant.process('export to json')
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
    @py_assert1 = result.get
    @py_assert3 = 'export_path'
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


def test_streaming_csv_load(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.modules.data.STREAM_THRESHOLD_BYTES', 1)
    engine = DataEngine()
    csv_path = data_dir / 'uploads' / 'big.csv'
# WARNING: Decompyle incomplete


def test_streaming_average(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.modules.data.STREAM_THRESHOLD_BYTES', 1)
    engine = DataEngine()
    csv_path = data_dir / 'uploads' / 'avg.csv'
# WARNING: Decompyle incomplete


def test_streaming_export_copy(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.modules.data.STREAM_THRESHOLD_BYTES', 1)
    monkeypatch.setattr('jarvis.modules.data.EXPORT_DIR', data_dir / 'exports')
    engine = DataEngine()
    csv_path = data_dir / 'uploads' / 'copy.csv'
    _write_csv(csv_path, [
        {
            'x': '1' },
        {
            'x': '2' },
        {
            'x': '3' }])
    engine.load_dataset(str(csv_path))
    out = engine.export(fmt = 'csv')
    @py_assert1 = out.startswith
    @py_assert3 = 'ERROR'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert2 = Path(out)
    @py_assert4 = @py_assert2.read_text
    @py_assert6 = 'utf-8'
    @py_assert8 = @py_assert4(encoding = @py_assert6)
    @py_assert10 = @py_assert8.count
    @py_assert12 = '\n'
    @py_assert14 = @py_assert10(@py_assert12)
    @py_assert17 = 3
    @py_assert16 = @py_assert14 >= @py_assert17
    if not @py_assert16:
        @py_format19 = @pytest_ar._call_reprcompare(('>=',), (@py_assert16,), ('%(py15)s\n{%(py15)s = %(py11)s\n{%(py11)s = %(py9)s\n{%(py9)s = %(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}.read_text\n}(encoding=%(py7)s)\n}.count\n}(%(py13)s)\n} >= %(py18)s',), (@py_assert14, @py_assert17)) % {
            'py0': @pytest_ar._saferepr(Path) if 'Path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(Path) else 'Path',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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


def test_export_pdf(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.modules.data.EXPORT_DIR', data_dir / 'exports')
    engine = DataEngine()
    csv_path = data_dir / 'uploads' / 'report.csv'
    _write_csv(csv_path, [
        {
            'item': 'apple',
            'qty': '10',
            'price': '1.5' },
        {
            'item': 'pear',
            'qty': '5',
            'price': '2.0' },
        {
            'item': 'banana',
            'qty': '3',
            'price': '0.9' }])
    engine.load_dataset(str(csv_path))
    out = engine.export(fmt = 'pdf')
    @py_assert1 = out.startswith
    @py_assert3 = 'ERROR'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = (@pytest_ar._format_assertmsg(out) + '\n>assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}') % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    pdf = Path(out)
    @py_assert1 = pdf.exists
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.exists\n}()\n}' % {
            'py0': @pytest_ar._saferepr(pdf) if 'pdf' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pdf) else 'pdf',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert0 = pdf.read_bytes()[:4]
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


def test_data_clean_duplicates(assistant, data_dir):
    csv_path = data_dir / 'uploads' / 'dup.csv'
    _write_csv(csv_path, [
        {
            'id': '1' },
        {
            'id': '1' },
        {
            'id': '2' }])
    assistant.data.load_dataset(str(csv_path))
    assistant.session.last_data_path = str(csv_path)
    result = assistant.process('clean drop duplicates')
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
    @py_assert0 = assistant.data.dataset['row_count']
    @py_assert3 = 2
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

