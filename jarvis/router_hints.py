# Source Generated with Decompyle++
# File: router_hints.cpython-312.pyc (Python 3.12)

'''High-confidence utterance hints for the local intent router (P1 #23).'''
from __future__ import annotations
import re
from typing import Any
_DURATION_RE = re.compile('(?P<n>\\d+)\\s*(?P<unit>minutes?|mins?|hours?|hrs?|seconds?|secs?)', re.I)
_ALARM_TIME_RE = re.compile('(?:at|for)\\s+(?P<time>\\d{1,2}(?::\\d{2})?\\s*(?:am|pm)?(?:\\s+tomorrow)?)', re.I)
_TASK_RE = re.compile('^(?:add(?:\\s+a)?\\s+)?task\\s+(.+)$', re.I)

def try_hint_route(message = None):
    '''Fast regex router for common voice phrases (~0ms). Returns intent dict or None.'''
    if not message:
        message
    text = ''.strip()
    if text or len(text) > 280:
        return None
    lower = text.lower()
    if re.search('\\b(stop|halt)\\b.+\\b(audio|playback|music|speaking)\\b', lower) or lower in ('stop', 'stop audio', 'stop playback', 'stop speaking'):
        return _hit('audio_stop')
    if None.search('\\b(pause|hold)\\b.+\\b(audio|playback|music)\\b', lower) or lower in ('pause', 'pause audio', 'pause playback'):
        return _hit('audio_pause')
    if None.search('\\b(good morning|morning briefing)\\b', lower):
        return _hit('morning_briefing')
    if None.search("\\b(situational briefing|what(?:'s| is) my status|status briefing)\\b", lower):
        return _hit('situational_briefing')
    if None.search('\\b(news briefing|curated news|headlines|tech news)\\b', lower):
        return _hit('curated_briefing')
    if None.search("\\b(system status|system info|gpu status|what(?:'s| is) running)\\b", lower):
        return _hit('system_info')
    if None.search("\\b(planner today|today(?:'s)? schedule|what(?:'s| is) on my (?:planner|calendar) today)\\b", lower):
        return _hit('planner_today')
    if None.search('\\b(smart home|home assistant)\\b.+\\bstatus\\b', lower) or lower in ('home status', 'smart home status'):
        return _hit('ha_status')
    if None.search('\\bweather\\b', lower) or re.search('forecast (?:for|in)\\b', lower):
        loc = _extract_location(text)
        if loc:
            return _hit('weather_forecast', {
                'location': loc })
        return None(_hit, 'weather_forecast')
    if None.search('\\b(search (?:the )?web|search for|look up|google)\\b', lower):
        q = re.sub('^(?:please\\s+)?(?:search(?:\\s+the\\s+web)?\\s+for|search for|look up|google)\\s+', '', text, flags = re.I).strip()
        if not q:
            q
        return _hit('web_search', {
            'query': text })
    if None(lower):
        if not _extract_duration(text):
            _extract_duration(text)
        duration = _extract_duration(lower)
        params = { }
        if duration:
            params['duration'] = duration
        return _hit('planner_set_timer', params)
    if None.search('\\b(alarm|wake me)\\b', lower):
        params = { }
        if not _ALARM_TIME_RE.search(text):
            _ALARM_TIME_RE.search(text)
        m = _ALARM_TIME_RE.search(lower)
        if m:
            params['time'] = m.group('time').strip()
        return _hit('planner_set_alarm', params)
    m = None.match(text)
    if m:
        return _hit('planner_add_task', {
            'text': m.group(1).strip() })
    if None.search('\\bturn (?:on|off|toggle)\\b', lower) or re.search('\\b(dim|brighten)\\b', lower):
        params = _parse_ha_control(text, lower)
        if params:
            return _hit('ha_control', params)
        cad_iterate = None(text, lower)
        if cad_iterate:
            return _hit('iterate_cad', cad_iterate)
        cad_new = None(text, lower)
        if cad_new:
            return _hit('generate_cad', cad_new)
        if None in ('hello', 'hi', 'hey', 'thanks', 'thank you'):
            return _hit('chat')
        if None.search('\\b(explain|why does|step by step|prove that|debug)\\b', lower):
            return {
                'action': 'chat',
                'params': {
                    'thinking_mode': 'deep' },
                'thinking': 'hint:deep',
                'router': 'hint' }


def _hit(action = None, params = None):
    if not params:
        params
    return {
        'action': action,
        'params': dict({ }),
        'thinking': f'''hint:{action}''',
        'router': 'hint',
        'router_ms': 0 }


def _looks_like_timer(lower = None):
    if re.search('\\b(timer|countdown)\\b', lower):
        return True
    if re.search('\\bset (?:a )?timer\\b', lower):
        return True
    if re.search('\\btimer for\\b', lower):
        return True
    if re.search('\\bfor \\d+\\s*(?:minutes?|mins?|hours?|secs?)\\b', lower) and 'alarm' not in lower:
        return True
    return False


