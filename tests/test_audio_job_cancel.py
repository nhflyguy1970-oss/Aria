# Source Generated with Decompyle++
# File: test_audio_job_cancel.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Audio job cancellation.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.audio_progress import JobCancelled, cancel_job, finish_job, start_job, update_job

def test_cancel_job_stops_updates():
    job_id = start_job('test')
    @py_assert2 = cancel_job(job_id)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(cancel_job) if 'cancel_job' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cancel_job) else 'cancel_job',
            'py1': @pytest_ar._saferepr(job_id) if 'job_id' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(job_id) else 'job_id',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    pytest.raises(JobCancelled)
    update_job(job_id, 50, 'mid')
    None(None, None)
    finish_job(job_id, error = 'Cancelled by user')
    return None
    with None:
        if not None:
            pass
    continue

