# Source Generated with Decompyle++
# File: test_chat_cancel.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Chat stream cancellation tokens.'''
import builtins as @py_builtins

rewrite
from jarvis.chat_cancel import begin, cancel, finish, is_cancelled
cancel = cancel
finish = finish
is_cancelled = is_cancelled
import _pytest.assertion.rewrite, assertion

def test_chat_cancel_lifecycle():
    rid = 'test-req-1'
    begin(rid)
    @py_assert2 = is_cancelled(rid)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_cancelled) if 'is_cancelled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_cancelled) else 'is_cancelled',
            'py1': @pytest_ar._saferepr(rid) if 'rid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rid) else 'rid',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None
    cancel(rid)
    @py_assert2 = is_cancelled(rid)
    if not @py_assert2:
        @py_format4 = 'assert %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_cancelled) if 'is_cancelled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_cancelled) else 'is_cancelled',
            'py1': @pytest_ar._saferepr(rid) if 'rid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rid) else 'rid',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format4))
    @py_assert2 = None
    finish(rid)
    @py_assert2 = is_cancelled(rid)
    @py_assert4 = not @py_assert2
    if not @py_assert4:
        @py_format5 = 'assert not %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_cancelled) if 'is_cancelled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_cancelled) else 'is_cancelled',
            'py1': @pytest_ar._saferepr(rid) if 'rid' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rid) else 'rid',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert2 = None
    @py_assert4 = None

