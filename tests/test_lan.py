# Source Generated with Decompyle++
# File: test_lan.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''LAN access and API key auth tests.'''
import builtins as @py_builtins

rewrite
from unittest.mock import MagicMock
import _pytest.assertion.rewrite, assertion
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from jarvis.auth import APIKeyMiddleware, api_key_enabled, api_key_required_for, check_key, is_local_client
from jarvis.lan import client_base_url, client_host, is_lan_bind, is_wildcard_bind, lan_status, list_lan_ips

async def _protected(request):
    pass
# WARNING: Decompyle incomplete

authed_app = (lambda monkeypatch: monkeypatch.setenv('JARVIS_API_KEY', 'test-secret-key')app = Starlette(routes = [
Route('/api/chat', _protected),
Route('/api/live', _protected),
Route('/api/lan', _protected)])app.add_middleware(APIKeyMiddleware)TestClient(app))()

def test_api_key_enabled(monkeypatch):
    monkeypatch.delenv('JARVIS_API_KEY', raising = False)
    @py_assert1 = api_key_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(api_key_enabled) if 'api_key_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(api_key_enabled) else 'api_key_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    monkeypatch.setenv('JARVIS_API_KEY', 'abc')
    @py_assert1 = api_key_enabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(api_key_enabled) if 'api_key_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(api_key_enabled) else 'api_key_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_check_key_strips_whitespace(monkeypatch):
    monkeypatch.setenv('JARVIS_API_KEY', 'jarvis-home')
    req = MagicMock()
    req.headers = {
        'X-API-Key': '  jarvis-home  ' }
    req.query_params = { }
    @py_assert2 = check_key(req)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(check_key) if 'check_key' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(check_key) else 'check_key',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    monkeypatch.setenv('JARVIS_API_KEY', 'sekret')
    req = MagicMock()
    req.headers = {
        'Authorization': 'Bearer sekret' }
    req.query_params = { }
    @py_assert2 = check_key(req)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(check_key) if 'check_key' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(check_key) else 'check_key',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    req.headers = {
        'X-API-Key': 'sekret' }
    @py_assert2 = check_key(req)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(check_key) if 'check_key' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(check_key) else 'check_key',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    req.headers = {
        'X-API-Key': 'wrong' }
    @py_assert2 = check_key(req)
    @py_assert5 = False
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(check_key) if 'check_key' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(check_key) else 'check_key',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_middleware_exempt_live_and_lan(authed_app):
    @py_assert1 = authed_app.get
    @py_assert3 = '/api/live'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = @py_assert5.status_code
    @py_assert10 = 200
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}.status_code\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(authed_app) if 'authed_app' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(authed_app) else 'authed_app',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None
    @py_assert1 = authed_app.get
    @py_assert3 = '/api/lan'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = @py_assert5.status_code
    @py_assert10 = 200
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}.status_code\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(authed_app) if 'authed_app' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(authed_app) else 'authed_app',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None


def test_localhost_skips_api_key(monkeypatch):
    monkeypatch.setenv('JARVIS_API_KEY', 'sekret')
    req = MagicMock()
    req.client.host = '127.0.0.1'
    req.headers = { }
    @py_assert2 = is_local_client(req)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(is_local_client) if 'is_local_client' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_local_client) else 'is_local_client',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert2 = api_key_required_for(req)
    @py_assert5 = False
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(api_key_required_for) if 'api_key_required_for' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(api_key_required_for) else 'api_key_required_for',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_lan_client_needs_api_key(monkeypatch):
    monkeypatch.setenv('JARVIS_API_KEY', 'sekret')
    req = MagicMock()
    req.client.host = '192.168.1.42'
    req.headers = { }
    @py_assert2 = is_local_client(req)
    @py_assert5 = False
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(is_local_client) if 'is_local_client' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_local_client) else 'is_local_client',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert2 = api_key_required_for(req)
    @py_assert5 = True
    @py_assert4 = @py_assert2 is @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('is',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} is %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(api_key_required_for) if 'api_key_required_for' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(api_key_required_for) else 'api_key_required_for',
            'py1': @pytest_ar._saferepr(req) if 'req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(req) else 'req',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_middleware_blocks_remote_without_key(monkeypatch, authed_app):
    monkeypatch.setenv('JARVIS_TRUST_PROXY', '1')
    res = authed_app.get('/api/chat', headers = {
        'X-Forwarded-For': '192.168.1.50' })
    @py_assert1 = res.status_code
    @py_assert4 = 401
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


