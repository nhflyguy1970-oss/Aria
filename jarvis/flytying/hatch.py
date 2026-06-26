# Source Generated with Decompyle++
# File: hatch.cpython-312.pyc (Python 3.12)

'''Seasonal hatch calendar for fly-tying suggestions.'''
from __future__ import annotations
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
_DATA = Path(__file__).resolve().parent / 'data' / 'hatch_northeast.json'
_calendar = (lambda : if not _DATA.is_file():
{ }try:
data = json.loads(_DATA.read_text(encoding = 'utf-8'))if isinstance(data, dict):
dataNoneexcept (OSError, json.JSONDecodeError):
)()

def hatch_context(*, month):
    cal = _calendar()
    if not month:
        month
    m = datetime.now().month
    if not cal.get('months'):
        cal.get('months')
    if not { }.get(str(m)):
        { }.get(str(m))
    month_data = { }
    if not cal.get('region'):
        cal.get('region')
    if not month_data.get('hatches'):
        month_data.get('hatches')
    if not month_data.get('suggest_types'):
        month_data.get('suggest_types')
    if not month_data.get('notes'):
        month_data.get('notes')
    return {
        'region': 'Northeast US',
        'month': m,
        'hatches': [],
        'suggest_types': [],
        'notes': '' }


def hatch_context_text(*, month):
    ctx = hatch_context(month = month)
    if not ctx.get('hatches'):
        ctx.get('hatches')
    hatches = ', '.join([])
    if not ctx.get('suggest_types'):
        ctx.get('suggest_types')
    types = ', '.join([])
    lines = [
        f'''Seasonal context ({ctx.get('region')}, month {ctx.get('month')}):''']
    if hatches:
        lines.append(f'''Typical hatches: {hatches}.''')
    if types:
        lines.append(f'''Suggested fly types: {types}.''')
    if ctx.get('notes'):
        lines.append(str(ctx['notes']))
    return ' '.join(lines)


def suggest_patterns_for_season(*, month, limit):
    ctx = hatch_context(month = month)
    terms = []
    if not ctx.get('hatches'):
        ctx.get('hatches')
    for h in []:
        terms.append(str(h))
    if not ctx.get('suggest_types'):
        ctx.get('suggest_types')
    for t in []:
        terms.append(str(t))
    return terms[:limit]

