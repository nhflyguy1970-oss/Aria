# Source Generated with Decompyle++
# File: test_daemon_watchdog.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Daemon and watchdog reliability tests.'''
import builtins as @py_builtins

rewrite
import subprocess = import _pytest.assertion.rewrite, assertion
import urllib.error as urllib
from unittest.mock import MagicMock, patch
import pytest
from jarvis.watchdog import ServerWatchdog, _media_work_active

def test_media_work_active_false_when_idle(monkeypatch):
    monkeypatch.setattr('jarvis.media_jobs.has_active_work_persisted', (lambda : False))
    monkeypatch.setattr('jarvis.media_jobs.has_active_work', (lambda : False))
    monkeypatch.setattr('jarvis.media_jobs.busy_state', (lambda : {
'busy': False,
'pending': 0 }))
    monkeypatch.setattr('jarvis.restart_flag.controlled_restart_active', (lambda : False))
    @py_assert1 = _media_work_active()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_media_work_active) if '_media_work_active' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_media_work_active) else '_media_work_active',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_media_work_active_true_when_busy(monkeypatch):
    monkeypatch.setattr('jarvis.media_jobs.has_active_work_persisted', (lambda : False))
    monkeypatch.setattr('jarvis.media_jobs.has_active_work', (lambda : True))
    monkeypatch.setattr('jarvis.media_jobs.busy_state', (lambda : {
'busy': True,
'pending': 0 }))
    monkeypatch.setattr('jarvis.restart_flag.controlled_restart_active', (lambda : False))
    @py_assert1 = _media_work_active()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_media_work_active) if '_media_work_active' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_media_work_active) else '_media_work_active',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_watchdog_does_not_restart_when_media_active(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_daemon_start_server_health_timeout(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete

