# Source Generated with Decompyle++
# File: test_git_util.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for git_util.'''
import builtins as @py_builtins

rewrite
from jarvis import git_util
import _pytest.assertion.rewrite, assertion

def test_status_not_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(git_util, 'PROJECT_ROOT', tmp_path)
    @py_assert0 = 'Not a git repository'
    @py_assert4 = git_util.status
    @py_assert7 = @py_assert4(tmp_path)
    @py_assert2 = @py_assert0 in @py_assert7
    if not @py_assert2:
        @py_format9 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py8)s\n{%(py8)s = %(py5)s\n{%(py5)s = %(py3)s.status\n}(%(py6)s)\n}',), (@py_assert0, @py_assert7)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(git_util) if 'git_util' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(git_util) else 'git_util',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py6': @pytest_ar._saferepr(tmp_path) if 'tmp_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tmp_path) else 'tmp_path',
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert7 = None


def test_status_in_repo(tmp_path, monkeypatch):
    import subprocess
    subprocess.run([
        'git',
        'init'], cwd = tmp_path, check = True, capture_output = True)
    monkeypatch.setattr(git_util, 'PROJECT_ROOT', tmp_path)
    out = git_util.status(tmp_path)
    @py_assert1 = []
    @py_assert2 = 'main'
    @py_assert4 = @py_assert2 in out
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert9 = 'master'
        @py_assert11 = @py_assert9 in out
        @py_assert0 = @py_assert11
        if not @py_assert11:
            @py_assert16 = 'No commits'
            @py_assert18 = @py_assert16 in out
            @py_assert0 = @py_assert18
            if not @py_assert18:
                @py_assert0 = out
# WARNING: Decompyle incomplete

