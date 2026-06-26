# Source Generated with Decompyle++
# File: test_web_search_auto.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for auto web search heuristics.'''
import builtins as @py_builtins

rewrite
from jarvis import web_search
import _pytest.assertion.rewrite, assertion

def test_should_auto_search_questions():
    @py_assert1 = web_search.should_auto_search
    @py_assert3 = 'Who is the CEO of Nvidia?'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_auto_search\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(web_search) if 'web_search' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(web_search) else 'web_search',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = web_search.should_auto_search
    @py_assert3 = 'What is the latest news about Linux?'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_auto_search\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(web_search) if 'web_search' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(web_search) else 'web_search',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_should_not_auto_search_coding():
    @py_assert1 = web_search.should_auto_search
    @py_assert3 = 'fix coding/main.py'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_auto_search\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(web_search) if 'web_search' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(web_search) else 'web_search',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert1 = web_search.should_auto_search
    @py_assert3 = 'search the web for cats'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_auto_search\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(web_search) if 'web_search' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(web_search) else 'web_search',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_format_results_for_llm():
    hits = [
        {
            'title': 'A',
            'url': 'https://a.test',
            'snippet': 'hello' }]
    text = web_search.format_results_for_llm(hits)
    @py_assert0 = '[1]'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'https://a.test'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

