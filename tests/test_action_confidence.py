# Source Generated with Decompyle++
# File: test_action_confidence.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for action_confidence module.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion

def test_confidence_insufficient_samples(data_dir, monkeypatch):
    monkeypatch.setenv('JARVIS_CONFIDENCE_MIN_SAMPLES', '5')
    ac = action_confidence
    import jarvis
    ac._loaded = False
    ac._stats = { }
    @py_assert1 = ac.confidence_for
    @py_assert3 = 'ha_control'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 0.5
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.confidence_for\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ac) if 'ac' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ac) else 'ac',
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
    @py_assert1 = ac.confidence_tier
    @py_assert3 = 'ha_control'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'medium'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.confidence_tier\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ac) if 'ac' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ac) else 'ac',
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


def test_confidence_after_outcomes(data_dir, monkeypatch):
    monkeypatch.setenv('JARVIS_CONFIDENCE_MIN_SAMPLES', '3')
    ac = action_confidence
    import jarvis
    ac._loaded = False
    ac._stats = { }
    monkeypatch.setattr(ac, 'STORE_FILE', data_dir / 'action_confidence.json')
    for _ in range(4):
        ac.record_outcome('ha_control', ok = True)
    ac.record_outcome('ha_control', ok = False)
    c = ac.confidence_for('ha_control')
    @py_assert0 = 0.7
    @py_assert2 = @py_assert0 <= c
    @py_assert5 = 0.9
    @py_assert3 = c <= @py_assert5
    if not @py_assert2 or @py_assert3:
        @py_format7 = @pytest_ar._call_reprcompare(('<=', '<='), (@py_assert2, @py_assert3), ('%(py1)s <= %(py4)s', '%(py4)s <= %(py6)s'), (@py_assert0, c, @py_assert5)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(c) if 'c' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(c) else 'c',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = ac.confidence_tier
    @py_assert3 = 'ha_control'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'high'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.confidence_tier\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(ac) if 'ac' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ac) else 'ac',
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


def test_autonomy_decision_low(data_dir, monkeypatch):
    monkeypatch.setenv('JARVIS_CONFIDENCE_MIN_SAMPLES', '3')
    monkeypatch.setenv('JARVIS_CONFIDENCE_LOW', '0.45')
    ac = action_confidence
    import jarvis
    ac._loaded = False
    ac._stats = {
        'workflow_run': {
            'success': 0,
            'failure': 5 } }
    ac._loaded = True
    monkeypatch.setattr(ac, 'STORE_FILE', data_dir / 'action_confidence.json')
    d = ac.autonomy_decision('workflow_run')
    @py_assert0 = d['needs_confirm']
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
    @py_assert0 = d['tier']
    @py_assert3 = 'low'
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

