# Source Generated with Decompyle++
# File: test_logging_config.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for centralized logging setup.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import logging = import _pytest.assertion.rewrite, assertion
import pytest
_isolate_logging = (lambda tmp_path, monkeypatch: monkeypatch.setenv('JARVIS_LOG_DIR', str(tmp_path / 'logs'))monkeypatch.setenv('JARVIS_LOG_LEVEL', 'DEBUG')lc = logging_configimport jarvis.logging_configmonkeypatch.setattr(lc, '_CONFIGURED', False)root = logging.getLogger()for handler in list(root.handlers):
root.removeHandler(handler))()

def test_setup_logging_writes_to_data_logs(tmp_path, monkeypatch):
    lc = logging_config
    import jarvis.logging_config
    log_dir = tmp_path / 'logs'
    monkeypatch.setenv('JARVIS_LOG_DIR', str(log_dir))
    lc.setup_logging(force = True)
    log = logging.getLogger('jarvis.test')
    log.info('hello from test')
    log_file = log_dir / 'jarvis.log'
    @py_assert1 = log_file.is_file
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(log_file) if 'log_file' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(log_file) else 'log_file',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert0 = 'hello from test'
    @py_assert4 = log_file.read_text
    @py_assert6 = 'utf-8'
    @py_assert8 = @py_assert4(encoding = @py_assert6)
    @py_assert2 = @py_assert0 in @py_assert8
    if not @py_assert2:
        @py_format10 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py9)s\n{%(py9)s = %(py5)s\n{%(py5)s = %(py3)s.read_text\n}(encoding=%(py7)s)\n}',), (@py_assert0, @py_assert8)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(log_file) if 'log_file' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(log_file) else 'log_file',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None


def test_setup_logging_idempotent(tmp_path, monkeypatch):
    lc = logging_config
    import jarvis.logging_config
    lc.setup_logging(force = True)
    count = len(logging.getLogger().handlers)
    lc.setup_logging()
    @py_assert2 = logging.getLogger
    @py_assert4 = @py_assert2()
    @py_assert6 = @py_assert4.handlers
    @py_assert8 = len(@py_assert6)
    @py_assert10 = @py_assert8 == count
    if not @py_assert10:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert10,), ('%(py9)s\n{%(py9)s = %(py0)s(%(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py1)s.getLogger\n}()\n}.handlers\n})\n} == %(py11)s',), (@py_assert8, count)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(logging) if 'logging' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(logging) else 'logging',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(count) if 'count' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(count) else 'count' }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None


def test_request_id_in_log_record(tmp_path, monkeypatch):
    lc = logging_config
    import jarvis.logging_config
    lc.setup_logging(force = True)
    lc.set_request_id('req-abc')
    record = logging.LogRecord(name = 'jarvis.test', level = logging.INFO, pathname = __file__, lineno = 1, msg = 'with id', args = (), exc_info = None)
    filt = lc.RequestIdFilter()
    @py_assert1 = filt.filter
    @py_assert4 = @py_assert1(record)
    @py_assert7 = True
    @py_assert6 = @py_assert4 is @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('is',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py2)s\n{%(py2)s = %(py0)s.filter\n}(%(py3)s)\n} is %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(filt) if 'filt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(filt) else 'filt',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(record) if 'record' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(record) else 'record',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    @py_assert1 = record.request_id
    @py_assert4 = 'req-abc'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.request_id\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(record) if 'record' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(record) else 'record',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    lc.clear_request_id()

