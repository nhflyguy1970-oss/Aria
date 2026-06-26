# Source Generated with Decompyle++
# File: test_ha_light_control.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''HA light color parsing, service payloads, and sunlight scene.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.ha_light_control import ASTRONOMICAL_TWILIGHT_ELEV, NAUTICAL_TWILIGHT_ELEV, NIGHT_OFF_ELEV, build_light_service_data, daylight_levels_from_sun, parse_color_control, resolve_color_name
from jarvis.home_assistant import parse_control

def test_resolve_color_name_movie():
    @py_assert1 = 'movie'
    @py_assert3 = resolve_color_name(@py_assert1)
    @py_assert6 = {
        'color_temp_kelvin': 2200,
        'brightness_pct': 12 }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_color_name) if 'resolve_color_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_color_name) else 'resolve_color_name',
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
    @py_assert1 = 'uv'
    @py_assert3 = resolve_color_name(@py_assert1)
    @py_assert6 = {
        'hs_color': [
            275,
            100] }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_color_name) if 'resolve_color_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_color_name) else 'resolve_color_name',
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


def test_build_light_service_data_rgb_and_brightness():
    (svc, data) = build_light_service_data('light.kitchen', action = 'on', rgb = [
        10,
        20,
        30], brightness_pct = 40)
    @py_assert2 = 'turn_on'
    @py_assert1 = svc == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (svc, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(svc) if 'svc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(svc) else 'svc',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = data['entity_id']
    @py_assert3 = 'light.kitchen'
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
    @py_assert0 = data['rgb_color']
    @py_assert3 = [
        10,
        20,
        30]
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
    @py_assert0 = data['brightness_pct']
    @py_assert3 = 40
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


def test_build_light_service_data_color_name():
    (svc, data) = build_light_service_data('light.lamp', color_name = 'warm')
    @py_assert2 = 'turn_on'
    @py_assert1 = svc == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (svc, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(svc) if 'svc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(svc) else 'svc',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = data['color_temp_kelvin']
    @py_assert3 = 2700
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


def test_build_light_service_data_off():
    (svc, data) = build_light_service_data('light.lamp', action = 'off')
    @py_assert2 = 'turn_off'
    @py_assert1 = svc == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (svc, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(svc) if 'svc' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(svc) else 'svc',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert2 = {
        'entity_id': 'light.lamp' }
    @py_assert1 = data == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (data, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_parse_color_control_phrases():
    @py_assert1 = 'set table lamp to blue'
    @py_assert3 = parse_color_control(@py_assert1)
    @py_assert6 = {
        'action': 'on',
        'target': 'table lamp',
        'color_name': 'blue' }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_color_control) if 'parse_color_control' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_color_control) else 'parse_color_control',
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
    @py_assert1 = 'dim table lamp to 30%'
    @py_assert3 = parse_color_control(@py_assert1)
    @py_assert6 = {
        'action': 'on',
        'target': 'table lamp',
        'brightness_pct': 30 }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_color_control) if 'parse_color_control' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_color_control) else 'parse_color_control',
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
    @py_assert1 = 'make family room uv'
    @py_assert3 = parse_color_control(@py_assert1)
    @py_assert6 = {
        'action': 'on',
        'target': 'family room',
        'color_name': 'uv' }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_color_control) if 'parse_color_control' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_color_control) else 'parse_color_control',
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


def test_parse_control_delegates_color():
    spec = parse_control('set table lamp to blue')
    @py_assert1 = []
    @py_assert0 = spec
    if spec:
        @py_assert5 = spec.get
        @py_assert7 = 'color_name'
        @py_assert9 = @py_assert5(@py_assert7)
        @py_assert12 = 'blue'
        @py_assert11 = @py_assert9 == @py_assert12
        @py_assert0 = @py_assert11
# WARNING: Decompyle incomplete

