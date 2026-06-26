# Source Generated with Decompyle++
# File: test_media_jobs.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for media job queue.'''
import builtins as @py_builtins

rewrite
from jarvis.media_jobs import ACTION_LABELS, QUEUED_ACTIONS, busy_state, cancel_job, get_job, is_busy, submit
QUEUED_ACTIONS = QUEUED_ACTIONS
busy_state = busy_state
cancel_job = cancel_job
get_job = get_job
is_busy = is_busy
submit = submit
import _pytest.assertion.rewrite, assertion

def test_submit_and_complete():
    pass
# WARNING: Decompyle incomplete


def test_busy_state_tracks_queue():
    state = busy_state()
    @py_assert0 = 'busy'
    @py_assert2 = @py_assert0 in state
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, state)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(state) if 'state' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(state) else 'state' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'pending'
    @py_assert2 = @py_assert0 in state
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, state)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(state) if 'state' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(state) else 'state' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_queued_actions_cover_media():
    @py_assert0 = 'generate_image'
    @py_assert2 = @py_assert0 in QUEUED_ACTIONS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, QUEUED_ACTIONS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(QUEUED_ACTIONS) if 'QUEUED_ACTIONS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(QUEUED_ACTIONS) else 'QUEUED_ACTIONS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'generate_video'
    @py_assert2 = @py_assert0 in QUEUED_ACTIONS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, QUEUED_ACTIONS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(QUEUED_ACTIONS) if 'QUEUED_ACTIONS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(QUEUED_ACTIONS) else 'QUEUED_ACTIONS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = ACTION_LABELS['generate_video']
    @py_assert3 = 'Video render'
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


def test_cancel_before_start():
    pass
# WARNING: Decompyle incomplete


def test_cancel_active_job_interrupts():
    pass
# WARNING: Decompyle incomplete

