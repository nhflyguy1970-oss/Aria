# Source Generated with Decompyle++
# File: videos_store.cpython-312.pyc (Python 3.12)

'''Persist custom fly-tying videos and article embed cache.'''
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
from jarvis.config import DATA_DIR
CUSTOM_VIDEOS_FILE = DATA_DIR / 'flytying_custom_videos.json'
VIDEO_CACHE_FILE = DATA_DIR / 'flytying_video_cache.json'

def _read_json(path, default):
    if not path.is_file():
        return default
    
    try:
        data = json.loads(path.read_text(encoding = 'utf-8'))
        if isinstance(data, (dict, list)):
            return data
        return None
    except (OSError, json.JSONDecodeError):
        return 



def _write_json(path = None, data = None):
    path.parent.mkdir(parents = True, exist_ok = True)
    path.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def list_custom_videos():
    rows = _read_json(CUSTOM_VIDEOS_FILE, [])
    if isinstance(rows, list):
        return rows


def add_custom_video(url = None, *, title):
    pass
# WARNING: Decompyle incomplete


def remove_custom_video(key = None):
    if not key:
        key
    key = ''.strip()
    rows = list_custom_videos()
# WARNING: Decompyle incomplete


def get_cached_videos(page_url = None):
    cache = _read_json(VIDEO_CACHE_FILE, { })
    if not isinstance(cache, dict):
        return []
    if not None.get(page_url):
        None.get(page_url)
    row = { }
    if not row.get('videos'):
        row.get('videos')
    videos = []
    if isinstance(videos, list):
        return videos


def set_cached_videos(page_url = None, videos = None):
    pass
# WARNING: Decompyle incomplete

