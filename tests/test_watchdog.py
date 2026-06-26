# Source Generated with Decompyle++
# File: test_watchdog.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for jarvis.watchdog.'''
import builtins as @py_builtins

rewrite
from unittest.mock import MagicMock, patch
patch = patch
import _pytest.assertion.rewrite, assertion
from jarvis.watchdog import ServerWatchdog, _media_work_active

def test_healthy_when_live_returns_200():
    wd = ServerWatchdog(failures_before_restart = 1)
    mock_urlopen = patch('urllib.request.urlopen')
    mock_urlopen.return_value.__enter__.return_value.status = 200
    @py_assert1 = wd._healthy
    @py_assert3 = @py_assert1()
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s._healthy\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(wd) if 'wd' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wd) else 'wd',
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
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_restart_after_consecutive_failures():
    pass
# WARNING: Decompyle incomplete


def test_no_restart_while_media_busy():
    pass
# WARNING: Decompyle incomplete


def test_media_work_active_true_when_heavy_api():
    begin_heavy = begin_heavy
    end_heavy = end_heavy
    import jarvis.request_activity
    begin_heavy()
    
    try:
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
        end_heavy()
        return None
    except:
        end_heavy()


