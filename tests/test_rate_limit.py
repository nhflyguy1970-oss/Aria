# Source Generated with Decompyle++
# File: test_rate_limit.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for per-IP rate limiting middleware.'''
import builtins as @py_builtins

rewrite
from unittest.mock import MagicMock
import _pytest.assertion.rewrite, assertion
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from jarvis import rate_limit

async def _protected(request):
    pass
# WARNING: Decompyle incomplete


def _req(ip = None, path = None, headers = None):
    req = MagicMock()
    req.url.path = path
    req.client.host = ip
    if not headers:
        headers
    req.headers = { }
    return req

_clear_hits = (lambda : pass# WARNING: Decompyle incomplete
)()
limited_app = (lambda monkeypatch: monkeypatch.setenv('JARVIS_RATE_LIMIT', '1')monkeypatch.setenv('JARVIS_TRUST_PROXY', '1')monkeypatch.setattr(rate_limit, '_MAX_REQUESTS', 5)app = Starlette(routes = [
Route('/api/chat', _protected),
Route('/api/health', _protected),
Route('/api/live', _protected),
Route('/api/lan', _protected),
Route('/api/ping', _protected)])app.add_middleware(rate_limit.RateLimitMiddleware)TestClient(app))()

def test_rate_limit_disabled_explicit(monkeypatch):
    monkeypatch.setenv('JARVIS_RATE_LIMIT', '0')
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    @py_assert1 = rate_limit.rate_limit_enabled
    @py_assert3 = @py_assert1()
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.rate_limit_enabled\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
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


def test_rate_limit_enabled_explicit(monkeypatch):
    monkeypatch.setenv('JARVIS_RATE_LIMIT', '1')
    monkeypatch.setenv('JARVIS_HOST', '127.0.0.1')
    @py_assert1 = rate_limit.rate_limit_enabled
    @py_assert3 = @py_assert1()
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.rate_limit_enabled\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
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


def test_rate_limit_auto_on_lan_bind(monkeypatch):
    monkeypatch.delenv('JARVIS_RATE_LIMIT', raising = False)
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    @py_assert1 = rate_limit.rate_limit_enabled
    @py_assert3 = @py_assert1()
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.rate_limit_enabled\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
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


def test_rate_limit_auto_off_localhost(monkeypatch):
    monkeypatch.delenv('JARVIS_RATE_LIMIT', raising = False)
    monkeypatch.setenv('JARVIS_HOST', '127.0.0.1')
    @py_assert1 = rate_limit.rate_limit_enabled
    @py_assert3 = @py_assert1()
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.rate_limit_enabled\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
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


def test_loopback_exempt(monkeypatch):
    monkeypatch.setenv('JARVIS_RATE_LIMIT', '1')
    @py_assert1 = rate_limit._is_loopback
    @py_assert3 = '127.0.0.1'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_loopback\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = rate_limit._is_loopback
    @py_assert3 = '127.0.0.2'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_loopback\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = rate_limit._is_loopback
    @py_assert3 = '::1'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_loopback\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = rate_limit._is_loopback
    @py_assert3 = '192.168.1.1'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_loopback\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(rate_limit) if 'rate_limit' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rate_limit) else 'rate_limit',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_middleware_loopback_exempt(monkeypatch):
    monkeypatch.setenv('JARVIS_RATE_LIMIT', '1')
    monkeypatch.setattr(rate_limit, '_MAX_REQUESTS', 5)
    app = Starlette(routes = [
        Route('/api/chat', _protected)])
    app.add_middleware(rate_limit.RateLimitMiddleware)
    client = TestClient(app, client = ('127.0.0.1', 50000))
    for _ in range(10):
        res = client.get('/api/chat')
        @py_assert1 = res.status_code
        @py_assert4 = 200
        @py_assert3 = @py_assert1 == @py_assert4
        if not @py_assert3:
            @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
                'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
                'py2': @pytest_ar._saferepr(@py_assert1),
                'py5': @pytest_ar._saferepr(@py_assert4) }
            @py_format8 = 'assert %(py7)s' % {
                'py7': @py_format6 }
            raise AssertionError(@pytest_ar._format_explanation(@py_format8))
        @py_assert1 = None
        @py_assert3 = None
        @py_assert4 = None


def test_middleware_burst_429_with_trusted_proxy(limited_app):
    headers = {
        'X-Forwarded-For': '192.168.1.50' }
    for _ in range(5):
        res = limited_app.get('/api/chat', headers = headers)
        @py_assert1 = res.status_code
        @py_assert4 = 200
        @py_assert3 = @py_assert1 == @py_assert4
        if not @py_assert3:
            @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
                'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
                'py2': @pytest_ar._saferepr(@py_assert1),
                'py5': @pytest_ar._saferepr(@py_assert4) }
            @py_format8 = 'assert %(py7)s' % {
                'py7': @py_format6 }
            raise AssertionError(@pytest_ar._format_explanation(@py_format8))
        @py_assert1 = None
        @py_assert3 = None
        @py_assert4 = None
    res = limited_app.get('/api/chat', headers = headers)
    @py_assert1 = res.status_code
    @py_assert4 = 429
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert0 = res.json()['ok']
    @py_assert3 = False
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


def test_exempt_paths_not_limited(limited_app):
    '''Health/live/lan/ping paths skip rate limit even for remote IPs.'''
    headers = {
        'X-Forwarded-For': '192.168.1.50' }
    for path in ('/api/health', '/api/live', '/api/lan', '/api/ping'):
        for _ in range(10):
            res = limited_app.get(path, headers = headers)
            @py_assert1 = res.status_code
            @py_assert4 = 429
            @py_assert3 = @py_assert1 != @py_assert4
            if not @py_assert3:
                @py_format6 = @pytest_ar._call_reprcompare(('!=',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} != %(py5)s',), (@py_assert1, @py_assert4)) % {
                    'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
                    'py2': @pytest_ar._saferepr(@py_assert1),
                    'py5': @pytest_ar._saferepr(@py_assert4) }
                @py_format8 = (@pytest_ar._format_assertmsg(path) + '\n>assert %(py7)s') % {
                    'py7': @py_format6 }
                raise AssertionError(@pytest_ar._format_explanation(@py_format8))
            @py_assert1 = None
            @py_assert3 = None
            @py_assert4 = None

