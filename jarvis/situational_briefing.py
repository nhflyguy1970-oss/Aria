# Source Generated with Decompyle++
# File: situational_briefing.cpython-312.pyc (Python 3.12)

'''Cross-domain situational briefing — world state + weather + headlines.'''
from __future__ import annotations
import os
from datetime import date, datetime
from typing import Any

def situational_enabled():
    return os.getenv('JARVIS_SITUATIONAL_BRIEFING', '1') != '0'


def build_situational_briefing(*, journal, memory_store, assistant, include_news):
    '''Combine world state, weather, and optional headlines.'''
    personalized_greeting = personalized_greeting
    profile_first_name = profile_first_name
    time_greeting = time_greeting
    import jarvis.morning_briefing
    _today = _today
    import jarvis.modules.journal
    refresh_world_state_cache = refresh_world_state_cache
    world_state_summary = world_state_summary
    import jarvis.world_state
    ref = datetime.now()
    d_iso = _today()
    greeting = personalized_greeting(when = ref, memory_store = memory_store, assistant = assistant)
    state = refresh_world_state_cache(memory_store = memory_store)
    world_md = world_state_summary(state)
    format_weather_line = format_weather_line
    weather_for_day = weather_for_day
    import jarvis.journal_weather
    page = journal.daily_get(d_iso)
    if not page.get('weather'):
        page.get('weather')
        if not weather_for_day(d_iso):
            weather_for_day(d_iso)
    weather = { }
    weather_line = format_weather_line(weather) if weather else ''
    if not greeting.get('greeting'):
        greeting.get('greeting')
    lines = [
        time_greeting(when = ref) + '.',
        '']
    lines.append('**Situational status**')
    lines.append(world_md)
    if weather_line:
        lines.extend([
            '',
            f'''**Weather:** {weather_line}'''])
    news = {
        'enabled': False,
        'national': [],
        'local': [] }
    if include_news and os.getenv('JARVIS_BRIEFING_NEWS', '1') != '0':
        fetch_briefing_news = fetch_briefing_news
        format_news_markdown = format_news_markdown
        import jarvis.briefing_news
        news = fetch_briefing_news(memory_store = memory_store, weather = weather, force_refresh = False)
        block = format_news_markdown(news)
        if block:
            None(lines.extend)
    open_tasks = journal.open_tasks(limit = 5)
    if open_tasks:
        lines.extend([
            '',
            f'''**Open tasks ({journal.stats().get('open_tasks', len(open_tasks))})**'''])
        for t in open_tasks[:5]:
            lines.append(f'''- {t.get('content', '')[:100]}''')
    assistant_name = assistant_name
    import jarvis.branding
    lines.extend([
        '',
        f'''_Say **situational briefing** or **what\'s my status** anytime · {assistant_name()}_'''])
    return {
        'day': d_iso,
        'greeting': greeting,
        'world_state': state,
        'weather': weather,
        'weather_line': weather_line,
        'news': news,
        'markdown': '\n'.join(lines),
        'name': profile_first_name(memory_store) }

