# Source Generated with Decompyle++
# File: test_network_guard.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for home-network request guard.'''
import builtins as @py_builtins

rewrite
import os = import _pytest.assertion.rewrite, assertion
from unittest.mock import MagicMock
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from jarvis import network_guard

async def _protected(request):
    pass
# WARNING: Decompyle incomplete

guarded_app = (lambda monkeypatch: monkeypatch.delenv('JARVIS_ALLOW_REMOTE', raising = False)monkeypatch.setenv('JARVIS_NETWORK_GUARD', '1')monkeypatch.setenv('JARVIS_TRUST_PROXY', '1')
def _guard_on():
if os.getenv('JARVIS_NETWORK_GUARD', '').lower() in ('0', 'false', 'no', 'off'):
FalseTruemonkeypatch.setattr(network_guard, 'guard_enabled', _guard_on)app = Starlette(routes = [
Route('/api/chat', _protected)])app.add_middleware(network_guard.NetworkGuardMiddleware)TestClient(app))()

def _req(ip = None, path = None):
    req = MagicMock()
    req.url.path = path
    req.client.host = ip
    req.headers = { }
    return req


def test_localhost_allowed(monkeypatch):
    monkeypatch.delenv('JARVIS_ALLOW_REMOTE', raising = False)
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising = False)
    monkeypatch.setenv('JARVIS_NETWORK_GUARD', '1')
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '127.0.0.1'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '::1'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None


def test_lan_allowed(monkeypatch):
    monkeypatch.delenv('JARVIS_ALLOW_REMOTE', raising = False)
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising = False)
    monkeypatch.setenv('JARVIS_NETWORK_GUARD', '1')
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '192.168.1.42'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '10.0.0.5'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None


def test_public_blocked(monkeypatch):
    monkeypatch.delenv('JARVIS_ALLOW_REMOTE', raising = False)
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising = False)
    monkeypatch.setenv('JARVIS_NETWORK_GUARD', '1')
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '8.8.8.8'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    @py_assert10 = not @py_assert8
    if not @py_assert10:
        @py_format11 = 'assert not %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '1.2.3.4'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    @py_assert10 = not @py_assert8
    if not @py_assert10:
        @py_format11 = 'assert not %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None


def test_allow_remote_override(monkeypatch):
    monkeypatch.setenv('JARVIS_ALLOW_REMOTE', '1')
    monkeypatch.setenv('JARVIS_NETWORK_GUARD', '1')
    @py_assert1 = network_guard.client_allowed
    @py_assert4 = '8.8.8.8'
    @py_assert6 = _req(@py_assert4)
    @py_assert8 = @py_assert1(@py_assert6)
    if not @py_assert8:
        @py_format10 = 'assert %(py9)s\n{%(py9)s = %(py2)s\n{%(py2)s = %(py0)s.client_allowed\n}(%(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n})\n}' % {
            'py0': @pytest_ar._saferepr(network_guard) if 'network_guard' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(network_guard) else 'network_guard',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(_req) if '_req' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_req) else '_req',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None


def test_middleware_blocks_public_ip(guarded_app):
    res = guarded_app.get('/api/chat', headers = {
        'X-Forwarded-For': '8.8.8.8' })
    @py_assert1 = res.status_code
    @py_assert4 = 403
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


def test_middleware_allows_lan_ip(guarded_app):
    res = guarded_app.get('/api/chat', headers = {
        'X-Forwarded-For': '192.168.1.42' })
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
    @py_assert0 = res.json()['ok']
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