def _extract_duration(text = None):
    m = _DURATION_RE.search(text)
    if not m:
        return None
    unit = m.group('unit').lower()
    if unit.startswith('min'):
        unit = 'minutes'
    elif unit.startswith('hour') or unit == 'hr':
        unit = 'hours'
    elif unit.startswith('sec'):
        unit = 'seconds'
    return f'''{m.group('n')} {unit}'''


def _extract_location(text = None):
    m = re.search('(?:weather|forecast)\\s+(?:for|in)\\s+(.+?)(?:\\?|$)', text, re.I)
    if m:
        return m.group(1).strip(' ?.')


def _parse_ha_control(text = None, lower = None):
    action = 'toggle'
    if re.search('\\bturn on\\b', lower) or re.search('\\bturn on the\\b', lower):
        action = 'on'
    elif re.search('\\bturn off\\b', lower):
        action = 'off'
    elif re.search('\\bdim\\b', lower):
        action = 'on'
    target = ''
    m = re.search('\\bturn (?:on|off|toggle)\\s+(?:the\\s+)?(.+)$', text, re.I)
    if m:
        target = m.group(1).strip(' .?!')
    if not target:
        m = re.search('\\b(?:dim|brighten)\\s+(?:the\\s+)?(.+)$', text, re.I)
        if m:
            target = m.group(1).strip(' .?!')
    if not target:
        return None
    return {
        'target': target,
        'action': action }


def _parse_iterate_cad(text = None, lower = None):
    if re.search('\\b(make it|make the)\\s+(taller|shorter|wider|thinner|thicker|bigger|smaller)\\b', lower):
        m = re.search('\\b(make it|make the)\\s+((?:taller|shorter|wider|thinner|thicker|bigger|smaller)\\b.*)$', text, re.I)
        prompt = m.group(0).strip(' .?!') if m else text.strip(' .?!')
        return {
            'prompt': prompt,
            'edit': 'true' }
    for pat in None:
        m = re.match(pat, text, re.I)
        if not m:
            continue
        
        return None, {
            'prompt': m.group(1).strip(' .?!'),
            'edit': 'true' }
    if re.search('\\b(iterate|modify)\\b.+\\b(design|cad|model|part)\\b', lower):
        if not prompt:
            prompt
        return {
            'prompt': text.strip(' .?!'),
            'edit': 'true' }


def _parse_generate_cad(text = None, lower = None):
    if re.search('\\b(iterate|modify|edit|update|make it)\\b', lower) and re.search('\\b(taller|thicker|thinner|wider|shorter|bigger|smaller)\\b', lower):
        return None
    for pat in ('^(?:design|generate|create|make)\\s+(?:a\\s+)?(?:cad\\s+)?(?:stl\\s+)?(?:for\\s+)?(.+)$', '^(?:design|generate|create)\\s+(?:a\\s+)?(?:3d\\s+)?(?:part|model)\\s+(?:for\\s+)?(.+)$', '^generate\\s+cad\\s+(?:for\\s+)?(.+)$'):
        m = re.match(pat, text, re.I)
        if not m:
            continue
        
        return ('^(?:design|generate|create|make)\\s+(?:a\\s+)?(?:cad\\s+)?(?:stl\\s+)?(?:for\\s+)?(.+)$', '^(?:design|generate|create)\\s+(?:a\\s+)?(?:3d\\s+)?(?:part|model)\\s+(?:for\\s+)?(.+)$', '^generate\\s+cad\\s+(?:for\\s+)?(.+)$'), {
            'prompt': m.group(1).strip(' .?!') }
    if re.search('\\b(design|generate|create)\\b.+\\b(cad|stl|adapter|bracket|part)\\b', lower):
        if not prompt:
            prompt
        return {
            'prompt': text.strip(' .?!') }


def contradicts_hint(message = None, action = None):
    '''True when a model route likely conflicts with obvious utterance intent.'''
    if not message:
        message
    lower = ''.lower()
    if action == 'morning_briefing' and _looks_like_timer(lower):
        return True
    if action == 'planner_set_alarm' and _looks_like_timer(lower) and 'alarm' not in lower and 'wake' not in lower:
        return True
    if action == 'morning_briefing' and re.search('\\bturn (?:on|off)\\b', lower):
        return True
    if action == 'planner_set_timer' and re.search('\\bgood morning\\b', lower):
        return True
    if action == 'generate_cad' and _parse_iterate_cad(message, lower):
        return True
    if action == 'chat' and _parse_iterate_cad(message, lower):
        return True
    if action in ('planner_set_alarm', 'planner_set_timer', 'morning_briefing', 'chat') and re.search('\\bturn (?:on|off|toggle)\\b', lower):
        return True
    if action == 'planner_set_alarm' and re.search('\\b(?:lights?|lamp|room)\\b', lower):
        return True
    if action == 'briefing_news_detail':
        looks_like_general_expansion = looks_like_general_expansion
        import jarvis.briefing_news
        if looks_like_general_expansion(message):
            return True
    return False

