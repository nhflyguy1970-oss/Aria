# Source Generated with Decompyle++
# File: test_prompt_refresh.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Prompt refresh skip tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.handlers.registry import action_needs_prompt_refresh
import _pytest.assertion.rewrite, assertion

def test_fly_status_skips_prompt_refresh():
    @py_assert1 = 'fly_status'
    @py_assert3 = action_needs_prompt_refresh(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(action_needs_prompt_refresh) if 'action_needs_prompt_refresh' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(action_needs_prompt_refresh) else 'action_needs_prompt_refresh',
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


def test_chat_needs_prompt_refresh():
    @py_assert1 = 'chat'
    @py_assert3 = action_needs_prompt_refresh(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(action_needs_prompt_refresh) if 'action_needs_prompt_refresh' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(action_needs_prompt_refresh) else 'action_needs_prompt_refresh',
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

