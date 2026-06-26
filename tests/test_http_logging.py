# Source Generated with Decompyle++
# File: test_http_logging.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''HTTP request logging middleware.'''
import builtins as @py_builtins

rewrite
from jarvis.http_logging import RequestLoggingMiddleware
import _pytest.assertion.rewrite, assertion

def test_request_logging_middleware_has_logger():
    mod = http_logging
    import jarvis.http_logging
    @py_assert2 = 'logger'
    @py_assert4 = hasattr(mod, @py_assert2)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py1)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(hasattr) if 'hasattr' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hasattr) else 'hasattr',
            'py1': @pytest_ar._saferepr(mod) if 'mod' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(mod) else 'mod',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert1 = mod.logger
    @py_assert3 = @py_assert1.name
    @py_assert6 = 'jarvis.http'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.logger\n}.name\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(mod) if 'mod' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(mod) else 'mod',
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
    @py_assert2 = None
    @py_assert1 = RequestLoggingMiddleware is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (RequestLoggingMiddleware, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(RequestLoggingMiddleware) if 'RequestLoggingMiddleware' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(RequestLoggingMiddleware) else 'RequestLoggingMiddleware',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None