def test_middleware_allows_with_header(authed_app):
    res = authed_app.get('/api/chat', headers = {
        'X-API-Key': 'test-secret-key' })
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


def test_client_host_wildcard():
    @py_assert1 = '0.0.0.0'
    @py_assert3 = client_host(@py_assert1)
    @py_assert6 = '127.0.0.1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(client_host) if 'client_host' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(client_host) else 'client_host',
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
    @py_assert1 = '0.0.0.0'
    @py_assert3 = 8765
    @py_assert5 = client_base_url(@py_assert1, @py_assert3)
    @py_assert8 = 'http://127.0.0.1:8765'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(client_base_url) if 'client_base_url' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(client_base_url) else 'client_base_url',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None


def test_is_lan_bind(monkeypatch):
    monkeypatch.setenv('JARVIS_HOST', '127.0.0.1')
    @py_assert1 = is_lan_bind()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(is_lan_bind) if 'is_lan_bind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_lan_bind) else 'is_lan_bind',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    @py_assert1 = is_lan_bind()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(is_lan_bind) if 'is_lan_bind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_lan_bind) else 'is_lan_bind',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = '0.0.0.0'
    @py_assert3 = is_wildcard_bind(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_wildcard_bind) if 'is_wildcard_bind' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_wildcard_bind) else 'is_wildcard_bind',
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


def test_lan_status_shape(monkeypatch):
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    monkeypatch.setenv('JARVIS_API_KEY', 'key123')
    status = lan_status()
    @py_assert0 = status['ok']
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
    @py_assert0 = status['lan_enabled']
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
    @py_assert0 = status['api_key_required']
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
    @py_assert0 = status['local_url']
    @py_assert2 = @py_assert0.startswith
    @py_assert4 = 'http://127.0.0.1:'
    @py_assert6 = @py_assert2(@py_assert4)
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.startswith\n}(%(py5)s)\n}' % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert1 = status['connect_urls']
    @py_assert4 = isinstance(@py_assert1, list)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert1 = status['hints']
    @py_assert4 = isinstance(@py_assert1, list)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py0)s(%(py2)s, %(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None


def test_list_lan_ips_returns_list():
    ips = list_lan_ips()
    @py_assert3 = isinstance(ips, list)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py1)s, %(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(ips) if 'ips' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ips) else 'ips',
            'py2': @pytest_ar._saferepr(list) if 'list' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list) else 'list',
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert3 = None


def test_api_lan_route(chat_app):
    res = chat_app.get('/api/lan')
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
    data = res.json()
    @py_assert0 = data['ok']
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
    @py_assert0 = 'connect_urls'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_live_payload_security_fields(monkeypatch):
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    _live_payload = _live_payload
    import jarvis.gui.server
    data = _live_payload()
    @py_assert0 = 'network_guard'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'allow_remote'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'rate_limit'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = data['rate_limit']
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


def test_health_lite_security_fields(monkeypatch):
    monkeypatch.setenv('JARVIS_HOST', '0.0.0.0')
    _build_health_lite = _build_health_lite
    import jarvis.gui.server
    data = _build_health_lite()
    @py_assert0 = 'network_guard'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'allow_remote'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'rate_limit'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_health_lite_route(monkeypatch):
    TestClient = TestClient
    import fastapi.testclient
    server = server
    import jarvis.gui
    client = TestClient(server.app)
    res = client.get('/api/health/lite')
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
    data = res.json()
    @py_assert1 = data.get
    @py_assert3 = 'status'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'ok'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    @py_assert0 = 'network_guard'
    @py_assert2 = @py_assert0 in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

