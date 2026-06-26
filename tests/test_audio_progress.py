# Source Generated with Decompyle++
# File: test_audio_progress.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for audio job persistence and GPU serialization.'''
import builtins as @py_builtins

rewrite
from jarvis import audio_progress
import _pytest.assertion.rewrite, assertion

def test_audio_job_persist_and_reload(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr(ap, 'DATA_DIR', data_dir)
    monkeypatch.setattr(ap, '_STATE_FILE', data_dir / 'audio_jobs_state.json')
    ap._jobs.clear()
    job_id = ap.start_job('Test song')
    ap.update_job(job_id, 50, 'Halfway')
    ap.finish_job(job_id, result = {
        'audio_path': '/tmp/x.wav' })
    ap._jobs.clear()
    ap._load_state()
    job = ap.get_job(job_id)
    @py_assert2 = None
    @py_assert1 = job is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (job, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(job) if 'job' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(job) else 'job',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = job['done']
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
    @py_assert0 = job['result']['audio_path']
    @py_assert3 = '/tmp/x.wav'
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


def test_audio_gpu_slot_serializes():
    audio_gpu_slot = audio_gpu_slot
    import jarvis.audio_work
    audio_gpu_slot('a')
    @py_assert0 = True
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass

