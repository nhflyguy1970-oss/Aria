# Source Generated with Decompyle++
# File: test_coding_jobs.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for coding job queue.'''
import builtins as @py_builtins

rewrite
import time = import _pytest.assertion.rewrite, assertion
from jarvis.coding_jobs import get_job, job_stats, submit

def test_coding_job_completes():
    pass
# WARNING: Decompyle incomplete


def test_coding_job_stats():
    stats = job_stats()
    @py_assert0 = 'busy'
    @py_assert2 = @py_assert0 in stats
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, stats)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(stats) if 'stats' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(stats) else 'stats' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'completed'
    @py_assert2 = @py_assert0 in stats
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, stats)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(stats) if 'stats' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(stats) else 'stats' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

