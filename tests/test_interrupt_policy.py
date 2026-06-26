# Source Generated with Decompyle++
# File: test_interrupt_policy.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for interrupt_policy module.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion

def test_should_interrupt_focus_mode(monkeypatch):
    ip = interrupt_policy
    import jarvis
    monkeypatch.setattr('jarvis.config._load_chat_settings', (lambda : {
'scene_state': {
'active_preset': 'focus mode' } }))
    ip._focus_mode = False
    @py_assert1 = ip.should_interrupt
    @py_assert3 = 'useful'
    @py_assert5 = @py_assert1(tier = @py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_interrupt\n}(tier=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ip) if 'ip' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ip) else 'ip',
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
    @py_assert1 = ip.should_interrupt
    @py_assert3 = 'urgent'
    @py_assert5 = @py_assert1(tier = @py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_interrupt\n}(tier=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ip) if 'ip' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ip) else 'ip',
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


def test_should_interrupt_voice_active():
    ip = interrupt_policy
    import jarvis
    ip._voice_state = 'speaking'
    ip._focus_mode = False
    @py_assert1 = ip.should_interrupt
    @py_assert3 = 'useful'
    @py_assert5 = @py_assert1(tier = @py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_interrupt\n}(tier=%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ip) if 'ip' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ip) else 'ip',
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
    ip._voice_state = 'idle'


def test_evaluate_interrupt_suppressed(monkeypatch):
    ip = interrupt_policy
    import jarvis
    monkeypatch.setattr(ip, '_refresh_focus_mode', (lambda : pass))
    ip._focus_mode = True
    monkeypatch.setattr(ip, '_notify', (lambda : pass))
    out = ip.evaluate_interrupt('test', title = 'T', body = 'B', tier = 'useful')
    @py_assert0 = out['fired']
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
    ip._focus_mode = False


def test_evaluate_interrupt_fires(monkeypatch):
    pass
# WARNING: Decompyle incomplete

