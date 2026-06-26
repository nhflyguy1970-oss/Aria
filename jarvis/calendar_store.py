# Source Generated with Decompyle++
# File: calendar_store.cpython-312.pyc (Python 3.12)

'''Local calendar data: weekly work schedule blocks.'''
from __future__ import annotations
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
log = logging.getLogger('jarvis.calendar')
SCHEDULE_FILE = DATA_DIR / 'calendar_work_schedule.json'
WEEKDAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
ISO_WEEKDAY_TO_KEY = {
    0: 'mon',
    1: 'tue',
    2: 'wed',
    3: 'thu',
    4: 'fri',
    5: 'sat',
    6: 'sun' }

def _default_schedule():
    return {
        'enabled': True,
        'days': {
            'mon': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }],
            'tue': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }],
            'wed': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }],
            'thu': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }],
            'fri': [
                {
                    'start': '09:00',
                    'end': '17:00',
                    'label': 'Work' }],
            'sat': [],
            'sun': [] } }


def load_work_schedule():
    if not SCHEDULE_FILE.is_file():
        return _default_schedule()
    
    try:
        data = json.loads(SCHEDULE_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict):
            data.setdefault('enabled', True)
            data.setdefault('days', _default_schedule()['days'])
            for key in WEEKDAYS:
                data['days'].setdefault(key, [])
            return data
        return _default_schedule()
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt work schedule: %s', exc)
        exc = None
        del exc
        return _default_schedule()
        exc = None
        del exc



def save_work_schedule(data = None):
    SCHEDULE_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(SCHEDULE_FILE)
    clean = {
        'enabled': bool(data.get('enabled', True)),
        'days': { } }
    for key in WEEKDAYS:
        blocks = []
        if not data.get('days', { }).get(key):
            data.get('days', { }).get(key)
        for block in []:
            if not isinstance(block, dict):
                continue
            if not block.get('start'):
                block.get('start')
            start = str('').strip()[:5]
            if not block.get('end'):
                block.get('end')
            end = str('').strip()[:5]
            if not block.get('label'):
                block.get('label')
            if not str('Work').strip()[:80]:
                str('Work').strip()[:80]
            label = 'Work'
            if not start:
                continue
            if not end:
                continue
            blocks.append({
                'start': start,
                'end': end,
                'label': label })
        clean['days'][key] = blocks
    SCHEDULE_FILE.write_text(json.dumps(clean, indent = 2), encoding = 'utf-8')
    return clean


def work_blocks_for_day(day = None):
    if isinstance(day, str):
        day = date.fromisoformat(day)
    sched = load_work_schedule()
    if not sched.get('enabled'):
        return []
    key = None.get(day.weekday(), 'mon')
# WARNING: Decompyle incomplete