test_daylight_levels_from_sun = (lambda elevation, rising, bright_min, bright_max, in_window, monkeypatch: monkeypatch.setattr('jarvis.ha_light_control._read_weather', (lambda : pass))
    levels = daylight_levels_from_sun({
        'attributes': {
            'elevation': elevation,
            'rising': rising } })
    @py_assert3 = levels['brightness_pct']
    @py_assert1 = bright_min <= @py_assert3
    @py_assert2 = @py_assert3 <= bright_max
    if not @py_assert1 or @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('<=', '<='), (@py_assert1, @py_assert2), ('%(py0)s <= %(py4)s', '%(py4)s <= %(py5)s'), (bright_min, @py_assert3, bright_max)) % {
            'py0': @pytest_ar._saferepr(bright_min) if 'bright_min' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bright_min) else 'bright_min',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py5': @pytest_ar._saferepr(bright_max) if 'bright_max' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bright_max) else 'bright_max' }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = levels['in_window']
    @py_assert2 = @py_assert0 is in_window
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py3)s',), (@py_assert0, in_window)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(in_window) if 'in_window' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(in_window) else 'in_window' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 2000
    @py_assert4 = levels['color_temp_kelvin']
    @py_assert2 = @py_assert0 <= @py_assert4
    @py_assert6 = 6500
    @py_assert3 = @py_assert4 <= @py_assert6
    if not @py_assert2 or @py_assert3:
        @py_format8 = @pytest_ar._call_reprcompare(('<=', '<='), (@py_assert2, @py_assert3), ('%(py1)s <= %(py5)s', '%(py5)s <= %(py7)s'), (@py_assert0, @py_assert4, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert6 = None
    if elevation <= NIGHT_OFF_ELEV:
        @py_assert0 = levels['phase']
        @py_assert3 = 'night'
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
        return None
    if elevation < 0 and rising:
        @py_assert0 = levels['phase']
        @py_assert3 = 'dawn'
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
        return None
    if elevation < 0:
        @py_assert0 = levels['phase']
        @py_assert3 = 'dusk'
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
        return None
)()

def test_twilight_thresholds():
    @py_assert1 = ASTRONOMICAL_TWILIGHT_ELEV < NAUTICAL_TWILIGHT_ELEV
    @py_assert4 = 0
    @py_assert2 = NAUTICAL_TWILIGHT_ELEV < @py_assert4
    if not @py_assert1 or @py_assert2:
        @py_format6 = @pytest_ar._call_reprcompare(('<', '<'), (@py_assert1, @py_assert2), ('%(py0)s < %(py3)s', '%(py3)s < %(py5)s'), (ASTRONOMICAL_TWILIGHT_ELEV, NAUTICAL_TWILIGHT_ELEV, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ASTRONOMICAL_TWILIGHT_ELEV) if 'ASTRONOMICAL_TWILIGHT_ELEV' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ASTRONOMICAL_TWILIGHT_ELEV) else 'ASTRONOMICAL_TWILIGHT_ELEV',
            'py3': @pytest_ar._saferepr(NAUTICAL_TWILIGHT_ELEV) if 'NAUTICAL_TWILIGHT_ELEV' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(NAUTICAL_TWILIGHT_ELEV) else 'NAUTICAL_TWILIGHT_ELEV',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert1 = NIGHT_OFF_ELEV == NAUTICAL_TWILIGHT_ELEV
    if not @py_assert1:
        @py_format3 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py2)s',), (NIGHT_OFF_ELEV, NAUTICAL_TWILIGHT_ELEV)) % {
            'py0': @pytest_ar._saferepr(NIGHT_OFF_ELEV) if 'NIGHT_OFF_ELEV' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(NIGHT_OFF_ELEV) else 'NIGHT_OFF_ELEV',
            'py2': @pytest_ar._saferepr(NAUTICAL_TWILIGHT_ELEV) if 'NAUTICAL_TWILIGHT_ELEV' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(NAUTICAL_TWILIGHT_ELEV) else 'NAUTICAL_TWILIGHT_ELEV' }
        @py_format5 = 'assert %(py4)s' % {
            'py4': @py_format3 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None


def test_natural_light_tints(monkeypatch):
    monkeypatch.setattr('jarvis.ha_light_control._read_weather', (lambda : pass))
    blue = daylight_levels_from_sun({
        'attributes': {
            'elevation': -15,
            'rising': False } })
    @py_assert0 = blue['light_tint']
    @py_assert3 = 'blue hour'
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
    @py_assert1 = blue.get
    @py_assert3 = 'hs'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(blue) if 'blue' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(blue) else 'blue',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    sunrise = daylight_levels_from_sun({
        'attributes': {
            'elevation': 3,
            'rising': True } })
    @py_assert0 = sunrise['light_tint']
    @py_assert3 = ('sunrise', 'golden hour')
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = sunrise['color_temp_kelvin']
    @py_assert3 = 4000
    @py_assert2 = @py_assert0 < @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('<',), (@py_assert2,), ('%(py1)s < %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    midday = daylight_levels_from_sun({
        'attributes': {
            'elevation': 40,
            'rising': True } })
    @py_assert0 = midday['light_tint']
    @py_assert3 = 'midday'
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
    @py_assert0 = midday['color_temp_kelvin']
    @py_assert3 = 5500
    @py_assert2 = @py_assert0 >= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('>=',), (@py_assert2,), ('%(py1)s >= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert1 = midday.get
    @py_assert3 = 'hs'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = None
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(midday) if 'midday' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(midday) else 'midday',
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
    sunset = daylight_levels_from_sun({
        'attributes': {
            'elevation': 4,
            'rising': False } })
    @py_assert0 = sunset['light_tint']
    @py_assert3 = ('golden hour', 'sunset', 'afternoon')
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = sunset['color_temp_kelvin']
    @py_assert3 = 4500
    @py_assert2 = @py_assert0 <= @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('<=',), (@py_assert2,), ('%(py1)s <= %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_sunlight_unified_color_uses_cct_for_midday():
    sunlight_unified_color = sunlight_unified_color
    import jarvis.ha_light_control
    @py_assert1 = {
        'color_temp_kelvin': 5800,
        'hs': None }
    @py_assert3 = sunlight_unified_color(@py_assert1)
    @py_assert6 = {
        'color_temp_kelvin': 5800 }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(sunlight_unified_color) if 'sunlight_unified_color' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_unified_color) else 'sunlight_unified_color',
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


def test_sunlight_color_groups_tint_only():
    sunlight_color_groups = sunlight_color_groups
    import jarvis.ha_light_control
    groups = sunlight_color_groups([
        'light.a',
        'light.b'], {
        'color_temp_kelvin': 5800,
        'hs': [
            24,
            30] })
    @py_assert2 = len(groups)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(groups) if 'groups' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(groups) else 'groups',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = groups[0][0]
    @py_assert3 = {
        'hs': [
            24,
            30] }
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
    @py_assert1 = [
        'light.a']
    @py_assert3 = {
        'color_temp_kelvin': 5800,
        'hs': None }
    @py_assert5 = sunlight_color_groups(@py_assert1, @py_assert3)
    @py_assert8 = []
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(sunlight_color_groups) if 'sunlight_color_groups' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_color_groups) else 'sunlight_color_groups',
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


def test_apply_sunlight_fleet_uniform_cct(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_apply_sunlight_fleet_uniform_hs_for_tint(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_sunlight_effective_brightness_matches_levels():
    sunlight_effective_brightness = sunlight_effective_brightness
    import jarvis.ha_light_control
    @py_assert1 = {
        'brightness_pct': 88,
        'elevation': 40 }
    @py_assert3 = { }
    @py_assert5 = sunlight_effective_brightness(@py_assert1, @py_assert3)
    @py_assert8 = 88
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(sunlight_effective_brightness) if 'sunlight_effective_brightness' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_effective_brightness) else 'sunlight_effective_brightness',
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
    @py_assert1 = {
        'brightness_pct': 88,
        'elevation': 40,
        'hs': [
            24,
            30] }
    @py_assert3 = {
        'hs': [
            24,
            30] }
    @py_assert5 = sunlight_effective_brightness(@py_assert1, @py_assert3)
    @py_assert8 = 88
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(sunlight_effective_brightness) if 'sunlight_effective_brightness' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_effective_brightness) else 'sunlight_effective_brightness',
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
    @py_assert1 = {
        'brightness_pct': 37,
        'elevation': 5 }
    @py_assert3 = { }
    @py_assert5 = sunlight_effective_brightness(@py_assert1, @py_assert3)
    @py_assert8 = 37
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(sunlight_effective_brightness) if 'sunlight_effective_brightness' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_effective_brightness) else 'sunlight_effective_brightness',
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
    @py_assert1 = {
        'brightness_pct': 0,
        'elevation': -19 }
    @py_assert3 = { }
    @py_assert5 = sunlight_effective_brightness(@py_assert1, @py_assert3)
    @py_assert8 = 0
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, %(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(sunlight_effective_brightness) if 'sunlight_effective_brightness' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_effective_brightness) else 'sunlight_effective_brightness',
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


def test_build_light_service_data_sets_brightness_pct():
    (_, data) = build_light_service_data('light.x', action = 'on', brightness_pct = 40, rgb = [
        255,
        0,
        0])
    @py_assert0 = data['brightness_pct']
    @py_assert3 = 40
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
    @py_assert0 = 'brightness'
    @py_assert2 = @py_assert0 not in data
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, data)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_weather_adjustment_overcast(monkeypatch):
    monkeypatch.setattr('jarvis.ha_light_control._read_weather', (lambda : {
'condition': 'rainy',
'cloud_coverage': 100 }))
    levels = daylight_levels_from_sun({
        'attributes': {
            'elevation': 60,
            'rising': True } })
    @py_assert0 = levels['weather_condition']
    @py_assert3 = 'rainy'
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
    @py_assert0 = levels['cloud_coverage']
    @py_assert3 = 100
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
    @py_assert0 = levels['clear_sky_brightness_pct']
    @py_assert3 = 95
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
    @py_assert0 = 50
    @py_assert4 = levels['brightness_pct']
    @py_assert2 = @py_assert0 <= @py_assert4
    @py_assert6 = 95
    @py_assert3 = @py_assert4 <= @py_assert6
    if not @py_assert2 or @py_assert3:
        @py_format8 = @pytest_ar._call_reprcompare(('<=', '<='), (@py_assert2, @py_assert3), ('%(py1)s <= %(py5)s', '%(py5)s <= %(py7)s'), (@py_assert0, @py_assert4, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert0 = levels['color_temp_kelvin']
    @py_assert3 = 6100
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


def test_sunlight_unified_color_uses_hs_for_tint():
    sunlight_unified_color = sunlight_unified_color
    import jarvis.ha_light_control
    @py_assert1 = {
        'color_temp_kelvin': 3200,
        'hs': [
            24,
            30] }
    @py_assert3 = sunlight_unified_color(@py_assert1)
    @py_assert6 = {
        'hs': [
            24,
            30] }
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(sunlight_unified_color) if 'sunlight_unified_color' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sunlight_unified_color) else 'sunlight_unified_color',
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


def test_set_lights_batch():
    pass
# WARNING: Decompyle incomplete


def test_sunlight_activate_mocked(tmp_path, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_sunlight_all_lights_targets(monkeypatch):
    '''all_lights: true should target every available HA light, not preset devices.'''
    pass
# WARNING: Decompyle incomplete


def test_tick_sunlight_when_auto_enabled(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_tick_sunlight_skips_when_paused(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_dawn_clears_preset_pause(monkeypatch):
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'preset',
        'active_preset': 'movie mode',
        '_last_sun_elevation': -2 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 1.5, rising = True)
    @py_assert0 = 'sunlight_paused'
    @py_assert2 = @py_assert0 not in out
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, out)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'active_preset'
    @py_assert2 = @py_assert0 not in out
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, out)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_manual_pause_resumes_at_dawn_cross(monkeypatch):
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'manual',
        '_last_sun_elevation': -3 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 1, rising = True)
    @py_assert0 = 'sunlight_paused'
    @py_assert2 = @py_assert0 not in out
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, out)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_manual_pause_not_resumed_at_astronomical_dawn(monkeypatch):
    '''Astronomical dawn (~-17°) is before sunrise — stay paused.'''
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'manual',
        '_last_sun_elevation': -19 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, -17, rising = True)
    @py_assert1 = out.get
    @py_assert3 = 'sunlight_paused'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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


