# Source Generated with Decompyle++
# File: test_profiles.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for config profiles.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.profiles import PROFILE_DEFS, apply_profile, list_profiles, web_search_disabled

def test_list_profiles():
    pass
# WARNING: Decompyle incomplete


def test_apply_offline_disables_web_search(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.config.CHAT_SETTINGS_FILE', data_dir / 'chat_settings.json')
    monkeypatch.setattr('jarvis.profiles._load_chat_settings', __import__('jarvis.config', fromlist = [
        'config'])._load_chat_settings)
    monkeypatch.setattr('jarvis.profiles._write_chat_settings', __import__('jarvis.config', fromlist = [
        'config'])._write_chat_settings)
    monkeypatch.setattr('jarvis.profiles.save_personality_preset', (lambda p: pass))
    monkeypatch.setattr('jarvis.profiles.save_vision_quality', (lambda m: pass))
    monkeypatch.setattr('jarvis.profiles.apply_preset', (lambda p: {
'ok': True }))
    monkeypatch.setattr('jarvis.comfyui_settings.save_mode', (lambda m: {
'ok': True }))
    result = apply_profile('offline')
    @py_assert0 = result['profile']
    @py_assert3 = 'offline'
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
    @py_assert1 = web_search_disabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(web_search_disabled) if 'web_search_disabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(web_search_disabled) else 'web_search_disabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_apply_unknown_raises():
    pytest.raises(ValueError)
    apply_profile('nope')
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_uncensored_profile_in_defs():
    @py_assert0 = 'uncensored'
    @py_assert2 = @py_assert0 in PROFILE_DEFS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, PROFILE_DEFS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(PROFILE_DEFS) if 'PROFILE_DEFS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(PROFILE_DEFS) else 'PROFILE_DEFS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = PROFILE_DEFS['uncensored']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'enable_uncensored'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = True
    @py_assert8 = @py_assert6 is @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('is',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} is %(py10)s',), (@py_assert6, @py_assert9)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        @py_format13 = 'assert %(py12)s' % {
            'py12': @py_format11 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format13))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert9 = None
    @py_assert0 = PROFILE_DEFS['uncensored']['comfyui_mode']
    @py_assert3 = 'gpu'
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

