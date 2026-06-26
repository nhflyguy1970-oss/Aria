# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Git fast-path routing rules.'''
from __future__ import annotations
import re
from jarvis.router_table import RouteRule

def git_routes():
    return [
        RouteRule('git_status', 22, 'git status', (lambda m, lower, _s: bool(re.search('\\b(git status|what changed in git)\\b', lower)))),
        RouteRule('git_diff', 23, 'git diff', (lambda m, lower, _s: bool(re.search('\\b(git diff|show diff)\\b', lower)))),
        RouteRule('git_summarize', 24, 'summarize diff', (lambda m, lower, _s: bool(re.search('\\b(summarize (the )?diff|what did i change)\\b', lower)))),
        RouteRule('git_commit', 25, 'git commit', (lambda m, lower, _s: bool(re.search('\\bcommit(?:\\s+with\\s+message)?[:\\s]+', m, re.I))), params = (lambda m: mobj = re.search('\\bcommit(?:\\s+with\\s+message)?[:\\s]+(.+)', m, re.I)if re.search('\\bcommit(?:\\s+with\\s+message)?[:\\s]+(.+)', m, re.I):
{
'message': mobj.group(1).strip() })),
        RouteRule('git_branch', 26, 'git branch', (lambda m, lower, _s: bool(re.search('\\bcreate\\s+(?:git\\s+)?branch\\s+[`\'\\"]?[\\w./-]+', m, re.I))), params = (lambda m: mobj = re.search('\\bcreate\\s+(?:git\\s+)?branch\\s+[`\'\\"]?([\\w./-]+)', m, re.I)if re.search('\\bcreate\\s+(?:git\\s+)?branch\\s+[`\'\\"]?([\\w./-]+)', m, re.I):
{
'name': mobj.group(1) })),
        RouteRule('git_pr', 27, 'pull request', (lambda m, lower, _s: bool(re.search('\\bcreate (?:a )?pull request\\b', lower))), params = (lambda m: if not re.sub('^.*create (?:a )?pull request[:\\s]+', '', m, flags = re.I).strip():
re.sub('^.*create (?:a )?pull request[:\\s]+', '', m, flags = re.I).strip(){
'title': 'Jarvis changes' }))]