def test_manual_pause_never_resumes_at_midnight_new_day(monkeypatch):
    '''Summer midnight can still be above -18° — manual pause must not clear on date roll.'''
    monkeypatch.setattr('jarvis.sunlight_scene._local_date_str', (lambda : '2026-06-23'))
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'manual',
        '_sunlight_paused_on': '2026-06-22',
        '_last_sun_elevation': -6.5 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, -8, rising = False)
    @py_assert1 = out.get
    @py_assert3 = 'sunlight_paused'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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
    @py_assert1 = out.get
    @py_assert3 = 'sunlight_pause_reason'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'manual'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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


def test_manual_pause_resumes_after_missed_dawn_on_new_day(monkeypatch):
    monkeypatch.setattr('jarvis.sunlight_scene._local_date_str', (lambda : '2026-06-23'))
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'manual',
        '_sunlight_paused_on': '2026-06-22',
        '_last_sun_elevation': -25 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 12, rising = True)
    @py_assert0 = 'sunlight_paused'
    @py_assert2 = @py_assert0 not in out
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, out)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_manual_pause_stays_paused_until_dawn(monkeypatch):
    '''Same-day manual off during daylight stays paused until next dawn.'''
    monkeypatch.setattr('jarvis.sunlight_scene._local_date_str', (lambda : '2026-06-22'))
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'manual',
        '_sunlight_paused_on': '2026-06-22',
        '_last_sun_elevation': 30 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 28, rising = False)
    @py_assert1 = out.get
    @py_assert3 = 'sunlight_paused'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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


def test_preset_pause_resumes_at_dawn_cross(monkeypatch):
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        'sunlight_pause_reason': 'preset',
        '_last_sun_elevation': -4 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 2, rising = True)
    @py_assert0 = 'sunlight_paused'
    @py_assert2 = @py_assert0 not in out
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, out)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_legacy_pause_records_pause_date(monkeypatch):
    monkeypatch.setattr('jarvis.sunlight_scene._local_date_str', (lambda : '2026-06-22'))
    state = {
        'sunlight_auto': True,
        'sunlight_paused': True,
        '_last_sun_elevation': 30 }
    _handle_dawn_transition = _handle_dawn_transition
    import jarvis.sunlight_scene
    out = _handle_dawn_transition(state, 35, rising = True)
    @py_assert1 = out.get
    @py_assert3 = 'sunlight_paused'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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
    @py_assert1 = out.get
    @py_assert3 = '_sunlight_paused_on'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = '2026-06-22'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
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


