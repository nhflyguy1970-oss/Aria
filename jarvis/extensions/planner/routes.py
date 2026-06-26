# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Fast-path routes for planner and system info.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def planner_routes():
    return [
        RouteRule('system_info', 9, 'system status', (lambda m, lower, _s: bool(re.search("\\b(system status|what'?s my status|what do i have|what's going on|status snapshot)\\b", lower)))),
        RouteRule('planner_set_timer', 15, 'set timer', (lambda m, lower, _s: bool(re.search('\\b(set|start)\\s+(a\\s+)?timer\\b', lower))), (lambda m: {
'duration': re.sub('.*timer\\s+(?:for\\s+)?', '', m, flags = re.I).strip() })),
        RouteRule('planner_set_alarm', 15, 'set alarm', (lambda m, lower, _s: bool(re.search('\\b(set|create)\\s+(an\\s+)?alarm\\b', lower))), (lambda m: {
'time': re.sub('.*alarm\\s+(?:for\\s+)?(?:at\\s+)?', '', m, flags = re.I).strip() })),
        RouteRule('planner_add_task', 16, 'add task', (lambda m, lower, _s: if not re.search('\\b(add|create)\\s+.+?\\s+to\\s+(my\\s+)?(to-?do|task) list\\b', lower):
re.search('\\b(add|create)\\s+.+?\\s+to\\s+(my\\s+)?(to-?do|task) list\\b', lower)bool(re.search('\\badd\\s+(buy|task)\\b', lower))), (lambda m: {
'text': re.sub('.*add\\s+', '', m, flags = re.I).strip() })),
        RouteRule('planner_today', 17, 'schedule today', (lambda m, lower, _s: bool(re.search("\\b(what'?s on my schedule|my schedule today|planner today)\\b", lower)))),
        RouteRule('curated_briefing', 18, 'curated news', (lambda m, lower, _s: bool(re.search('\\b(curated (news|briefing)|tech headlines)\\b', lower)))),
        RouteRule('audio_stop', 6, 'stop audio', (lambda m, lower, _s: bool(re.search('\\b(stop (speaking|audio|playback)|pause audio)\\b', lower)))),
        RouteRule('audio_pause', 6, 'pause audio', (lambda m, lower, _s: bool(re.search('\\b(pause (speaking|audio)|resume (speaking|audio))\\b', lower))))]

