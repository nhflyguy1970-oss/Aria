# Source Generated with Decompyle++
# File: test_ada_parity.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Ada local + Ada v2 feature parity tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
(lambda : group_devices_by_room = group_devices_by_roomlist_rooms = list_roomsimport jarvis.kasa_roomsdevices = [
{
'alias': 'Office Lamp',
'host': '192.168.1.10' },
{
'alias': 'Kitchen Strip',
'host': '192.168.1.11' },
{
'alias': 'mystery plug',
'host': '192.168.1.12' }]groups = group_devices_by_room(devices)@py_assert0 = 'Office'@py_assert2 = @py_assert0 in groupsif not @py_assert2:
@py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, groups)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py3': @pytest_ar._saferepr(groups) if 'groups' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(groups) else 'groups' }@py_format6 = 'assert %(py5)s' % {
'py5': @py_format4 }raise AssertionError(@pytest_ar._format_explanation(@py_format6))@py_assert0 = None@py_assert2 = None@py_assert0 = 'Kitchen'@py_assert2 = @py_assert0 in groupsif not @py_assert2:
@py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, groups)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py3': @pytest_ar._saferepr(groups) if 'groups' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(groups) else 'groups' }@py_format6 = 'assert %(py5)s' % {
'py5': @py_format4 }raise AssertionError(@pytest_ar._format_explanation(@py_format6))@py_assert0 = None@py_assert2 = None@py_assert0 = 'Other'@py_assert2 = @py_assert0 in groupsif not @py_assert2:
@py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, groups)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py3': @pytest_ar._saferepr(groups) if 'groups' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(groups) else 'groups' }@py_format6 = 'assert %(py5)s' % {
'py5': @py_format4 }raise AssertionError(@pytest_ar._format_explanation(@py_format6))@py_assert0 = None@py_assert2 = Nonerooms = list_rooms(devices)@py_assert0 = rooms[0]@py_assert3 = 'All'@py_assert2 = @py_assert0 == @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None@py_assert0 = 'Office'@py_assert2 = @py_assert0 in roomsif not @py_assert2:
@py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, rooms)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py3': @pytest_ar._saferepr(rooms) if 'rooms' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(rooms) else 'rooms' }@py_format6 = 'assert %(py5)s' % {
'py5': @py_format4 }raise AssertionError(@pytest_ar._format_explanation(@py_format6))@py_assert0 = None@py_assert2 = None) = import _pytest.assertion.rewrite, assertion

def test_focus_relax_presets_in_defaults():
    DEFAULT_PRESETS = DEFAULT_PRESETS
    import jarvis.scene_presets
    @py_assert0 = 'focus mode'
    @py_assert2 = @py_assert0 in DEFAULT_PRESETS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, DEFAULT_PRESETS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(DEFAULT_PRESETS) if 'DEFAULT_PRESETS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(DEFAULT_PRESETS) else 'DEFAULT_PRESETS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = DEFAULT_PRESETS['focus mode']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'kasa_all'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = 'off'
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
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
    @py_assert0 = 'relax'
    @py_assert2 = @py_assert0 in DEFAULT_PRESETS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, DEFAULT_PRESETS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(DEFAULT_PRESETS) if 'DEFAULT_PRESETS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(DEFAULT_PRESETS) else 'DEFAULT_PRESETS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = DEFAULT_PRESETS['relax']
    @py_assert2 = @py_assert0.get
    @py_assert4 = 'kasa_brightness'
    @py_assert6 = @py_assert2(@py_assert4)
    @py_assert9 = 40
    @py_assert8 = @py_assert6 == @py_assert9
    if not @py_assert8:
        @py_format11 = @pytest_ar._call_reprcompare(('==',), (@py_assert8,), ('%(py7)s\n{%(py7)s = %(py3)s\n{%(py3)s = %(py1)s.get\n}(%(py5)s)\n} == %(py10)s',), (@py_assert6, @py_assert9)) % {
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


def test_curated_news_categories():
    get_curated_headlines = get_curated_headlines
    import jarvis.curated_news
    data = get_curated_headlines(use_ai = False, force_refresh = True)
    if not data.get('categories'):
        data.get('categories')
    cats = []
    @py_assert0 = 'Markets'
    @py_assert2 = @py_assert0 in cats
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, cats)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cats) if 'cats' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cats) else 'cats' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'Culture'
    @py_assert2 = @py_assert0 in cats
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, cats)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cats) if 'cats' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cats) else 'cats' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert2 = 'breaking'
    @py_assert4 = @py_assert2 in data
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert10 = data.get
        @py_assert12 = 'headlines'
        @py_assert14 = @py_assert10(@py_assert12)
        @py_assert17 = None
        @py_assert16 = @py_assert14 is not @py_assert17
        @py_assert0 = @py_assert16
# WARNING: Decompyle incomplete


def test_system_info_intelligence_block():
    build_system_info = build_system_info
    import jarvis.system_info
    info = build_system_info()
    @py_assert0 = 'intelligence'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    intel = info['intelligence']
    @py_assert0 = 'daily_focus'
    @py_assert2 = @py_assert0 in intel
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, intel)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(intel) if 'intel' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intel) else 'intel' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'intel_alert'
    @py_assert2 = @py_assert0 in intel
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, intel)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(intel) if 'intel' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intel) else 'intel' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'smart_home'
    @py_assert2 = @py_assert0 in intel
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, intel)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(intel) if 'intel' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intel) else 'intel' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'priority'
    @py_assert2 = @py_assert0 in intel
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, intel)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(intel) if 'intel' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(intel) else 'intel' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_system_info_greeting_and_weather_fields():
    build_system_info = build_system_info
    import jarvis.system_info
    info = build_system_info()
    @py_assert0 = 'greeting_short'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'welcome'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'date_label'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'time_display'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    if not info.get('weather'):
        info.get('weather')
    weather = { }
    @py_assert1 = []
    @py_assert3 = weather.get
    @py_assert5 = 'summary'
    @py_assert7 = @py_assert3(@py_assert5)
    @py_assert0 = @py_assert7
    if not @py_assert7:
        @py_assert11 = weather.get
        @py_assert13 = 'hint'
        @py_assert15 = @py_assert11(@py_assert13)
        @py_assert0 = @py_assert15
        if not @py_assert15:
            @py_assert19 = weather.get
            @py_assert21 = 'error'
            @py_assert23 = @py_assert19(@py_assert21)
            @py_assert0 = @py_assert23
# WARNING: Decompyle incomplete


def test_iterate_cad_handler_registered():
    has_action = has_action
    import jarvis.handlers.registry
    @py_assert1 = 'iterate_cad'
    @py_assert3 = has_action(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(has_action) if 'has_action' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(has_action) else 'has_action',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None