def test_weather_twilight_floor_follows_clear_sky(monkeypatch):
    daylight_levels_from_sun = daylight_levels_from_sun
    import jarvis.ha_light_control
    monkeypatch.setattr('jarvis.ha_light_control._read_weather', (lambda : {
'condition': 'rainy',
'cloud_coverage': 100 }))
    low = daylight_levels_from_sun({
        'attributes': {
            'elevation': -10,
            'rising': False } })
    high = daylight_levels_from_sun({
        'attributes': {
            'elevation': -2,
            'rising': False } })
    @py_assert0 = high['brightness_pct']
    @py_assert3 = low['brightness_pct']
    @py_assert2 = @py_assert0 > @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('>',), (@py_assert2,), ('%(py1)s > %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_other_preset_pauses_sunlight(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_tick_skips_unchanged_levels(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_night_off_at_nautical_twilight(monkeypatch):
    '''Lights must turn off at or below -12° (end of nautical twilight).'''
    pass
# WARNING: Decompyle incomplete


def test_tick_forces_night_off_when_paused(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_tick_skips_when_sun_elevation_missing(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_maybe_pause_on_light_off(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_maybe_pause_on_toggle_when_on(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_maybe_pause_skips_when_not_managing(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_turn_off_sunlight_lights(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_sunlight_excludes_bedroom_lights(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_apply_sunlight_fleet_skips_instant_retry_when_fading(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_resolve_sunlight_transition_uses_long_fade_when_off(monkeypatch):
    _resolve_sunlight_transition = _resolve_sunlight_transition
    import jarvis.sunlight_scene
    monkeypatch.setattr('jarvis.sunlight_scene._any_target_light_off', (lambda lights: True))
    t = _resolve_sunlight_transition([
        'light.a'], base_transition = 45, sunrise_transition = 600, bright = 30, resumed = False)
    @py_assert2 = 600
    @py_assert1 = t == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (t, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(t) if 't' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t) else 't',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    monkeypatch.setattr('jarvis.sunlight_scene._any_target_light_off', (lambda lights: False))
    t = _resolve_sunlight_transition([
        'light.a'], base_transition = 45, sunrise_transition = 600, bright = 30, resumed = False)
    @py_assert2 = 45
    @py_assert1 = t == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (t, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(t) if 't' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t) else 't',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    t = _resolve_sunlight_transition([
        'light.a'], base_transition = 45, sunrise_transition = 600, bright = 30, resumed = True)
    @py_assert2 = 600
    @py_assert1 = t == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (t, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(t) if 't' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(t) else 't',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_sunlight_excludes_merkury_lights(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_sunlight_includes_wall1_merkury_and_lamp(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_evening_twilight_avoids_blue_hour_hs():
    _natural_light_tint = _natural_light_tint
    import jarvis.ha_light_control
    tint = _natural_light_tint(-5, rising = False)
    @py_assert1 = tint.get
    @py_assert3 = 'hs'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = None
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(tint) if 'tint' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tint) else 'tint',
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
    @py_assert0 = tint['label']
    @py_assert3 = ('dusk', 'twilight', 'sunset')
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_twilight_brightness_monotonic_evening():
    pass
# WARNING: Decompyle incomplete


def test_entity_hidden_from_jarvis(tmp_path, monkeypatch):
    hef = ha_entity_filter
    import jarvis
    hef._hidden_config.cache_clear()
    cfg = tmp_path / 'ha_hidden_entities.json'
    cfg.write_text('{"entity_ids":["light.bathroom_lamp"],"name_keywords":["bathroom"],"hide_unavailable_lights":true}', encoding = 'utf-8')
    monkeypatch.setattr(hef, '_HIDDEN_FILE', cfg)
    hef._hidden_config.cache_clear()
    @py_assert1 = hef.entity_hidden_from_jarvis
    @py_assert3 = {
        'entity_id': 'light.bathroom_lamp',
        'state': 'on',
        'attributes': { } }
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.entity_hidden_from_jarvis\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(hef) if 'hef' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hef) else 'hef',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = hef.entity_hidden_from_jarvis
    @py_assert3 = {
        'entity_id': 'light.hall',
        'state': 'on',
        'attributes': {
            'friendly_name': 'Main Bathroom' } }
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.entity_hidden_from_jarvis\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(hef) if 'hef' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hef) else 'hef',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = hef.entity_hidden_from_jarvis
    @py_assert3 = {
        'entity_id': 'light.ghost',
        'state': 'unavailable',
        'attributes': { } }
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.entity_hidden_from_jarvis\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(hef) if 'hef' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hef) else 'hef',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = hef.entity_hidden_from_jarvis
    @py_assert3 = {
        'entity_id': 'light.kitchen',
        'state': 'on',
        'attributes': {
            'friendly_name': 'Kitchen' } }
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.entity_hidden_from_jarvis\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(hef) if 'hef' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hef) else 'hef',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_weather_adjustment_morning_floor():
    _apply_weather_adjustment = _apply_weather_adjustment
    import jarvis.ha_light_control
    patch = patch
    import unittest.mock
    patch('jarvis.ha_light_control._read_weather', return_value = {
        'condition': 'cloudy',
        'cloud_coverage': 90 })
    out = _apply_weather_adjustment({
        'brightness_pct': 60,
        'elevation': 20 })
    None(None, None)
# WARNING: Decompyle incomplete

