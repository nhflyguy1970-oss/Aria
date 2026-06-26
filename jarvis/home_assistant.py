# Source Generated with Decompyle++
# File: home_assistant.cpython-312.pyc (Python 3.12)

'''Home Assistant integration — read state, call services, scenes, automation webhooks.'''
from __future__ import annotations
import json
import logging
import os
import re
import time
import urllib.error as urllib
import urllib.parse as urllib
import urllib.request as urllib
from typing import Any
log = logging.getLogger('jarvis')
_USER_AGENT = 'Jarvis/3.2 HomeAssistant'

def _normalize_ha_text(message = None):
    '''Lowercase and normalize casual typing / STT (missing apostrophes, trailing punctuation).'''
    if not message:
        message
    text = ''.lower().strip()
    text = re.sub('[?.!,;]+$', '', text)
    text = re.sub('\\bwhats\\b', "what's", text)
    text = re.sub('\\bhows\\b', "how's", text)
    text = re.sub('\\bwhat s\\b', "what's", text)
    text = re.sub('\\bhow s\\b', "how's", text)
    return text


def ha_enabled():
    flag = os.getenv('JARVIS_HA_ENABLED', '').lower()
    if flag in ('0', 'false', 'no', 'off'):
        return False
    if flag in ('1', 'true', 'yes', 'on'):
        if ha_url():
            ha_url()
        return bool(ha_token())
    if ha_url():
        ha_url()
    return None(ha_token())


def ha_url():
    if not os.getenv('JARVIS_HA_URL', ''):
        os.getenv('JARVIS_HA_URL', '')
    return os.getenv('HOME_ASSISTANT_URL', '').strip().rstrip('/')


def ha_token():
    if not os.getenv('JARVIS_HA_TOKEN', ''):
        os.getenv('JARVIS_HA_TOKEN', '')
    return normalize_ha_token(os.getenv('HOME_ASSISTANT_TOKEN', ''))


def normalize_ha_token(raw = None):
    '''Clean pasted tokens — strip whitespace, quotes, accidental Bearer prefix.'''
    if not raw:
        raw
    token = ''.strip()
    if not token:
        return ''
    if token.lower().startswith('bearer '):
        token = token[7:].strip()
    if (token.startswith('"') or token.endswith('"') or token.startswith("'")) and token.endswith("'"):
        token = token[1:-1].strip()
    return token.replace('\r', '').replace('\n', '').replace(' ', '')


def ha_feature_on():
    flag = os.getenv('JARVIS_HA_ENABLED', '').lower().strip()
    if flag in ('0', 'false', 'no', 'off'):
        return False
    return True


def _friendly_ha_error(exc = None):
    msg = str(exc)
    if 'HTTP 401' in msg or 'Unauthorized' in msg:
        return 'Invalid Home Assistant token (401). In HA: Profile → Security → Long-lived access tokens → Create token. Copy the entire token and paste again.'
    if 'HTTP 403' in msg:
        return 'Home Assistant rejected the token (403). Create a new long-lived token.'
    return msg


def automation_secret():
    return os.getenv('JARVIS_AUTOMATION_SECRET', '').strip()


def leave_scene():
    if not os.getenv('JARVIS_HA_SCENE_LEAVE', '').strip():
        os.getenv('JARVIS_HA_SCENE_LEAVE', '').strip()
    return 'scene.leaving'


def _headers():
    return {
        'Authorization': f'''Bearer {ha_token()}''',
        'Content-Type': 'application/json',
        'User-Agent': _USER_AGENT }


def _request(method = None, path = None, body = None, *, timeout):
    if not ha_url() or ha_token():
        raise RuntimeError('Home Assistant not configured — set JARVIS_HA_URL and JARVIS_HA_TOKEN.')
    url = f'''{ha_url()}{path}'''
# WARNING: Decompyle incomplete


def _ha_version():
    '''HA /api/ often omits version — /api/config includes it.'''
    
    try:
        info = _request('GET', '/api/')
        version = info.get('version') if isinstance(info, dict) else None
        if version:
            return str(version)
        
        try:
            cfg = _request('GET', '/api/config')
            if isinstance(cfg, dict) and cfg.get('version'):
                return str(cfg['version'])
            except Exception:
                continue
        except Exception:
            return None



_ha_location_cache: 'dict[str, Any] | None' = None
_ha_location_cache_ts: 'float' = 0
_states_cache: 'list[dict] | None' = None
_states_cache_at: 'float' = 0
_STATES_CACHE_TTL = float(os.getenv('JARVIS_HA_STATES_CACHE_SEC', '12'))
_conn_cache: 'dict[str, Any] | None' = None
_conn_cache_at: 'float' = 0
_CONN_CACHE_TTL = float(os.getenv('JARVIS_HA_CONN_CACHE_SEC', '30'))

def get_ha_location(*, max_age):
    '''Home coordinates from HA /api/config (used by sun.sun elevation).'''
    global _ha_location_cache, _ha_location_cache_ts
    import time
    if _ha_location_cache and time.time() - _ha_location_cache_ts < max_age:
        return dict(_ha_location_cache)
    
    try:
        cfg = _request('GET', '/api/config')
        if isinstance(cfg, dict):
            loc = {
                'latitude': cfg.get('latitude'),
                'longitude': cfg.get('longitude'),
                'elevation': cfg.get('elevation'),
                'time_zone': cfg.get('time_zone'),
                'location_name': cfg.get('location_name') }
            _ha_location_cache = loc
            _ha_location_cache_ts = time.time()
            return dict(loc)
        if not _ha_location_cache:
            _ha_location_cache
        return dict({ })
    except Exception:
        exc = None
        log.debug('get_ha_location: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc



def get_sun_times():
    '''Current sun state plus next rising/setting from HA.'''
    if not get_state('sun.sun'):
        get_state('sun.sun')
    st = { }
    if not st.get('attributes'):
        st.get('attributes')
    attrs = { }
    return {
        'elevation': attrs.get('elevation'),
        'azimuth': attrs.get('azimuth'),
        'rising': attrs.get('rising'),
        'next_rising': attrs.get('next_rising'),
        'next_setting': attrs.get('next_setting'),
        'next_dawn': attrs.get('next_dawn'),
        'next_dusk': attrs.get('next_dusk') }


def check_connection(*, refresh):
    pass
# WARNING: Decompyle incomplete


def invalidate_states_cache():
    global _states_cache, _states_cache_at, _conn_cache, _conn_cache_at
    _states_cache = None
    _states_cache_at = 0
    _conn_cache = None
    _conn_cache_at = 0


def list_states(*, refresh):
    pass
# WARNING: Decompyle incomplete


def get_state(entity_id = None):
    if not entity_id:
        entity_id
    eid = ''.strip()
    if not eid:
        return None
    
    try:
        state = _request('GET', f'''/api/states/{urllib.parse.quote(eid)}''')
        if isinstance(state, dict):
            return state
        return None
    except RuntimeError:
        return None



def _norm(s = None):
    if not s:
        s
    return re.sub('[\\s_]+', ' ', ''.lower()).strip()


def find_entities(query = None, *, domain, limit):
    q = _norm(query)
    if not q:
        return []
# WARNING: Decompyle incomplete


def call_service(domain = None, service = None, data = None):
    if not data:
        data
    payload = dict({ })
    result = _request('POST', f'''/api/services/{domain}/{service}''', payload)
    invalidate_states_cache()
    return {
        'domain': domain,
        'service': service,
        'data': payload,
        'result': result }


def _entity_line(st = None):
    eid = st.get('entity_id', '')
    if not st.get('attributes'):
        st.get('attributes')
    attrs = { }
    if not attrs.get('friendly_name'):
        attrs.get('friendly_name')
    name = eid
    state = st.get('state', '?')
    if not attrs.get('unit_of_measurement'):
        attrs.get('unit_of_measurement')
    unit = ''
    suffix = f''' {unit}''' if unit else ''
    return f'''- **{name}** (`{eid}`): {state}{suffix}'''


def format_entity(st = None):
    return _entity_line(st).replace('- **', '**').replace('** (`', '** (`', 1)


def activate_scene(scene = None):
    if not scene:
        scene
    scene = ''.strip()
    if not scene:
        return (False, 'Which scene?')
    if not scene.startswith('scene.'):
        matches = find_entities(scene, domain = 'scene', limit = 3)
        if len(matches) == 1:
            scene = matches[0]['entity_id']
        elif matches:
            lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(matches())
            return (False, f'''Multiple scenes match — be specific:\n{lines}''')
        scene = f'''scene.{scene.replace(' ', '_').lower()}'''
    
    try:
        call_service('scene', 'turn_on', {
            'entity_id': scene })
        st = get_state(scene)
        if not st:
            st
        if not { }.get('attributes', { }).get('friendly_name'):
            { }.get('attributes', { }).get('friendly_name')
        name = scene
        return (True, f'''Activated scene **{name}** (`{scene}`).''')
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def _fuzzy_control_enabled():
    
    try:
        ha_fuzzy_enabled = ha_fuzzy_enabled
        import jarvis.feature_flags
        return ha_fuzzy_enabled()
    except Exception:
        return True


_LIGHT_QUERY_WORDS = frozenset({
    'bulb',
    'lamp',
    'bulbs',
    'lamps',
    'light',
    'lights'})
_CONTROL_DOMAINS = ('light', 'switch')
_CONTROL_SKIP_WORDS = _LIGHT_QUERY_WORDS | frozenset({
    'a',
    'an',
    'my',
    'all',
    'the',
    'room',
    'switch',
    'switches',
    'everything'})
_CONTROL_EXCLUDE_HAY = frozenset({
    'ink',
    'media',
    'sonos',
    'toner',
    'sensor',
    'printer',
    'speaker',
    'chromecast',
    'television'})

def _control_domains(target = None):
    words = set(_norm(target).split())
    if words & _LIGHT_QUERY_WORDS:
        return ('light',)
    return _CONTROL_DOMAINS


def _significant_control_tokens(target = None):
    pass
# WARNING: Decompyle incomplete


def entity_is_available(st = None):
    '''False for HA ghost/restored entities (e.g. after Tuya auth expires).'''
    if not st.get('state'):
        st.get('state')
    state = ''.lower()
    if state in ('unavailable', 'unknown'):
        return False
    if not st.get('attributes'):
        st.get('attributes')
    if { }.get('restored'):
        return False
    return True


def _entity_controllable(st = None, *, domains):
    pass
# WARNING: Decompyle incomplete


def _entity_matches_tokens(st = None, tokens = None):
    pass
# WARNING: Decompyle incomplete


def _filter_control_matches(matches = None, target = None, *, domains):
    tokens = _significant_control_tokens(target)
# WARNING: Decompyle incomplete


def _fuzzy_match_entities(target = None, *, limit):
    '''Match controllable HA entities for voice/chat control — lights/switches only.'''
    t = _norm(target)
    if not t:
        return []
    domains = None(target)
# WARNING: Decompyle incomplete


def control_entity(target = None, action = None, *, brightness_pct, brightness, rgb, hs, color_temp_kelvin, color_name, transition):
    if not action:
        action
    action = ''.strip().lower()
    if action not in ('on', 'off', 'toggle'):
        return (False, f'''Unknown action `{action}` — use on, off, or toggle.''')
# WARNING: Decompyle incomplete


def _control_many(matches = None, action = None, *, brightness_pct, brightness, rgb, hs, color_temp_kelvin, color_name, transition):
    pass
# WARNING: Decompyle incomplete


def query_entity(question = None):
    if not question:
        question
    q = ''.strip()
    matches = find_entities(q, limit = 5)
    if matches and re.search('^(sensor|light|switch|climate|binary_sensor)\\.', q.replace(' ', '_')):
        st = get_state(q.replace(' ', '_'))
        if st:
            matches = [
                st]
    if not matches:
        return (False, f'''I couldn\'t find a Home Assistant entity for `{q}`.''')
    if None(matches) > 1:
        lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(matches[:6]())
        return (True, f'''Matches:\n{lines}''')
    return (None, _entity_line(matches[0]).lstrip('- '))


def home_summary(*, limit):
    pass
# WARNING: Decompyle incomplete


def parse_scene(message = None):
    if not message:
        message
    text = ''.strip()
    for pat in ('^(?:activate|run|trigger|start)\\s+(?:the\\s+)?scene[:\\s]+(.+)$', '^scene[:\\s]+(.+)$', '^(?:activate|run)\\s+(.+)\\s+scene$'):
        m = re.match(pat, text, re.I)
        if not m:
            continue
        
        return ('^(?:activate|run|trigger|start)\\s+(?:the\\s+)?scene[:\\s]+(.+)$', '^scene[:\\s]+(.+)$', '^(?:activate|run)\\s+(.+)\\s+scene$'), m.group(1).strip()
    if re.search("\\b(i'?m leaving|heading out|goodbye house|good night house)\\b", lower):
        leave_scene() = text.lower()
        if preset:
            return preset
        if None in lower or 'goodnight' in lower:
            return 'goodnight'
        return 'leaving'


def parse_control(message = None):
    parse_color_control = parse_color_control
    import jarvis.ha_light_control
    color = parse_color_control(message)
    if color:
        return color
    if not None:
        pass
    text = ''.strip()
    m = re.match('^(?:please\\s+)?(turn|switch)\\s+(on|off|toggle)\\s+(?:the\\s+)?(.+)$', text, re.I)
    if m:
        return {
            'action': m.group(2).lower(),
            'target': m.group(3).strip() }
    m = None.match('^(?:please\\s+)?(turn|switch)\\s+(?:the\\s+)?(.+?)\\s+(on|off)$', text, re.I)
    if m:
        return {
            'action': m.group(3).lower(),
            'target': m.group(2).strip() }


def is_ha_status_query(message = None):
    lower = _normalize_ha_text(message)
    if re.search("\\b(home assistant status|ha status|house status|home status|smart home status|home overview|home snapshot|what(?:'?s| is| are) on at (?:home|the house|my house|my home)|how(?:'?s| is) (?:the )?house|(?:anything|something) (?:on|going on|running) (?:at )?(?:home|the house|my house))\\b", lower):
        return True
    if re.search('\\bstatus (?:of )?(?:my |the )?home\\b', lower):
        return True
    if re.search("\\b(check|show|get|tell me|what(?:'?s| is| are)|which|status of|state of)\\b", lower) and re.search('\\b(home assistant|smart home|(?:my |the )?home|my house|the house|at home)\\b', lower):
        return True
    if re.search("\\b(check|show|get|tell me|what(?:'?s| is| are)|which|status of|state of)\\b", lower) and re.search('\\b(lights?|switches?|thermostat|doors?|garage|living room|bedroom|kitchen)\\b', lower):
        return True
    if re.search('\\b(which|what) lights? (?:are )?(?:on|off)\\b', lower):
        return True
    if re.search('\\b(lights?|switches?) (?:that are )?(?:on|off)\\b', lower):
        return True
    return False


def is_ha_state_query(message = None):
    lower = _normalize_ha_text(message)
    if re.search("\\b(what(?:'?s| is) the (?:temperature|temp|humidity)|is the .+ (?:on|off|open|closed)|state of (?:the )?.+)\\b", lower):
        re.search("\\b(what(?:'?s| is) the (?:temperature|temp|humidity)|is the .+ (?:on|off|open|closed)|state of (?:the )?.+)\\b", lower)
    return bool(re.search('\\b(light|switch|sensor|thermostat|door|garage|room|living|bedroom|office)\\b', lower))


def quick_route_home_assistant(message = None):
    '''Return HA action dict for smart-home phrasing (works even before token is saved).'''
    scene = parse_scene(message)
    if scene:
        return {
            'action': 'ha_scene',
            'params': {
                'scene': scene } }
    control = None(message)
    if control:
        return {
            'action': 'ha_control',
            'params': control }
    if None(message):
        return {
            'action': 'ha_status',
            'params': { } }
    if None(message):
        return {
            'action': 'ha_query',
            'params': {
                'query': message } }


def integration_issues():
    '''HA config entries that are not loaded (auth expired, setup errors, etc.).'''
    
    try:
        entries = _request('GET', '/api/config/config_entries/entry')
        if not isinstance(entries, list):
            return []
        issues = None
        for entry in entries:
            if not entry.get('state'):
                entry.get('state')
            state = ''.strip()
            if state in ('loaded', 'not_loaded', ''):
                continue
            if not entry.get('domain'):
                entry.get('domain')
            if not entry.get('title'):
                entry.get('title')
            if not entry.get('reason'):
                entry.get('reason')
            issues.append({
                'domain': '',
                'title': '',
                'state': state,
                'reason': '' })
        return issues
    except Exception:
        exc = None
        log.debug('HA integration_issues: %s', exc)
        del exc
        return None
        None = 
        del exc



def entity_health_summary():
    """Counts for lights/switches — surfaces stale 'restored' entities after integration outages."""
    pass
# WARNING: Decompyle incomplete


def status_payload():
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    load_jarvis_env()
    conn = check_connection()
    secret = automation_secret()
    webhook_url = ''
    if secret:
        
        try:
            client_base_url = client_base_url
            import jarvis.lan
            webhook_url = f'''{client_base_url()}/api/automation/inbound?secret={secret}'''
            health = entity_health_summary() if conn.get('ok') else { }
            issues = integration_issues() if conn.get('ok') else []
            if ha_url():
                ha_url()
            return {
                'enabled': ha_feature_on(),
                'feature_on': ha_feature_on(),
                'configured': bool(ha_token()),
                'connected': bool(conn.get('ok')),
                'token_set': bool(ha_token()),
                'url': ha_url(),
                'leave_scene': leave_scene(),
                'automation_secret_set': bool(secret),
                'automation_webhook': '/api/automation/inbound',
                'automation_webhook_url': webhook_url,
                'connection': conn,
                'entity_health': health,
                'integration_issues': issues }
        except Exception:
            webhook_url = f'''/api/automation/inbound?secret={secret}'''
            continue



def save_config(*, url, token, leave_scene, enabled, ensure_automation_secret):
    load_jarvis_env = load_jarvis_env
    upsert_env_vars = upsert_env_vars
    import jarvis.env_loader
    generate_api_key = generate_api_key
    import jarvis.lan
    updates = { }
# WARNING: Decompyle incomplete


def test_connection(url = None, token = None):
    '''Probe HA without persisting config.'''
    if not url:
        url
    probe_url = ha_url().strip().rstrip('/')
    if not token:
        token
    probe_token = normalize_ha_token(ha_token())
    if not probe_url:
        return {
            'ok': False,
            'message': 'Home Assistant URL is required.' }
    if not None:
        return {
            'ok': False,
            'message': 'Paste your long-lived access token first.' }
    old_token = os.environ.get('JARVIS_HA_TOKEN')
    old_url = None.environ.get('JARVIS_HA_URL')
# WARNING: Decompyle incomplete


def briefing_home_lines(*, limit):
    if not ha_enabled():
        return []
    (ok, text) = None(limit = limit)
    if not ok or text.strip():
        return []
    return [
        None]


def parse_ha_token_message(message = None):
    if not message:
        message
    text = ''.strip()
    for pat in ('^(?:set\\s+)?(?:home assistant|ha)\\s+token[:\\s]+(.+)$', '^paste(?:\\s+(?:ha|home assistant))?\\s+token[:\\s]+(.+)$'):
        m = re.match(pat, text, re.I | re.S)
        if not m:
            continue
        token = m.group(1).strip()
        if not token:
            token
        
        return ('^(?:set\\s+)?(?:home assistant|ha)\\s+token[:\\s]+(.+)$', '^paste(?:\\s+(?:ha|home assistant))?\\s+token[:\\s]+(.+)$'), None
    if re.fullmatch('eyJ[A-Za-z0-9._-]+', text) and len(text) >= 30:
        return text


def verify_automation_secret(header_value = None, query_value = None):
    secret = automation_secret()
    if not secret:
        return False
    if not header_value:
        header_value
        if not query_value:
            query_value
    supplied = ''.strip()
    return supplied == secret

