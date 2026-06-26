# Source Generated with Decompyle++
# File: calendar_ics.cpython-312.pyc (Python 3.12)

'''Optional external calendar (ICS URL) for morning briefing.'''
from __future__ import annotations
import logging
import os
import re
import urllib.request as urllib
from datetime import date, datetime
from typing import Any
log = logging.getLogger('jarvis')

def ics_url():
    if not os.getenv('JARVIS_ICS_URL'):
        os.getenv('JARVIS_ICS_URL')
        if not os.getenv('JARVIS_CALENDAR_ICS_URL'):
            os.getenv('JARVIS_CALENDAR_ICS_URL')
    return ''.strip()


def _parse_dt(value = None, *, day):
    if not value:
        value
    raw = ''.strip()
    if not raw:
        return None
    if raw.endswith('Z'):
        raw = raw[:-1] + '+0000'
    for fmt in ('%Y%m%dT%H%M%S%z', '%Y%m%dT%H%M%S', '%Y%m%d'):
        dt = datetime.strptime(raw[:15] if 'T' in raw else raw[:8], fmt.split('T')[0] if 'T' not in raw else fmt)
        if dt.tzinfo:
            dt = dt.replace(tzinfo = None)
        if 'T' not in value and len(value.strip()) == 8:
            
            return ('%Y%m%dT%H%M%S%z', '%Y%m%dT%H%M%S', '%Y%m%d'), dt.replace(hour = 0, minute = 0)
        
        return None, ('%Y%m%dT%H%M%S%z', '%Y%m%dT%H%M%S', '%Y%m%d')
    if len(raw) >= 8 and raw[:8].isdigit():
        
        try:
            if d.date() != day:
                return None
                
                try:
                    if 'T' in raw and len(raw) >= 13:
                        int(raw[9:11]) = datetime.strptime(raw[:8], '%Y%m%d')
                        mm = int(raw[11:13])
                        return d.replace(hour = hh, minute = mm)
                    return datetime.strptime(raw[:8], '%Y%m%d')
                    return None
                    except ValueError:
                        continue
                except ValueError:
                    return None




def _parse_ics_events(text = None, day = None):
    events = []
    blocks = re.split('BEGIN:VEVENT', text, flags = re.I)
    for block in blocks[1:]:
        chunk = block.split('END:VEVENT', 1)[0]
        summary = ''
        dtstart = ''
        for line in chunk.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.upper().startswith('SUMMARY'):
                summary = line.split(':', 1)[-1].strip()
                continue
            if not line.upper().startswith('DTSTART'):
                continue
            dtstart = line.split(':', 1)[-1].strip()
        if not summary:
            continue
        start = _parse_dt(dtstart, day = day)
        if start or start.date() != day:
            continue
        time_str = start.strftime('%H:%M') if start.hour or start.minute else ''
        events.append({
            'summary': summary,
            'time': time_str,
            'source': 'ics' })
    events.sort(key = (lambda e: if not e.get('time'):
e.get('time')'99:99'))
    return events


def _parse_ics_event_block(chunk = None):
    summary = ''
    dtstart = ''
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith('SUMMARY'):
            summary = line.split(':', 1)[-1].strip()
            continue
        if not line.upper().startswith('DTSTART'):
            continue
        dtstart = line.split(':', 1)[-1].strip()
    if not summary or dtstart:
        return (None, '', '')
    raw = dtstart.strip()
    
    try:
        if len(raw) >= 8 and raw[:8].isdigit():
            d = date(int(raw[0:4]), int(raw[4:6]), int(raw[6:8]))
        else:
            return (None, '', '')
        start = _parse_dt(dtstart, day = d)
        if start:
            pass
        time_str = start.strftime('%H:%M') if start.hour or start.minute else ''
        return (d, summary, time_str)
    except ValueError:
        return (None, '', '')



def fetch_events_for_month(month = None):
    '''ICS events keyed by YYYY-MM-DD for a calendar month.'''
    url = ics_url()
    if not url:
        return { }
# WARNING: Decompyle incomplete


def fetch_events_for_day(day = None):
    url = ics_url()
    if not url:
        return []
    if not None:
        pass
    day = date.today()
# WARNING: Decompyle incomplete

